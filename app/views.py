from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError, transaction
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
import hmac
import hashlib
import logging
import json
import re

from .models import Retailer, PaymentRequest, PANApplication, WalletTransaction

logger = logging.getLogger(__name__)

# ₹15 charge per PAN application
PAN_APPLICATION_CHARGE = Decimal('15.00')


# ---------------------------------------------------------------------------
# Session helper
# ---------------------------------------------------------------------------

def _get_retailer_from_session(request):
    retailer_id = request.session.get('retailer_id')
    if not retailer_id:
        logger.debug(f"No retailer_id in session. Session keys: {list(request.session.keys())}")
        return None
    try:
        return Retailer.objects.get(retailer_id=retailer_id)
    except Retailer.DoesNotExist:
        logger.warning(f"Retailer with id {retailer_id} not found in database")
        return None


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

def retailer_login(request):
    context = {}
    if request.method == 'POST':
        user_id  = request.POST.get('user_id', '').strip()
        password = request.POST.get('password', '')

        if not user_id or not password:
            context['error'] = 'User ID aur password dono bharna zaroori hain.'
            return render(request, 'login.html', context)

        try:
            retailer = Retailer.objects.get(user_id=user_id)
        except Retailer.DoesNotExist:
            context['error'] = 'Invalid User ID ya password.'
            return render(request, 'login.html', context)

        if not check_password(password, retailer.password):
            context['error'] = 'Invalid User ID ya password.'
            return render(request, 'login.html', context)

        if not retailer.is_active:
            context['error'] = 'Aapka account abhi active nahi hai. Kripya administrator se sampark karein.'
            return render(request, 'login.html', context)

        request.session['retailer_id'] = str(retailer.retailer_id)
        request.session.modified = True
        request.session.save()

        logger.info(f"User {user_id} logged in successfully. Session ID: {request.session.session_key}")
        return redirect('retailer_dashboard')

    return render(request, 'login.html', context)


def retailer_signup(request):
    context = {}
    if request.method == 'POST':
        full_name  = request.POST.get('full_name', '').strip()
        mobile     = request.POST.get('mobile', '').strip()
        user_id    = request.POST.get('user_id', '').strip()
        password   = request.POST.get('password', '')
        shop_name  = request.POST.get('shop_name', '').strip()
        utr_number = request.POST.get('utr_number', '').strip()
        screenshot = request.FILES.get('screenshot')

        if not full_name or not mobile or not user_id or not password or not utr_number:
            context['error'] = 'Sabhi required fields bharna zaroori hai.'
            return render(request, 'signup.html', context)

        if len(password) < 6:
            context['error'] = 'Password kam se kam 6 characters ka hona chahiye.'
            return render(request, 'signup.html', context)

        try:
            retailer = Retailer(
                full_name=full_name,
                mobile=mobile,
                user_id=user_id,
                shop_name=shop_name,
            )
            retailer.set_password(password)
            retailer.save()

            PaymentRequest.objects.create(
                retailer=retailer,
                utr_number=utr_number,
                screenshot=screenshot,
            )

            context['success'] = 'Registration successful hai. Ab aap login kar sakte hain.'
            return render(request, 'signup.html', context)

        except IntegrityError:
            context['error'] = 'User ID ya mobile number pehle se exist karta hai. Kripya doosra choose karein.'
            return render(request, 'signup.html', context)

    return render(request, 'signup.html', context)


def retailer_logout(request):
    request.session.pop('retailer_id', None)
    request.session.flush()
    return redirect('retailer_login')


# ---------------------------------------------------------------------------
# Dashboard — sirf us retailer ki applications
# ---------------------------------------------------------------------------

def retailer_dashboard(request):
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return redirect('retailer_login')

    # ✅ Sirf is retailer ki applications
    total_apps  = PANApplication.objects.filter(retailer=retailer).count()
    recent_apps = PANApplication.objects.filter(retailer=retailer).order_by('-created_at')[:5]

    return render(request, 'dashboard.html', {
        'retailer':    retailer,
        'total_apps':  total_apps,
        'recent_apps': recent_apps,
    })


# ---------------------------------------------------------------------------
# PAN application pages
# ---------------------------------------------------------------------------

def form(request):
    # ✅ Login check — bina login ke form nahi dikhega
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return redirect('retailer_login')
    return render(request, 'form.html', {'retailer': retailer})


def applied_list(request):
    # ✅ Sirf us retailer ki list
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return redirect('retailer_login')

    applications = PANApplication.objects.filter(retailer=retailer).order_by('-created_at')
    return render(request, 'applied_list.html', {
        'applications': applications,
        'retailer':     retailer,
    })


def detail(request, order_id):
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return redirect('retailer_login')

    try:
        # ✅ Ownership check — dusre retailer ka order nahi dekh sakta
        app_obj = PANApplication.objects.get(order_id=order_id, retailer=retailer)
    except PANApplication.DoesNotExist:
        return render(request, 'detail.html', {'error': 'Application not found.'})

    return render(request, 'detail.html', {'app': app_obj})


def pan_print(request, order_id):
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return redirect('retailer_login')

    try:
        # ✅ Ownership check
        app_obj = PANApplication.objects.get(order_id=order_id, retailer=retailer)
    except PANApplication.DoesNotExist:
        return render(request, 'pan_print.html', {'error': 'PAN application not found.'})

    return render(request, 'pan_print.html', {'app': app_obj})


@csrf_exempt
def verify_pan(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid payload'}, status=400)

    pan = payload.get('pan', '').strip().upper()
    if not pan or len(pan) != 10:
        return JsonResponse({'success': False, 'message': 'Invalid PAN number'}, status=400)

    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
        return JsonResponse({'success': False, 'message': 'PAN format invalid'}, status=400)

    surepass_token = getattr(settings, 'SUREPASS_TOKEN', '').strip()
    if not surepass_token:
        return JsonResponse({'success': False, 'message': 'SurePass token configure nahi hai.'}, status=500)

    last_error = None

    try:
        response = requests.post(
            'https://kyc-api.surepass.app/api/v1/pan/pan-comprehensive',
            headers={
                'Authorization': f'Bearer {surepass_token}',
                'Content-Type': 'application/json',
            },
            json={'id_number': pan},
            timeout=20,
        )
        logger.info(f'SurePass raw response: status={response.status_code}, body={response.text[:500]}')

        if response.status_code >= 500:
            last_error = f'SurePass server error: {response.status_code}'
        else:
            result = response.json()
            if result.get('success'):
                data = result.get('data', {})
                gender_raw = str(data.get('gender') or '').upper()
                gender_val = 'Male' if gender_raw in ['M', 'MALE'] else ('Female' if gender_raw in ['F', 'FEMALE'] else gender_raw)
                
                # Format DOB if needed
                dob_val = data.get('dob') or ''

                return JsonResponse({
                    'success': True,
                    'data': {
                        'full_name': data.get('full_name') or '',
                        'first_name': data.get('first_name') or '',
                        'last_name': data.get('last_name') or '',
                        'father_name': data.get('father_name') or '',
                        'dob': dob_val,
                        'gender': gender_val,
                        'category': data.get('category') or '',
                        'address': data.get('full_address') or '',
                        'aadhaar_linked': data.get('aadhaar_linked', False),
                    }
                })
            last_error = result.get('message', 'PAN details nahi mile.')

    except requests.Timeout:
        last_error = 'API timeout. Dobara try karo.'
    except Exception as exc:
        logger.error('SurePass PAN verification failed: %s', exc)
        last_error = 'SurePass API fail ho gayi.'

    return JsonResponse({'success': False, 'message': last_error or 'PAN details nahi mile.'}, status=400)
@csrf_exempt
def submit_application(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    # ✅ Session se retailer lo — login zaroori hai
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return JsonResponse({
            'status':  'error',
            'message': 'Session expire ho gayi. Kripya dobara login karein.',
            'redirect': '/login/'
        }, status=401)

    # ✅ Wallet balance check — ₹15 chahiye
    current_balance = retailer.wallet_balance or Decimal('0')
    if current_balance < PAN_APPLICATION_CHARGE:
        shortage = PAN_APPLICATION_CHARGE - current_balance
        return JsonResponse({
            'status':  'insufficient_balance',
            'message': f'Wallet balance kam hai. ₹{PAN_APPLICATION_CHARGE} chahiye, aapke paas sirf ₹{current_balance} hain. Kripya ₹{shortage} ya zyada add karein.',
            'balance': str(current_balance),
            'required': str(PAN_APPLICATION_CHARGE),
        }, status=402)

    pan_number  = request.POST.get('pan_number', '').strip().upper()
    full_name   = request.POST.get('full_name', '').strip()
    father_name = request.POST.get('father_name', '').strip()
    dob         = request.POST.get('dob', '').strip()
    gender      = request.POST.get('gender', '').strip()
    signature   = request.FILES.get('signature')
    photo       = request.FILES.get('photo')

    if not pan_number or not full_name or not father_name or not dob or not gender or not signature or not photo:
        return JsonResponse({'status': 'error', 'message': 'Sabhi fields bharna zaroori hain.'}, status=400)

    try:
        # ✅ Atomic: application create + wallet deduct ek saath
        with transaction.atomic():
            app_obj = PANApplication.objects.create(
                retailer=retailer,
                pan_number=pan_number,
                full_name=full_name,
                father_name=father_name,
                dob=dob,
                gender=gender,
                signature=signature,
                photo=photo,
                amount=PAN_APPLICATION_CHARGE,
            )

            # Wallet se ₹15 deduct
            retailer.wallet_balance = current_balance - PAN_APPLICATION_CHARGE
            retailer.save(update_fields=['wallet_balance'])

            # Transaction record
            WalletTransaction.objects.create(
                retailer=retailer,
                amount=PAN_APPLICATION_CHARGE,
                tx_type='debit',
                status='completed',
                payment_provider='internal',
                note=f'PAN application charge — Order ID: {app_obj.order_id}',
            )

    except Exception as exc:
        logger.error('submit_application: failed: %s', exc)
        return JsonResponse({'status': 'error', 'message': 'Application submit nahi ho payi. Dobara try karein.'}, status=500)

    return JsonResponse({
        'status':          'success',
        'order_id':        app_obj.order_id,
        'wallet_balance':  str(retailer.wallet_balance),
        'amount_deducted': str(PAN_APPLICATION_CHARGE),
    })


# ---------------------------------------------------------------------------
# Wallet page
# ---------------------------------------------------------------------------

def retailer_wallet(request):
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return redirect('retailer_login')

    transactions = WalletTransaction.objects.filter(retailer=retailer).order_by('-created_at')[:50]
    context = {'retailer': retailer, 'transactions': transactions}

    if request.method == 'POST':
        amount_str = request.POST.get('amount', '0').strip()
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            context['error'] = 'Kripya valid rakam daalein.'
            return render(request, 'wallet.html', context)

        if amount <= 0:
            context['error'] = 'Rakam zero se zyada honi chahiye.'
            return render(request, 'wallet.html', context)

        retailer.wallet_balance = (retailer.wallet_balance or Decimal('0')) + amount
        retailer.save()
        WalletTransaction.objects.create(
            retailer=retailer,
            amount=amount,
            tx_type='credit',
            status='completed',
            payment_provider='manual',
            note='Direct credit via demo form',
        )
        context['success'] = f'Rs.{amount} added to wallet.'

    return render(request, 'wallet.html', context)


# ---------------------------------------------------------------------------
# Razorpay — create order
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def create_razorpay_order(request):
    retailer = _get_retailer_from_session(request)
    if not retailer:
        logger.warning('create_razorpay_order: No retailer in session - Unauthorized')
        return JsonResponse({'error': 'not_authenticated', 'detail': 'Please login again'}, status=401)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError as exc:
        logger.error('create_razorpay_order: bad JSON: %s', exc)
        return JsonResponse({'error': 'invalid_payload', 'detail': str(exc)}, status=400)

    amount_str = data.get('amount')
    if not amount_str:
        return JsonResponse({'error': 'amount_required'}, status=400)

    try:
        amount = Decimal(str(amount_str))
    except (InvalidOperation, TypeError) as exc:
        return JsonResponse({'error': 'invalid_amount', 'detail': str(exc)}, status=400)

    if amount <= 0:
        return JsonResponse({'error': 'invalid_amount', 'detail': 'Amount must be positive'}, status=400)

    amount_paise = int((amount * 100).quantize(Decimal('1')))

    key_id     = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()

    if not key_id or not key_secret:
        logger.error('Razorpay credentials missing')
        return JsonResponse({'error': 'razorpay_not_configured'}, status=500)

    receipt = f"wallet_{retailer.retailer_id}"[:40]

    order_payload = {
        'amount':          amount_paise,
        'currency':        'INR',
        'receipt':         receipt,
        'payment_capture': 1,
        'notes': {
            'retailer_id':   str(retailer.retailer_id),
            'retailer_name': retailer.full_name[:50],
            'user_id':       retailer.user_id[:30],
        }
    }

    try:
        resp = requests.post(
            'https://api.razorpay.com/v1/orders',
            auth=(key_id, key_secret),
            json=order_payload,
            timeout=15,
        )

        if resp.status_code != 200:
            error_data = resp.json() if resp.text else {}
            error_msg  = error_data.get('error', {}).get('description', resp.text)
            logger.error(f'Razorpay error: {error_msg}')
            return JsonResponse({'error': 'razorpay_error', 'detail': error_msg}, status=resp.status_code)

        order = resp.json()
        return JsonResponse({
            'order_id': order.get('id'),
            'key':      key_id,
            'amount':   amount_paise,
        })

    except requests.exceptions.RequestException as exc:
        logger.error(f'Razorpay request failed: {exc}')
        return JsonResponse({'error': 'razorpay_request_failed', 'detail': str(exc)}, status=502)


# ---------------------------------------------------------------------------
# Razorpay — verify payment
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def verify_razorpay_payment(request):
    retailer = _get_retailer_from_session(request)
    if not retailer:
        return JsonResponse({'error': 'not_authenticated', 'detail': 'Please login again'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return JsonResponse({'error': 'invalid_payload', 'detail': str(exc)}, status=400)

    razorpay_payment_id = payload.get('razorpay_payment_id')
    razorpay_order_id   = payload.get('razorpay_order_id')
    razorpay_signature  = payload.get('razorpay_signature')

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        return JsonResponse({'error': 'missing_fields'}, status=400)

    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    if not key_secret:
        return JsonResponse({'error': 'razorpay_not_configured'}, status=500)

    msg           = f'{razorpay_order_id}|{razorpay_payment_id}'.encode('utf-8')
    generated_sig = hmac.new(
        key_secret.encode('utf-8'),
        msg,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(generated_sig, razorpay_signature):
        logger.warning(f'Signature mismatch for order {razorpay_order_id}')
        return JsonResponse({'error': 'invalid_signature'}, status=400)

    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    try:
        resp = requests.get(
            f'https://api.razorpay.com/v1/orders/{razorpay_order_id}',
            auth=(key_id, key_secret),
            timeout=15,
        )
        resp.raise_for_status()
        order = resp.json()
    except Exception as exc:
        logger.error(f'Order fetch failed: {exc}')
        return JsonResponse({'error': 'razorpay_order_fetch_failed', 'detail': str(exc)}, status=502)

    amount_paise = int(order.get('amount', 0))
    amount       = Decimal(amount_paise) / Decimal(100)

    txn = WalletTransaction.objects.filter(
        provider_order_id=razorpay_order_id,
        retailer=retailer,
    ).first()

    if not txn:
        txn = WalletTransaction.objects.create(
            retailer=retailer,
            amount=amount,
            tx_type='credit',
            status='pending',
            payment_provider='razorpay',
            provider_order_id=razorpay_order_id,
        )

    if txn.status != 'completed':
        txn.provider_payment_id = razorpay_payment_id
        txn.status              = 'completed'
        txn.save()

        retailer.wallet_balance = (retailer.wallet_balance or Decimal('0')) + amount
        retailer.save()

    return JsonResponse({'status': 'success', 'added': str(amount)})

import json
import requests

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST


# -----------------------------
# Vehicle RC Page
# -----------------------------
def vehicle_rc_page(request):
    retailer = _get_retailer_from_session(request)

    if retailer is None:
        return redirect('retailer_login')

    return render(request, 'vehicle_rc.html', {
        'retailer': retailer
    })


# -----------------------------
# Vehicle RC API
# -----------------------------
@require_POST
def vehicle_rc_api(request):
    try:
        retailer = _get_retailer_from_session(request)

        if retailer is None:
            return JsonResponse({
                'success': False,
                'error': 'Please login first.'
            }, status=401)

        body = json.loads(request.body)

        vehicle_number = body.get('vehicle_number', '').strip().upper()

        if not vehicle_number:
            return JsonResponse({
                'success': False,
                'error': 'Vehicle number is required.'
            })

        SUREPASS_TOKEN = settings.SUREPASS_TOKEN

        response = requests.post(
            "https://sandbox.surepass.io/api/v1/rc/rc-advance",
            headers={
                "Authorization": f"Bearer {SUREPASS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "id_number": vehicle_number
            },
            timeout=20
        )

        result = response.json()

        if result.get("success"):

            data = result.get("data", {})

            rc = {
                "reg_no": data.get("registration_number"),
                "owner_name": data.get("owner_name"),
                "father_name": data.get("father_name"),
                "address": data.get("permanent_address"),
                "vehicle_class": data.get("vehicle_class"),
                "maker_model": f"{data.get('maker_description','')} / {data.get('model','')}",
                "fuel_type": data.get("fuel_type"),
                "colour": data.get("color"),
                "engine_no": data.get("engine_number"),
                "chassis_no": data.get("chassis_number"),
                "reg_date": data.get("registration_date"),
                "validity": data.get("registration_valid_upto"),
                "fitness_upto": data.get("fitness_upto"),
                "insurance_upto": data.get("insurance_upto"),
                "financer": data.get("financer"),
                "rto": data.get("office_name"),
            }

            return JsonResponse({
                "success": True,
                "rc": rc
            })

        return JsonResponse({
            "success": False,
            "error": result.get("message", "RC details not found.")
        })

    except requests.Timeout:
        return JsonResponse({
            "success": False,
            "error": "API Timeout. Please try again."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })


# -----------------------------
# Vehicle RC List
# -----------------------------
def vehicle_rc_list(request):

    retailer = _get_retailer_from_session(request)

    if retailer is None:
        return redirect('retailer_login')

    from .models import RCAdvanceApplication

    applications = RCAdvanceApplication.objects.filter(
        retailer=retailer
    ).order_by('-id')

    return render(request, "vehicle_rc_list.html", {
        "retailer": retailer,
        "applications": applications
    })


import uuid
from decimal import Decimal
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from .views import _get_retailer_from_session
from .models import DLAllIndiaApplication, WalletTransaction

DL_ALLINDIA_CHARGE = Decimal('25.00')


# -----------------------------
# Driving Licence Services � listing page (Image 1)
# -----------------------------
def driving_services(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'driving_services.html', {'retailer': retailer})


import uuid
from .models import DLAllIndiaApplication

DL_ALLINDIA_CHARGE = Decimal('25.00')


def driving_services(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'driving_services.html', {'retailer': retailer})


def dl_allindia_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')

    applications = DLAllIndiaApplication.objects.filter(retailer=retailer)[:20]
    return render(request, 'dlallindia.html', {
        'retailer': retailer,
        'applications': applications,
        'charge': DL_ALLINDIA_CHARGE,
    })


@require_http_methods(["POST"])
def dl_allindia_api(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Please login first.'}, status=401)

    dl_number = request.POST.get('dl_number', '').strip().upper()
    dob       = request.POST.get('dob', '').strip()

    if not dl_number or not dob:
        return JsonResponse({'success': False, 'error': 'DL Number aur DOB dono zaroori hain.'})

    try:
        d, m, y = dob.split('/')
        dob_api = f"{y}-{m}-{d}"
    except ValueError:
        return JsonResponse({'success': False, 'error': 'DOB format galat hai. DD/MM/YYYY use karein.'})

    current_balance = retailer.wallet_balance or Decimal('0')
    if current_balance < DL_ALLINDIA_CHARGE:
        shortage = DL_ALLINDIA_CHARGE - current_balance
        return JsonResponse({
            'success': False,
            'error': f'Wallet balance kam hai. ?{DL_ALLINDIA_CHARGE} chahiye, aapke paas ?{current_balance} hain. ?{shortage} add karein.'
        }, status=402)

    SUREPASS_TOKEN = settings.SUREPASS_TOKEN
    try:
        response = requests.post(
            "https://sandbox.surepass.io/api/v1/driving-license/driving-license",
            headers={
                "Authorization": f"Bearer {SUREPASS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"id_number": dl_number, "dob": dob_api},
            timeout=20,
        )
        result = response.json()
    except requests.Timeout:
        return JsonResponse({'success': False, 'error': 'API Timeout. Dobara try karein.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    if not result.get("success"):
        return JsonResponse({'success': False, 'error': result.get("message", "DL details nahi mile.")})

    data = result.get("data", {})

    dl_info = {
        "dl_number":     data.get("dl_number") or data.get("license_number") or dl_number,
        "name":          data.get("name") or data.get("full_name"),
        "father_name":   data.get("father_or_husband_name") or data.get("father_name"),
        "dob":           data.get("dob"),
        "address":       data.get("permanent_address") or data.get("address"),
        "issue_date":    data.get("date_of_issue") or data.get("issue_date"),
        "validity_nt":   data.get("nt_validity") or data.get("non_transport_validity"),
        "validity_tr":   data.get("tr_validity") or data.get("transport_validity"),
        "vehicle_class": data.get("vehicle_class") or data.get("cov_details"),
        "rto":           data.get("rto") or data.get("rto_name"),
        "blood_group":   data.get("blood_group"),
    }

    order_id = 'DLA' + uuid.uuid4().hex[:14].upper()

    try:
        with transaction.atomic():
            DLAllIndiaApplication.objects.create(
                retailer=retailer,
                order_id=order_id,
                dl_number=dl_number,
                dob=dob,
                full_name=dl_info.get("name") or "",
                dl_data=dl_info,
                amount=DL_ALLINDIA_CHARGE,
                status='completed',
            )

            retailer.wallet_balance = current_balance - DL_ALLINDIA_CHARGE
            retailer.save(update_fields=['wallet_balance'])

            WalletTransaction.objects.create(
                retailer=retailer,
                amount=DL_ALLINDIA_CHARGE,
                tx_type='debit',
                status='completed',
                payment_provider='internal',
                note=f'DL All India PVC charge � Order ID: {order_id}',
            )
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Application save nahi hui: {e}'}, status=500)

    return JsonResponse({
        'success':         True,
        'order_id':        order_id,
        'dl':              dl_info,
        'wallet_balance':  str(retailer.wallet_balance),
        'amount_deducted': str(DL_ALLINDIA_CHARGE),
    })
import uuid
from django.utils import timezone
from .models import DLKarnatakaApplication

DL_KARNATAKA_CHARGE = Decimal('25.00')


def dl_karnataka_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')

    applications = DLKarnatakaApplication.objects.filter(retailer=retailer)[:100]
    return render(request, 'dl_karnataka.html', {
        'retailer': retailer,
        'applications': applications,
        'charge': DL_KARNATAKA_CHARGE,
    })


@require_http_methods(["POST"])
def dl_karnataka_api(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Please login first.'}, status=401)

    dl_number = request.POST.get('dl_number', '').strip().upper()
    dob       = request.POST.get('dob', '').strip()       # dd-mm-yyyy expected
    photo     = request.FILES.get('photo')
    signature = request.FILES.get('signature')

    if not dl_number or not dob:
        return JsonResponse({'success': False, 'error': 'DL Number aur DOB dono zaroori hain.'})
    if not photo or not signature:
        return JsonResponse({'success': False, 'error': 'Photo aur Signature dono upload karna zaroori hai.'})

    try:
        d, m, y = dob.split('-')
        dob_api = f"{y}-{m}-{d}"
    except ValueError:
        return JsonResponse({'success': False, 'error': 'DOB format galat hai. dd-mm-yyyy use karein.'})

    order_id = 'KAR_DL_' + timezone.now().strftime('%Y%m%d') + '_' + uuid.uuid4().hex[:6].upper()
    current_balance = retailer.wallet_balance or Decimal('0')

    SUREPASS_TOKEN = settings.SUREPASS_TOKEN
    try:
        response = requests.post(
            "https://sandbox.surepass.io/api/v1/driving-license/driving-license",
            headers={"Authorization": f"Bearer {SUREPASS_TOKEN}", "Content-Type": "application/json"},
            json={"id_number": dl_number, "dob": dob_api},
            timeout=20,
        )
        result = response.json()
    except Exception as e:
        result = {"success": False, "message": str(e)}

    # ? API fail � record log hoga status=failed, amount ?0, koi deduction nahi
    if not result.get("success"):
        DLKarnatakaApplication.objects.create(
            retailer=retailer, order_id=order_id, dl_number=dl_number, dob=dob,
            photo=photo, signature=signature, amount=Decimal('0'), status='failed',
        )
        return JsonResponse({
            'success': False,
            'error': result.get("message", "DL details nahi mile."),
            'order_id': order_id,
        })

    # ? API success � wallet check yahan karenge (fail hua toh charge hi nahi hoga)
    if current_balance < DL_KARNATAKA_CHARGE:
        shortage = DL_KARNATAKA_CHARGE - current_balance
        return JsonResponse({
            'success': False,
            'error': f'Wallet balance kam hai. ?{DL_KARNATAKA_CHARGE} chahiye, ?{shortage} aur add karein.'
        }, status=402)

    data = result.get("data", {})
    dl_info = {
        "name":          data.get("name") or data.get("full_name"),
        "vehicle_class": data.get("vehicle_class") or data.get("cov_details"),
        "dob":           data.get("dob"),
        "address":       data.get("permanent_address") or data.get("address"),
        "issue_date":    data.get("date_of_issue") or data.get("issue_date"),
        "validity_nt":   data.get("nt_validity") or data.get("non_transport_validity"),
        "validity_tr":   data.get("tr_validity") or data.get("transport_validity"),
        "rto":           data.get("rto") or data.get("rto_name"),
    }

    try:
        with transaction.atomic():
            DLKarnatakaApplication.objects.create(
                retailer=retailer, order_id=order_id, dl_number=dl_number, dob=dob,
                full_name=dl_info.get('name') or '', vehicle_type=dl_info.get('vehicle_class') or '',
                dl_data=dl_info, photo=photo, signature=signature,
                amount=DL_KARNATAKA_CHARGE, status='success',
            )
            retailer.wallet_balance = current_balance - DL_KARNATAKA_CHARGE
            retailer.save(update_fields=['wallet_balance'])
            WalletTransaction.objects.create(
                retailer=retailer, amount=DL_KARNATAKA_CHARGE, tx_type='debit',
                status='completed', payment_provider='internal',
                note=f'DL Karnataka PVC charge � Order ID: {order_id}',
            )
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({
        'success':         True,
        'order_id':        order_id,
        'dl':              dl_info,
        'vehicle_type':    dl_info.get('vehicle_class'),
        'wallet_balance':  str(retailer.wallet_balance),
        'amount_deducted': str(DL_KARNATAKA_CHARGE),
    })


def dl_karnataka_view_card(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    try:
        app_obj = DLKarnatakaApplication.objects.get(order_id=order_id, retailer=retailer, status='success')
    except DLKarnatakaApplication.DoesNotExist:
        return render(request, 'dl_karnataka_card.html', {'error': 'Card abhi available nahi hai.'})
    return render(request, 'dl_karnataka_card.html', {'app': app_obj})

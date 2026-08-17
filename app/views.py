from django.shortcuts import render, redirect, get_object_or_404
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

from .models import Retailer, PaymentRequest, PANApplication, WalletTransaction, AadhaarPdfApplication, EidToUidApplication, LMSCertificateApplication, PanToAadhaarApplication, SeniorCitizenApplication, GruhaLaxmiApplication, GruhaLaxmiStatusApplication, GruhaLaxmiKYCApplication, GruhaLaxmiSanctionApplication, GruhaJyothiApplication, GruhaJyothiDlinkApplication, BhoomiPahaniLinkApplication, RTCDownloadApplication, AbhaCardApplication, AyushCardApplication, AyushDownloadApplication, EShramApplication, EShramDownloadApplication, PMKisanApplication, NaadaKacheriDownloadApplication, YuvaNidhiApplication, SSPPasswordChangeApplication, SSPMobileLinkApplication, MobileToPanApplication
from .vehicle_views import vehicle_rc_allindia_pdf

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
    # Agar user pehle se logged in hai, to seedha dashboard par bhejo
    if _get_retailer_from_session(request) is not None:
        return redirect('retailer_dashboard')

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
        request.session.set_expiry(86400 * 30) # 30 Days persistent login
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
            "https://kyc-api.surepass.app/api/v1/rc/rc-v2",
            headers={
                "Authorization": f"Bearer {SUREPASS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "id_number": vehicle_number,
                "enrich": False
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


def tailoring_certificate_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'tailoring_certificate.html', {'retailer': retailer})


def tailoring_certificate_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please login again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    full_name = request.POST.get('full_name', '').strip()
    mobile_number = request.POST.get('mobile_number', '').strip()
    email_id = request.POST.get('email_id', '').strip()
    confirm_email = request.POST.get('confirm_email', '').strip()
    gender = request.POST.get('gender', '').strip()
    date_of_birth = request.POST.get('date_of_birth', '').strip()
    father_husband_name = request.POST.get('father_husband_name', '').strip()

    state = request.POST.get('state', '').strip()
    district = request.POST.get('district', '').strip()
    taluk = request.POST.get('taluk', '').strip()
    village = request.POST.get('village', '').strip()
    pin_code = request.POST.get('pin_code', '').strip()
    physical_handicap = request.POST.get('physical_handicap', '').strip()
    address = request.POST.get('address', '').strip()

    highest_education = request.POST.get('highest_education', '').strip()

    photo = request.FILES.get('photo')
    id_proof = request.FILES.get('id_proof')
    education_cert = request.FILES.get('education_cert')

    if not (full_name and mobile_number and email_id and gender and date_of_birth and father_husband_name and state and district and taluk and village and pin_code and physical_handicap and address and highest_education and id_proof):
        return JsonResponse({'success': False, 'error': 'Kripya sabhi required fields bharein.'}, status=400)

    if email_id.lower() != confirm_email.lower():
        return JsonResponse({'success': False, 'error': 'Email ID aur Confirm Email ID match nahi ho rahe hain.'}, status=400)

    charge_amount = Decimal('450.00')
    if retailer.wallet_balance < charge_amount:
        shortage = charge_amount - retailer.wallet_balance
        return JsonResponse({
            'success': False,
            'error': f'Wallet balance kam hai. ₹{charge_amount} chahiye, ₹{shortage} aur add karein.'
        }, status=402)

    try:
        from .models import TailoringCertificateApplication
        with transaction.atomic():
            app_obj = TailoringCertificateApplication.objects.create(
                retailer=retailer,
                full_name=full_name,
                mobile_number=mobile_number,
                email_id=email_id,
                gender=gender,
                date_of_birth=date_of_birth,
                father_husband_name=father_husband_name,
                state=state,
                district=district,
                taluk=taluk,
                village=village,
                pin_code=pin_code,
                physical_handicap=physical_handicap,
                address=address,
                highest_education=highest_education,
                photo=photo,
                id_proof=id_proof,
                education_cert=education_cert,
                amount=charge_amount,
                status='PENDING'
            )
            retailer.wallet_balance -= charge_amount
            retailer.save(update_fields=['wallet_balance'])

            WalletTransaction.objects.create(
                retailer=retailer,
                amount=charge_amount,
                tx_type='debit',
                status='completed',
                payment_provider='internal',
                note=f'Tailoring Certificate Application — Order ID: {app_obj.order_id}'
            )

        return JsonResponse({
            'success': True,
            'order_id': app_obj.order_id,
            'message': 'Tailoring Certificate Application successfully submit ho gayi hai!',
            'wallet_balance': str(retailer.wallet_balance)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def tailoring_certificate_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import TailoringCertificateApplication
    apps = TailoringCertificateApplication.objects.filter(retailer=retailer)
    return render(request, 'tailoring_certificate_list.html', {'retailer': retailer, 'applications': apps})


def tailoring_certificate_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import TailoringCertificateApplication
    app_obj = get_object_or_404(TailoringCertificateApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'tailoring_certificate_list.html', {'retailer': retailer, 'error': 'Certificate PDF abhi upload nahi hua hai.'})


def other_services_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'other_services.html', {'retailer': retailer})


def kar_gov_services_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'kar_gov_services.html', {'retailer': retailer})



def print_services_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'print_services.html', {'retailer': retailer})


def voter_services_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'voter_services.html', {'retailer': retailer})


def ration_services_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'ration_services.html', {'retailer': retailer})


def aadhaar_services_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'aadhaar_services.html', {'retailer': retailer})


def basic_computer_certificate_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'basic_computer_certificate.html', {'retailer': retailer})


def basic_computer_certificate_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        from .models import BasicComputerCertificateApplication
        charge_amount = Decimal('400.00')

        if retailer.wallet_balance < charge_amount:
            return JsonResponse({'success': False, 'error': f'Insufficient wallet balance! ₹{charge_amount} required, but your balance is ₹{retailer.wallet_balance}.'}, status=400)

        student_name  = request.POST.get('student_name', '').strip()
        father_name   = request.POST.get('father_name', '').strip()
        mother_name   = request.POST.get('mother_name', '').strip()
        dob_str       = request.POST.get('dob', '').strip()
        gender        = request.POST.get('gender', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        cast_category = request.POST.get('cast_category', '').strip()
        state         = request.POST.get('state', '').strip()
        district      = request.POST.get('district', '').strip()
        full_address  = request.POST.get('full_address', '').strip()
        pin_code      = request.POST.get('pin_code', '').strip()
        mobile_no     = request.POST.get('mobile_no', '').strip()
        email_id      = request.POST.get('email_id', '').strip()

        photo_file    = request.FILES.get('photo')

        if not all([student_name, father_name, mother_name, dob_str, gender, qualification, cast_category, state, district, full_address, pin_code, mobile_no, email_id]):
            return JsonResponse({'success': False, 'error': 'All mandatory fields must be filled.'}, status=400)

        with transaction.atomic():
            retailer.wallet_balance -= charge_amount
            retailer.save(update_fields=['wallet_balance'])

            app_obj = BasicComputerCertificateApplication.objects.create(
                retailer=retailer,
                student_name=student_name,
                father_name=father_name,
                mother_name=mother_name,
                date_of_birth=dob_str,
                gender=gender,
                qualification=qualification,
                cast_category=cast_category,
                state=state,
                district=district,
                full_address=full_address,
                pin_code=pin_code,
                mobile_no=mobile_no,
                email_id=email_id,
                photo=photo_file,
                amount=charge_amount,
                status='PENDING',
            )

            WalletTransaction.objects.create(
                retailer=retailer,
                amount=charge_amount,
                tx_type='debit',
                status='completed',
                payment_provider='internal',
                note=f'Basic Computer Certificate Application — Order ID: {app_obj.order_id}'
            )

        return JsonResponse({
            'success': True,
            'order_id': app_obj.order_id,
            'message': 'Basic Computer Certificate Application successfully submit ho gayi hai!',
            'wallet_balance': str(retailer.wallet_balance)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def basic_computer_certificate_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import BasicComputerCertificateApplication
    apps = BasicComputerCertificateApplication.objects.filter(retailer=retailer)
    return render(request, 'basic_computer_certificate_list.html', {'retailer': retailer, 'applications': apps})


def basic_computer_certificate_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import BasicComputerCertificateApplication
    app_obj = get_object_or_404(BasicComputerCertificateApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'basic_computer_certificate_list.html', {'retailer': retailer, 'error': 'Certificate PDF abhi upload nahi hua hai.'})


def udyam_registration_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'udyam_registration.html', {'retailer': retailer})


def udyam_registration_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        from .models import UdyamRegistrationApplication
        charge_amount = Decimal('100.00')

        if retailer.wallet_balance < charge_amount:
            return JsonResponse({'success': False, 'error': f'Insufficient wallet balance! ₹{charge_amount} required, but your balance is ₹{retailer.wallet_balance}.'}, status=400)

        applicant_name   = request.POST.get('applicant_name', '').strip()
        aadhaar_no       = request.POST.get('aadhaar_no', '').strip()
        dob_str          = request.POST.get('date_of_birth', '').strip() or None
        email_id         = request.POST.get('email_id', '').strip()
        mobile_no        = request.POST.get('mobile_no', '').strip()
        pan_card_no      = request.POST.get('pan_card_no', '').strip()

        business_name    = request.POST.get('business_name', '').strip()
        business_type    = request.POST.get('business_type', '').strip()
        business_address = request.POST.get('business_address', '').strip()
        working_member   = request.POST.get('working_member', '').strip()
        gst_number       = request.POST.get('gst_number', '').strip()
        annual_income    = request.POST.get('annual_income', '').strip()

        bank_name        = request.POST.get('bank_name', '').strip()
        ifsc_code        = request.POST.get('ifsc_code', '').strip()
        account_no       = request.POST.get('account_no', '').strip()

        aadhaar_file     = request.FILES.get('aadhaar_file')
        pan_file         = request.FILES.get('pan_file')
        passbook_file    = request.FILES.get('bank_passbook_file')

        if not applicant_name:
            return JsonResponse({'success': False, 'error': 'Applicant name is required.'}, status=400)

        with transaction.atomic():
            retailer.wallet_balance -= charge_amount
            retailer.save(update_fields=['wallet_balance'])

            app_obj = UdyamRegistrationApplication.objects.create(
                retailer=retailer,
                applicant_name=applicant_name,
                aadhaar_no=aadhaar_no,
                date_of_birth=dob_str if dob_str else None,
                email_id=email_id,
                mobile_no=mobile_no,
                pan_card_no=pan_card_no,
                business_name=business_name,
                business_type=business_type,
                business_address=business_address,
                working_member=working_member,
                gst_number=gst_number,
                annual_income=annual_income,
                bank_name=bank_name,
                ifsc_code=ifsc_code,
                account_no=account_no,
                aadhaar_file=aadhaar_file,
                pan_file=pan_file,
                bank_passbook_file=passbook_file,
                amount=charge_amount,
                status='PENDING',
            )

            WalletTransaction.objects.create(
                retailer=retailer,
                amount=charge_amount,
                tx_type='debit',
                status='completed',
                payment_provider='internal',
                note=f'Udyam Registration Application — Order ID: {app_obj.order_id}'
            )

        return JsonResponse({
            'success': True,
            'order_id': app_obj.order_id,
            'message': 'Udyam Registration Application successfully submit ho gayi hai!',
            'wallet_balance': str(retailer.wallet_balance)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def udyam_registration_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import UdyamRegistrationApplication
    apps = UdyamRegistrationApplication.objects.filter(retailer=retailer)
    return render(request, 'udyam_registration_list.html', {'retailer': retailer, 'applications': apps})


def udyam_registration_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import UdyamRegistrationApplication
    app_obj = get_object_or_404(UdyamRegistrationApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'udyam_registration_list.html', {'retailer': retailer, 'error': 'Udyam Certificate PDF abhi upload nahi hua hai.'})


def pvc_maker_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'pvc_maker.html', {'retailer': retailer})


def pvc_maker_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        from .models import PVCMakerApplication
        charge_amount = Decimal('150.00')

        if retailer.wallet_balance < charge_amount:
            return JsonResponse({'success': False, 'error': f'Insufficient wallet balance! ₹{charge_amount} required, but your balance is ₹{retailer.wallet_balance}.'}, status=400)

        pvc_card_type   = request.POST.get('pvc_card_type', '').strip()
        service_types_list = request.POST.getlist('service_type[]')
        service_types   = ','.join(service_types_list)

        agent_mobile    = request.POST.get('agent_mobile', '').strip()
        customer_mobile = request.POST.get('customer_mobile', '').strip()
        full_name       = request.POST.get('full_name', '').strip()
        village         = request.POST.get('village', '').strip()
        taluk           = request.POST.get('taluk', '').strip()
        district        = request.POST.get('district', '').strip()
        pincode         = request.POST.get('pincode', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()

        pdf_file        = request.FILES.get('pdf_file')
        card_number     = request.POST.get('card_number', '').strip()

        if not pvc_card_type or not full_name or not delivery_address:
            return JsonResponse({'success': False, 'error': 'PVC card type, full name, and delivery address are required.'}, status=400)

        with transaction.atomic():
            retailer.wallet_balance -= charge_amount
            retailer.save(update_fields=['wallet_balance'])

            app_obj = PVCMakerApplication.objects.create(
                retailer=retailer,
                pvc_card_type=pvc_card_type,
                service_types=service_types,
                agent_mobile=agent_mobile,
                customer_mobile=customer_mobile,
                full_name=full_name,
                village=village,
                taluk=taluk,
                district=district,
                pincode=pincode,
                delivery_address=delivery_address,
                pdf_file=pdf_file,
                card_number=card_number,
                amount=charge_amount,
                status='PENDING',
            )

            WalletTransaction.objects.create(
                retailer=retailer,
                amount=charge_amount,
                tx_type='debit',
                status='completed',
                payment_provider='internal',
                note=f'PVC Card Maker Application — Order ID: {app_obj.order_id}'
            )

        return JsonResponse({
            'success': True,
            'order_id': app_obj.order_id,
            'message': 'PVC Card Maker Application successfully submit ho gayi hai!',
            'wallet_balance': str(retailer.wallet_balance)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def pvc_maker_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import PVCMakerApplication
    apps = PVCMakerApplication.objects.filter(retailer=retailer)
    return render(request, 'pvc_maker_list.html', {'retailer': retailer, 'applications': apps})


def pvc_maker_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import PVCMakerApplication
    app_obj = get_object_or_404(PVCMakerApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'pvc_maker_list.html', {'retailer': retailer, 'error': 'PVC Card PDF abhi upload nahi hua hai.'})


def cibil_score_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'cibil_score.html', {'retailer': retailer})


def cibil_score_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        from .models import CibilScoreApplication
        charge_amount = Decimal('120.00')

        if retailer.wallet_balance < charge_amount:
            return JsonResponse({'success': False, 'error': f'Insufficient wallet balance! ₹{charge_amount} required, but your balance is ₹{retailer.wallet_balance}.'}, status=400)

        first_name     = request.POST.get('firstName', '').strip()
        last_name      = request.POST.get('lastname', '').strip()
        pan_number     = request.POST.get('panNumber', '').strip()
        mobile_number  = request.POST.get('mobileNumber', '').strip()
        aadhaar_number = request.POST.get('aadhaar_number', '').strip()

        if not first_name or not last_name or not pan_number or not mobile_number:
            return JsonResponse({'success': False, 'error': 'First name, last name, PAN number, and mobile number are required.'}, status=400)

        with transaction.atomic():
            retailer.wallet_balance -= charge_amount
            retailer.save(update_fields=['wallet_balance'])

            app_obj = CibilScoreApplication.objects.create(
                retailer=retailer,
                first_name=first_name,
                last_name=last_name,
                pan_number=pan_number,
                mobile_number=mobile_number,
                aadhaar_number=aadhaar_number,
                amount=charge_amount,
                status='PENDING',
            )

            WalletTransaction.objects.create(
                retailer=retailer,
                amount=charge_amount,
                tx_type='debit',
                status='completed',
                payment_provider='internal',
                note=f'CIBIL Score Report Application — Order ID: {app_obj.order_id}'
            )

        return JsonResponse({
            'success': True,
            'order_id': app_obj.order_id,
            'message': 'CIBIL Score Application successfully submit ho gayi hai!',
            'wallet_balance': str(retailer.wallet_balance)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def cibil_score_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import CibilScoreApplication
    apps = CibilScoreApplication.objects.filter(retailer=retailer)
    return render(request, 'cibil_score_list.html', {'retailer': retailer, 'applications': apps})


def cibil_score_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from .models import CibilScoreApplication
    app_obj = get_object_or_404(CibilScoreApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'cibil_score_list.html', {'retailer': retailer, 'error': 'CIBIL Report PDF abhi upload nahi hua hai.'})


def free_tools_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'free_tools.html', {'retailer': retailer})


def free_resume_maker_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'free_resume_maker.html', {'retailer': retailer})


def free_jpg_to_pdf_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'free_jpg_to_pdf.html', {'retailer': retailer})


def free_pdf_to_jpg_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'free_pdf_to_jpg.html', {'retailer': retailer})


def free_photo_maker_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'free_photo_maker.html', {'retailer': retailer})


def free_bg_remover_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'free_bg_remover.html', {'retailer': retailer})


def free_pvc_maker_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'free_pvc_maker.html', {'retailer': retailer})


def profile_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')

    success_msg = None
    error_msg = None

    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        state = request.POST.get('state', '').strip()
        address = request.POST.get('address', '').strip()
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if fullname:
            retailer.full_name = fullname
        retailer.state = state
        retailer.address = address

        if current_password or new_password or confirm_password:
            if not check_password(current_password, retailer.password):
                error_msg = "Current password is incorrect."
            elif not new_password or len(new_password) < 6:
                error_msg = "New password must be at least 6 characters."
            elif new_password != confirm_password:
                error_msg = "New passwords do not match."
            else:
                retailer.set_password(new_password)

        if not error_msg:
            retailer.save()
            success_msg = "Profile updated successfully!"

    return render(request, 'profile.html', {
        'retailer': retailer,
        'success_msg': success_msg,
        'error_msg': error_msg
    })


def aadhaar_pdf_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'aadhaar_pdf.html', {'retailer': retailer})


def aadhaar_pdf_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    uid_number = request.POST.get('uid_number', '').strip()
    name = request.POST.get('name', '').strip().upper()

    if not uid_number or len(uid_number) != 12 or not uid_number.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit UID Number is required.'})

    if not name or len(name) < 2:
        return JsonResponse({'success': False, 'error': 'Valid Name is required.'})

    cost = Decimal('1000.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    # Deduct wallet & record transaction
    retailer.wallet_balance -= cost
    retailer.save()

    app_obj = AadhaarPdfApplication.objects.create(
        retailer=retailer,
        uid_number=uid_number,
        name=name,
        amount=cost,
        status='PENDING'
    )

    WalletTransaction.objects.create(
        retailer=retailer,
        amount=cost,
        tx_type='debit',
        status='completed'
    )

    return JsonResponse({'success': True, 'message': 'Application submitted successfully!', 'order_id': app_obj.order_id})


def aadhaar_pdf_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = AadhaarPdfApplication.objects.filter(retailer=retailer)
    return render(request, 'aadhaar_pdf_list.html', {'retailer': retailer, 'applications': applications})


def aadhaar_pdf_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(AadhaarPdfApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'aadhaar_pdf_list.html', {'retailer': retailer, 'error': 'Aadhaar PDF report is not ready yet.'})


def eid_to_uid_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'eid_to_uid.html', {'retailer': retailer})


def eid_to_uid_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    eid_number = request.POST.get('eid_number', '').strip()
    upload_slip = request.FILES.get('upload_slip')

    if not eid_number or len(eid_number) != 28 or not eid_number.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 28-digit EID Number is required.'})

    if not upload_slip:
        return JsonResponse({'success': False, 'error': 'Upload Slip file is required.'})

    cost = Decimal('750.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    # Deduct wallet & record transaction
    retailer.wallet_balance -= cost
    retailer.save()

    app_obj = EidToUidApplication.objects.create(
        retailer=retailer,
        eid_number=eid_number,
        upload_slip=upload_slip,
        amount=cost,
        status='PENDING'
    )

    WalletTransaction.objects.create(
        retailer=retailer,
        amount=cost,
        tx_type='debit',
        status='completed'
    )

    return JsonResponse({'success': True, 'message': 'EID to UID Application submitted successfully!', 'order_id': app_obj.order_id})


def eid_to_uid_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = EidToUidApplication.objects.filter(retailer=retailer)
    return render(request, 'eid_to_uid_list.html', {'retailer': retailer, 'applications': applications})


def eid_to_uid_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(EidToUidApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'eid_to_uid_list.html', {'retailer': retailer, 'error': 'EID to UID report is not ready yet.'})


def lms_certificate_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'lms_certificate.html', {'retailer': retailer})


def lms_certificate_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    full_name = request.POST.get('full_name', '').strip().upper()
    aadhaarno = request.POST.get('aadhaarno', '').strip()
    email = request.POST.get('email', '').strip().lower()
    mobile = request.POST.get('mobile', '').strip()
    state = request.POST.get('state', '').strip()
    district = request.POST.get('district', '').strip().upper()
    taluka = request.POST.get('taluka', '').strip().upper()
    native_place = request.POST.get('native_place', '').strip().upper()

    if not full_name or len(full_name) < 2:
        return JsonResponse({'success': False, 'error': 'Valid Full Name is required.'})

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not email or '@' not in email:
        return JsonResponse({'success': False, 'error': 'Valid Email Address is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not state or not district or not taluka or not native_place:
        return JsonResponse({'success': False, 'error': 'State, District, Taluka and Native Place are required.'})

    cost = Decimal('1000.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    # Deduct wallet & record transaction
    retailer.wallet_balance -= cost
    retailer.save()

    app_obj = LMSCertificateApplication.objects.create(
        retailer=retailer,
        full_name=full_name,
        aadhaar_number=aadhaarno,
        email=email,
        mobile=mobile,
        state=state,
        district=district,
        taluka=taluka,
        native_place=native_place,
        amount=cost,
        status='PENDING'
    )

    WalletTransaction.objects.create(
        retailer=retailer,
        amount=cost,
        tx_type='debit',
        status='completed'
    )

    return JsonResponse({'success': True, 'message': 'LMS Certificate Application submitted successfully!', 'order_id': app_obj.order_id})


def lms_certificate_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = LMSCertificateApplication.objects.filter(retailer=retailer)
    return render(request, 'lms_certificate_list.html', {'retailer': retailer, 'applications': applications})


def lms_certificate_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(LMSCertificateApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'lms_certificate_list.html', {'retailer': retailer, 'error': 'LMS Certificate is not ready yet.'})


def pan_services_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'pan_services.html', {'retailer': retailer})


def pan_to_aadhaar_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = PanToAadhaarApplication.objects.filter(retailer=retailer)
    return render(request, 'pan_to_aadhaar.html', {'retailer': retailer, 'applications': applications})


def pan_to_aadhaar_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    panno = request.POST.get('panno', '').strip().upper()

    if not panno or len(panno) != 10 or not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', panno):
        return JsonResponse({'success': False, 'error': 'Valid 10-character PAN Number (e.g. ABCDE1234F) is required.'})

    cost = Decimal('200.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    # Deduct wallet & record transaction
    retailer.wallet_balance -= cost
    retailer.save()

    app_obj = PanToAadhaarApplication.objects.create(
        retailer=retailer,
        pan_number=panno,
        amount=cost,
        status='PENDING'
    )

    WalletTransaction.objects.create(
        retailer=retailer,
        amount=cost,
        tx_type='debit',
        status='completed'
    )

    return JsonResponse({'success': True, 'message': 'PAN to Aadhaar Application submitted successfully!', 'order_id': app_obj.order_id})


def pricing_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'pricing.html', {'retailer': retailer})


# ── Senior Citizen Application ──────────────────────────────────────

def senior_citizen_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'senior_citizen.html', {'retailer': retailer})


def senior_citizen_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    aadhaarno = request.POST.get('aadhaarno', '').strip()
    mobile = request.POST.get('mobile', '').strip()
    email = request.POST.get('email', '').strip().lower()
    gender = request.POST.get('gender', '').strip()
    dob = request.POST.get('dob', '').strip()
    address = request.POST.get('address', '').strip().upper()
    talluk = request.POST.get('talluk', '').strip().upper()
    district = request.POST.get('district', '').strip().upper()
    pincode = request.POST.get('pincode', '').strip()

    photo_file = request.FILES.get('photo_file')
    aadhaar_file = request.FILES.get('aadhaar_file')
    blood_file = request.FILES.get('blood_file')

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required (minimum 2 characters).'})

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not email or '@' not in email:
        return JsonResponse({'success': False, 'error': 'Valid Email Address is required.'})

    if not gender or gender in ['Select...', '']:
        return JsonResponse({'success': False, 'error': 'Gender is required.'})

    if not dob:
        return JsonResponse({'success': False, 'error': 'Date of Birth is required.'})

    if not address or not talluk or not district:
        return JsonResponse({'success': False, 'error': 'Address, Talluk, and District are required.'})

    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 6-digit Pincode is required.'})

    if not photo_file:
        return JsonResponse({'success': False, 'error': 'Applicant Photo file is required.'})

    if not aadhaar_file:
        return JsonResponse({'success': False, 'error': 'Aadhaar document PDF is required.'})

    if not blood_file:
        return JsonResponse({'success': False, 'error': 'Blood Group Report PDF is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    # Deduct wallet & record transaction atomically
    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = SeniorCitizenApplication.objects.create(
            retailer=retailer,
            applicant_name=applicant_name,
            aadhaar_number=aadhaarno,
            mobile=mobile,
            email=email,
            gender=gender,
            dob=dob,
            address=address,
            talluk=talluk,
            district=district,
            pincode=pincode,
            photo=photo_file,
            aadhaar_file=aadhaar_file,
            blood_file=blood_file,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Senior Citizen Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Senior Citizen Application submitted successfully!', 'order_id': app_obj.order_id})


def senior_citizen_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = SeniorCitizenApplication.objects.filter(retailer=retailer)
    return render(request, 'senior_citizen_list.html', {'retailer': retailer, 'applications': applications})


def senior_citizen_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(SeniorCitizenApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'senior_citizen_list.html', {'retailer': retailer, 'error': 'Senior Citizen Card/Certificate is not ready yet.'})


# ── Gruha Laxmi Application ───────────────────────────────────────

def gruha_laxmi_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'gruha_laxmi.html', {'retailer': retailer})


def gruha_laxmi_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    rationno = request.POST.get('rationno', '').strip()
    aadhaarno = request.POST.get('aadhaarno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()

    if not rationno or len(rationno) < 5 or not rationno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid Ration Card Number is required (minimum 5 digits).'})

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required (minimum 2 characters).'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    # Deduct wallet & record transaction atomically
    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = GruhaLaxmiApplication.objects.create(
            retailer=retailer,
            ration_number=rationno,
            aadhaar_number=aadhaarno,
            applicant_name=applicant_name,
            mobile=mobile,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Gruha Laxmi Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Gruha Laxmi Application submitted successfully!', 'order_id': app_obj.order_id})


def gruha_laxmi_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = GruhaLaxmiApplication.objects.filter(retailer=retailer)
    return render(request, 'gruha_laxmi_list.html', {'retailer': retailer, 'applications': applications})


def gruha_laxmi_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(GruhaLaxmiApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'gruha_laxmi_list.html', {'retailer': retailer, 'error': 'Gruha Laxmi Sanction/Document is not ready yet.'})


# ── Gruha Laxmi Status Application ─────────────────────────────────

def gruha_laxmi_status_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'gruha_laxmi_status.html', {'retailer': retailer})


def gruha_laxmi_status_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    rationno = request.POST.get('rationno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()

    if not rationno or len(rationno) < 5 or not rationno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid Ration Card Number is required (minimum 5 digits).'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required (minimum 2 characters).'})

    cost = Decimal('30.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = GruhaLaxmiStatusApplication.objects.create(
            retailer=retailer,
            ration_number=rationno,
            applicant_name=applicant_name,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Gruha Laxmi Status Request — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Gruha Laxmi Status Request submitted successfully!', 'order_id': app_obj.order_id})


def gruha_laxmi_status_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = GruhaLaxmiStatusApplication.objects.filter(retailer=retailer)
    return render(request, 'gruha_laxmi_status_list.html', {'retailer': retailer, 'applications': applications})


def gruha_laxmi_status_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(GruhaLaxmiStatusApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'gruha_laxmi_status_list.html', {'retailer': retailer, 'error': 'Gruha Laxmi Status Report is not ready yet.'})


# ── Gruha Laxmi KYC Application ────────────────────────────────────

def gruha_laxmi_kyc_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'gruha_laxmi_kyc.html', {'retailer': retailer})


def gruha_laxmi_kyc_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    rationno = request.POST.get('rationno', '').strip()
    aadhaarno = request.POST.get('aadhaarno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()

    if not rationno or len(rationno) < 5 or not rationno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid Ration Card Number is required (minimum 5 digits).'})

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required (minimum 2 characters).'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = GruhaLaxmiKYCApplication.objects.create(
            retailer=retailer,
            ration_number=rationno,
            aadhaar_number=aadhaarno,
            applicant_name=applicant_name,
            mobile=mobile,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Gruha Laxmi e-KYC Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Gruha Laxmi e-KYC Application submitted successfully!', 'order_id': app_obj.order_id})


def gruha_laxmi_kyc_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = GruhaLaxmiKYCApplication.objects.filter(retailer=retailer)
    return render(request, 'gruha_laxmi_kyc_list.html', {'retailer': retailer, 'applications': applications})


def gruha_laxmi_kyc_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(GruhaLaxmiKYCApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'gruha_laxmi_kyc_list.html', {'retailer': retailer, 'error': 'Gruha Laxmi e-KYC Document is not ready yet.'})


# ── Gruha Laxmi Sanction Order Application ─────────────────────────

def gruha_laxmi_sanction_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'gruha_laxmi_sanction.html', {'retailer': retailer})


def gruha_laxmi_sanction_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    rationno = request.POST.get('rationno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()

    if not rationno or len(rationno) < 5 or not rationno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid Ration Card Number is required (minimum 5 digits).'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required (minimum 2 characters).'})

    cost = Decimal('30.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = GruhaLaxmiSanctionApplication.objects.create(
            retailer=retailer,
            ration_number=rationno,
            applicant_name=applicant_name,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Gruha Laxmi Sanction Order Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Gruha Laxmi Sanction Order Application submitted successfully!', 'order_id': app_obj.order_id})


def gruha_laxmi_sanction_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = GruhaLaxmiSanctionApplication.objects.filter(retailer=retailer)
    return render(request, 'gruha_laxmi_sanction_list.html', {'retailer': retailer, 'applications': applications})


def gruha_laxmi_sanction_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(GruhaLaxmiSanctionApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'gruha_laxmi_sanction_list.html', {'retailer': retailer, 'error': 'Gruha Laxmi Sanction Order Document is not ready yet.'})


# ── Gruha Jyothi Application ───────────────────────────────────────

def gruha_jyothi_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'gruha_jyothi.html', {'retailer': retailer})


def gruha_jyothi_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    escom = request.POST.get('escom', '').strip()
    rrid = request.POST.get('rrid', '').strip().upper()
    rrname = request.POST.get('rrname', '').strip().upper()
    rraddrss = request.POST.get('rraddrss', '').strip().upper()
    occupany = request.POST.get('occupany', '').strip()
    aadhaarno = request.POST.get('aadhaarno', '').strip()
    aadhaarname = request.POST.get('aadhaarname', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()

    if not escom:
        return JsonResponse({'success': False, 'error': 'Please select ESCOM.'})

    if not rrid or len(rrid) < 3:
        return JsonResponse({'success': False, 'error': 'Account ID / Connection ID is required.'})

    if not rrname or len(rrname) < 2:
        return JsonResponse({'success': False, 'error': 'Account Holder Name is required.'})

    if not rraddrss or len(rraddrss) < 5:
        return JsonResponse({'success': False, 'error': 'Account Holder Address is required.'})

    if not occupany:
        return JsonResponse({'success': False, 'error': 'Please select Type of Occupancy.'})

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not aadhaarname or len(aadhaarname) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = GruhaJyothiApplication.objects.create(
            retailer=retailer,
            escom=escom,
            account_id=rrid,
            account_holder_name=rrname,
            account_holder_address=rraddrss,
            occupancy_type=occupany,
            aadhaar_number=aadhaarno,
            applicant_name=aadhaarname,
            mobile=mobile,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Gruha Jyothi Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Gruha Jyothi Application submitted successfully!', 'order_id': app_obj.order_id})


def gruha_jyothi_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = GruhaJyothiApplication.objects.filter(retailer=retailer)
    return render(request, 'gruha_jyothi_list.html', {'retailer': retailer, 'applications': applications})


def gruha_jyothi_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(GruhaJyothiApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'gruha_jyothi_list.html', {'retailer': retailer, 'error': 'Gruha Jyothi Document is not ready yet.'})


# ── Gruha Jyothi D-Link Application ────────────────────────────────

def gruha_jyothi_dlink_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'gruha_jyothi_dlink.html', {'retailer': retailer})


def gruha_jyothi_dlink_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    aadhaarno = request.POST.get('aadhaarno', '').strip()
    aadhaarname = request.POST.get('aadhaarname', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()
    state = request.POST.get('state', '').strip().upper()

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not aadhaarname or len(aadhaarname) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not state or len(state) < 2:
        return JsonResponse({'success': False, 'error': 'District is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = GruhaJyothiDlinkApplication.objects.create(
            retailer=retailer,
            aadhaar_number=aadhaarno,
            applicant_name=aadhaarname,
            mobile=mobile,
            district=state,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Gruha Jyothi D-Link Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Gruha Jyothi D-Link Application submitted successfully!', 'order_id': app_obj.order_id})


def gruha_jyothi_dlink_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = GruhaJyothiDlinkApplication.objects.filter(retailer=retailer)
    return render(request, 'gruha_jyothi_dlink_list.html', {'retailer': retailer, 'applications': applications})


def gruha_jyothi_dlink_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(GruhaJyothiDlinkApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'gruha_jyothi_dlink_list.html', {'retailer': retailer, 'error': 'Gruha Jyothi D-Link Document is not ready yet.'})


# ── Bhoomi Pahani Link Application ─────────────────────────────────

def bhoomi_pahani_link_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'bhoomi_pahani_link.html', {'retailer': retailer})


def bhoomi_pahani_link_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    aadhaarno = request.POST.get('aadhaarno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()
    district = request.POST.get('district', '').strip().upper()
    assembly = request.POST.get('assembly', '').strip().upper()
    hobli = request.POST.get('hobli', '').strip().upper()
    village = request.POST.get('village', '').strip().upper()
    survey = request.POST.get('survey', '').strip().upper()
    hissa = request.POST.get('hissa', '').strip().upper()

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not district or district == 'SELECT...':
        return JsonResponse({'success': False, 'error': 'District is required.'})

    if not assembly or len(assembly) < 2:
        return JsonResponse({'success': False, 'error': 'Talluk is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = BhoomiPahaniLinkApplication.objects.create(
            retailer=retailer,
            aadhaar_number=aadhaarno,
            applicant_name=applicant_name,
            mobile=mobile,
            district=district,
            talluk=assembly,
            hobli=hobli,
            village=village,
            survey_no=survey,
            hissa_no=hissa,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Bhoomi Pahani Link Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Aadhaar & Pahani Link Application submitted successfully!', 'order_id': app_obj.order_id})


def bhoomi_pahani_link_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = BhoomiPahaniLinkApplication.objects.filter(retailer=retailer)
    return render(request, 'bhoomi_pahani_link_list.html', {'retailer': retailer, 'applications': applications})


def bhoomi_pahani_link_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(BhoomiPahaniLinkApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'bhoomi_pahani_link_list.html', {'retailer': retailer, 'error': 'Bhoomi Pahani Link Document is not ready yet.'})


# ── RTC Download Application ───────────────────────────────────────

def rtc_download_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'rtc_download.html', {'retailer': retailer})


def rtc_download_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    district = request.POST.get('district', '').strip().upper()
    assembly = request.POST.get('assembly', '').strip().upper()
    hobli = request.POST.get('hobli', '').strip().upper()
    village = request.POST.get('village', '').strip().upper()
    survey = request.POST.get('survey', '').strip().upper()

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not district or district == 'SELECT...':
        return JsonResponse({'success': False, 'error': 'District is required.'})

    if not assembly or len(assembly) < 2:
        return JsonResponse({'success': False, 'error': 'Talluk is required.'})

    cost = Decimal('10.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = RTCDownloadApplication.objects.create(
            retailer=retailer,
            applicant_name=applicant_name,
            district=district,
            talluk=assembly,
            hobli=hobli,
            village=village,
            survey_no=survey,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'RTC Download Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'RTC / Pahani Download Application submitted successfully!', 'order_id': app_obj.order_id})


def rtc_download_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = RTCDownloadApplication.objects.filter(retailer=retailer)
    return render(request, 'rtc_download_list.html', {'retailer': retailer, 'applications': applications})


def rtc_download_pdf(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(RTCDownloadApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'rtc_download_list.html', {'retailer': retailer, 'error': 'RTC Document is not ready yet.'})


# ── Ayushman Bharat Health Card (ABHA Card) Application ───────────

def abha_card_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'abha_card.html', {'retailer': retailer})


def abha_card_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    aadhaarno = request.POST.get('aadhaarno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()
    state = request.POST.get('state', '').strip().title()

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not state or state == 'Select...':
        return JsonResponse({'success': False, 'error': 'State is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = AbhaCardApplication.objects.create(
            retailer=retailer,
            aadhaar_number=aadhaarno,
            applicant_name=applicant_name,
            mobile=mobile,
            state=state,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'ABHA Card Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Ayushman Bharat Health Card Application submitted successfully!', 'order_id': app_obj.order_id})


def abha_card_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = AbhaCardApplication.objects.filter(retailer=retailer)
    return render(request, 'abha_card_list.html', {'retailer': retailer, 'applications': applications})


def abha_card_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(AbhaCardApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'abha_card_list.html', {'retailer': retailer, 'error': 'ABHA Card Document is not ready yet.'})


# ── Ayushman Bharat Health Card (₹100 Insurance Scheme) Application ─

def ayush_card_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'ayush_card.html', {'retailer': retailer})


def ayush_card_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    aadhaarno = request.POST.get('aadhaarno', '').strip()
    mobile = request.POST.get('mobile', '').strip()
    relationship = request.POST.get('relationship', '').strip()
    dob = request.POST.get('dob', '').strip()
    state = request.POST.get('state', '').strip().title()
    district = request.POST.get('district', '').strip().upper()
    assembly = request.POST.get('assembly', '').strip().upper()
    photo_file = request.FILES.get('photo_file')

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not relationship or relationship == 'Select...':
        return JsonResponse({'success': False, 'error': 'Relationship with Family Head is required.'})

    if not dob:
        return JsonResponse({'success': False, 'error': 'Date of Birth is required.'})

    if not photo_file:
        return JsonResponse({'success': False, 'error': 'Live Photo is required.'})

    if not state or state == 'Select...':
        return JsonResponse({'success': False, 'error': 'State is required.'})

    if not district:
        return JsonResponse({'success': False, 'error': 'District is required.'})

    if not assembly:
        return JsonResponse({'success': False, 'error': 'Sub Division is required.'})

    cost = Decimal('100.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = AyushCardApplication.objects.create(
            retailer=retailer,
            applicant_name=applicant_name,
            aadhaar_number=aadhaarno,
            mobile=mobile,
            relationship=relationship,
            dob=dob,
            photo_file=photo_file,
            state=state,
            district=district,
            sub_division=assembly,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Ayushman Card Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Ayushman Bharat Health Card Application submitted successfully!', 'order_id': app_obj.order_id})


def ayush_card_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = AyushCardApplication.objects.filter(retailer=retailer)
    return render(request, 'ayush_card_list.html', {'retailer': retailer, 'applications': applications})


def ayush_card_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(AyushCardApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'ayush_card_list.html', {'retailer': retailer, 'error': 'Ayushman Card Document is not ready yet.'})


# ── Ayushman Card Download Only Service Application ───────────────

def ayush_dwnld_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'ayush_dwnld.html', {'retailer': retailer})


def ayush_dwnld_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    aadhaarno = request.POST.get('aadhaarno', '').strip()
    mobile = request.POST.get('mobile', '').strip()
    dob = request.POST.get('dob', '').strip()
    state = request.POST.get('state', '').strip().title()
    district = request.POST.get('district', '').strip().upper()

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not aadhaarno or len(aadhaarno) != 12 or not aadhaarno.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not dob:
        return JsonResponse({'success': False, 'error': 'Date of Birth is required.'})

    if not state or state == 'Select...':
        return JsonResponse({'success': False, 'error': 'State is required.'})

    if not district or len(district) < 2:
        return JsonResponse({'success': False, 'error': 'District is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = AyushDownloadApplication.objects.create(
            retailer=retailer,
            applicant_name=applicant_name,
            aadhaar_number=aadhaarno,
            mobile=mobile,
            dob=dob,
            state=state,
            district=district,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Ayushman Card Download Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Ayushman Smart Card Download Application submitted successfully!', 'order_id': app_obj.order_id})


def ayush_dwnld_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = AyushDownloadApplication.objects.filter(retailer=retailer)
    return render(request, 'ayush_dwnld_list.html', {'retailer': retailer, 'applications': applications})


def ayush_dwnld_pdf(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(AyushDownloadApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'ayush_dwnld_list.html', {'retailer': retailer, 'error': 'Ayushman Smart Card Document is not ready yet.'})


# ── e-Shram Card Registration Application ─────────────────────────

def eshram_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'eshram.html', {'retailer': retailer})


def eshram_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    aadhaar_no = request.POST.get('aadhaar_no', '').strip()
    mobile_no = request.POST.get('mobile_no', '').strip()
    marital_status = request.POST.get('marital_status', '').strip()
    relationship = request.POST.get('relationship', '').strip()
    father_name = request.POST.get('father_name', '').strip().upper()
    social_category = request.POST.get('social_category', '').strip()
    differently_abled = request.POST.get('differently_abled', 'no').strip()
    state = request.POST.get('state', '').strip().title()
    district = request.POST.get('district', '').strip().upper()
    assembly = request.POST.get('assembly', '').strip().upper()
    address_line1 = request.POST.get('address_line1', '').strip().upper()
    address_line2 = request.POST.get('address_line2', '').strip().upper()
    pincode = request.POST.get('pincode', '').strip()
    staying_from = request.POST.get('staying_from', '').strip()
    education = request.POST.get('education', '').strip()
    monthly_income = request.POST.get('monthly_income', '').strip()
    online_working = request.POST.get('online_working', 'no').strip()
    primary_occupation = request.POST.get('primary_occupation', '').strip().upper()
    work_exp = request.POST.get('work_exp', '').strip()
    acc_number = request.POST.get('acc_number', '').strip().upper()
    ifsc_code = request.POST.get('ifsc_code', '').strip().upper()

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not aadhaar_no or len(aadhaar_no) != 12 or not aadhaar_no.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not mobile_no or len(mobile_no) != 10 or not mobile_no.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not marital_status or marital_status == 'Select...':
        return JsonResponse({'success': False, 'error': 'Marital Status is required.'})

    if not relationship or relationship == 'Select...':
        return JsonResponse({'success': False, 'error': 'Relationship is required.'})

    if not father_name or len(father_name) < 2:
        return JsonResponse({'success': False, 'error': 'Relative Name is required.'})

    if not social_category or social_category == 'Select...':
        return JsonResponse({'success': False, 'error': 'Social Category is required.'})

    if not state or state == 'Select...':
        return JsonResponse({'success': False, 'error': 'State is required.'})

    if not district:
        return JsonResponse({'success': False, 'error': 'District is required.'})

    if not assembly:
        return JsonResponse({'success': False, 'error': 'Sub Division is required.'})

    if not address_line1 or len(address_line1) < 5:
        return JsonResponse({'success': False, 'error': 'Address Line 1 is required.'})

    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 6-digit Pincode is required.'})

    if not primary_occupation:
        return JsonResponse({'success': False, 'error': 'Primary Occupation is required.'})

    if not acc_number or len(acc_number) < 5:
        return JsonResponse({'success': False, 'error': 'Bank Account Number is required.'})

    if not ifsc_code or len(ifsc_code) < 11:
        return JsonResponse({'success': False, 'error': 'Valid IFSC Code is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = EShramApplication.objects.create(
            retailer=retailer,
            applicant_name=applicant_name,
            aadhaar_number=aadhaar_no,
            mobile=mobile_no,
            marital_status=marital_status,
            relationship=relationship,
            relative_name=father_name,
            social_category=social_category,
            differently_abled=differently_abled,
            state=state,
            district=district,
            sub_division=assembly,
            address_line1=address_line1,
            address_line2=address_line2,
            pincode=pincode,
            staying_from=staying_from,
            education=education,
            monthly_income=monthly_income,
            online_working=online_working,
            primary_occupation=primary_occupation,
            work_exp=work_exp,
            account_number=acc_number,
            ifsc_code=ifsc_code,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'e-Shram Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'e-Shram Registration Application submitted successfully!', 'order_id': app_obj.order_id})


def eshram_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = EShramApplication.objects.filter(retailer=retailer)
    return render(request, 'eshram_list.html', {'retailer': retailer, 'applications': applications})


def eshram_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(EShramApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'eshram_list.html', {'retailer': retailer, 'error': 'e-Shram Card Document is not ready yet.'})


# ── e-Shram Card Download Only Application ─────────────────────────

def eshram_dwnld_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'eshram_dwnld.html', {'retailer': retailer})


def eshram_dwnld_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    aadhaar_no = request.POST.get('aadhaarno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()
    state = request.POST.get('state', '').strip().title()

    if not aadhaar_no or len(aadhaar_no) != 12 or not aadhaar_no.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not state or state == 'Select...':
        return JsonResponse({'success': False, 'error': 'State is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = EShramDownloadApplication.objects.create(
            retailer=retailer,
            applicant_name=applicant_name,
            aadhaar_number=aadhaar_no,
            mobile=mobile,
            state=state,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'e-Shram Download Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'e-Shram Download Application submitted successfully!', 'order_id': app_obj.order_id})


def eshram_dwnld_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = EShramDownloadApplication.objects.filter(retailer=retailer)
    return render(request, 'eshram_dwnld_list.html', {'retailer': retailer, 'applications': applications})


def eshram_dwnld_pdf(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(EShramDownloadApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'eshram_dwnld_list.html', {'retailer': retailer, 'error': 'e-Shram Smart Card Document is not ready yet.'})


# ── PM Kisan Services Application ─────────────────────────────────

def pmkisan_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'pmkisan.html', {'retailer': retailer})


def pmkisan_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    appl_type = request.POST.get('appl_type', 'e-KYC').strip()
    aadhaar_no = request.POST.get('aadhaarno', '').strip()
    applicant_name = request.POST.get('applicant_name', '').strip().upper()
    mobile = request.POST.get('mobile', '').strip()
    state = request.POST.get('state', '').strip().title()

    if not aadhaar_no or len(aadhaar_no) != 12 or not aadhaar_no.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not state or state == 'Select...':
        return JsonResponse({'success': False, 'error': 'State is required.'})

    cost = Decimal('30.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = PMKisanApplication.objects.create(
            retailer=retailer,
            application_type=appl_type,
            applicant_name=applicant_name,
            aadhaar_number=aadhaar_no,
            mobile=mobile,
            state=state,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'PM Kisan Application ({appl_type}) — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'PM Kisan Application submitted successfully!', 'order_id': app_obj.order_id})


def pmkisan_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = PMKisanApplication.objects.filter(retailer=retailer)
    return render(request, 'pmkisan_list.html', {'retailer': retailer, 'applications': applications})


def pmkisan_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(PMKisanApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'pmkisan_list.html', {'retailer': retailer, 'error': 'PM Kisan Document is not ready yet.'})


# ── Naada Kacheri Certificate Download Application ───────────────

def naadakacheri_dwnld_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'naadakacheri_dwnld.html', {'retailer': retailer})


def naadakacheri_dwnld_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    rd_number = request.POST.get('rdnumber', '').strip().upper()
    applicant_name = request.POST.get('aadhaarname', '').strip().upper()
    certificate_type = request.POST.get('certificate', '').strip()

    if not rd_number or not re.match(r'^[A-Z0-9]+$', rd_number):
        return JsonResponse({'success': False, 'error': 'Valid Alphanumeric RD Number is required.'})

    if not applicant_name or len(applicant_name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not certificate_type or certificate_type == 'Select Certificate Type':
        return JsonResponse({'success': False, 'error': 'Certificate Type is required.'})

    cert_labels = {
        'caste': 'Caste Certificate',
        'income': 'Income Certificate',
        'obc': 'OBC Certificate',
        'widow': 'Widow/Not Remarried Certificate',
        'birth_death': 'Birth/Death Certificate',
        'residence': 'Residence/Domicile Certificate',
        'non_tenancy': 'Non-Tenancy Certificate',
        'agricultural_services': 'Agricultural Services Certificate',
        'physically_challenged': 'Physically Challenged Certificate',
        'population': 'Population Certificate'
    }
    display_cert_type = cert_labels.get(certificate_type, certificate_type.replace('_', ' ').title())

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = NaadaKacheriDownloadApplication.objects.create(
            retailer=retailer,
            rd_number=rd_number,
            applicant_name=applicant_name,
            certificate_type=display_cert_type,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Naada Kacheri Certificate Download ({display_cert_type}) — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Naada Kacheri Certificate Download Application submitted successfully!', 'order_id': app_obj.order_id})


def naadakacheri_dwnld_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = NaadaKacheriDownloadApplication.objects.filter(retailer=retailer)
    return render(request, 'naadakacheri_dwnld_list.html', {'retailer': retailer, 'applications': applications})


def naadakacheri_dwnld_pdf(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(NaadaKacheriDownloadApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'naadakacheri_dwnld_list.html', {'retailer': retailer, 'error': 'Naada Kacheri Certificate Document is not ready yet.'})


# ── Yuva Nidhi Scheme Application ─────────────────────────────────

def yuvanidhi_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'yuvanidhi.html', {'retailer': retailer})


def yuvanidhi_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    name = request.POST.get('name', '').strip().upper()
    aadhaar_no = request.POST.get('aadhaarno', '').strip()
    mobile = request.POST.get('mobile', '').strip()
    email = request.POST.get('email', '').strip().lower()
    district = request.POST.get('district', '').strip().title()
    talluk = request.POST.get('talluk', '').strip().title()
    education = request.POST.get('education', '').strip()
    certificateno = request.POST.get('certificateno', '').strip().upper()
    university = request.POST.get('university', '').strip().title()
    college = request.POST.get('college', '').strip().title()
    rationno = request.POST.get('rationno', '').strip()
    caste = request.POST.get('cast', '').strip()
    disability = request.POST.get('disability', 'no').strip()

    markscard1 = request.FILES.get('markscard1')
    markscard2 = request.FILES.get('markscard2')
    markscard3 = request.FILES.get('markscard3')

    if not name or len(name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not aadhaar_no or len(aadhaar_no) != 12 or not aadhaar_no.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 12-digit Aadhaar Number is required.'})

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number is required.'})

    if not email or '@' not in email:
        return JsonResponse({'success': False, 'error': 'Valid Email ID is required.'})

    if not district or not talluk:
        return JsonResponse({'success': False, 'error': 'District and Talluk are required.'})

    if not education:
        return JsonResponse({'success': False, 'error': 'Education Selection is required.'})

    if not certificateno or not university or not college:
        return JsonResponse({'success': False, 'error': 'Certificate No., University Name, and College Name are required.'})

    if not caste:
        return JsonResponse({'success': False, 'error': 'Caste is required.'})

    if not markscard1 or not markscard3:
        return JsonResponse({'success': False, 'error': '10th Marks Card and Degree/Diploma Marks Card are required.'})

    cost = Decimal('30.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = YuvaNidhiApplication.objects.create(
            retailer=retailer,
            applicant_name=name,
            aadhaar_number=aadhaar_no,
            mobile=mobile,
            email=email,
            district=district,
            talluk=talluk,
            education=education,
            certificate_no=certificateno,
            university=university,
            college=college,
            ration_card_no=rationno,
            caste=caste,
            disability=disability,
            markscard_10th=markscard1,
            markscard_puc=markscard2,
            markscard_degree=markscard3,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'Yuva Nidhi Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'Yuva Nidhi Application submitted successfully!', 'order_id': app_obj.order_id})


def yuvanidhi_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = YuvaNidhiApplication.objects.filter(retailer=retailer)
    return render(request, 'yuvanidhi_list.html', {'retailer': retailer, 'applications': applications})


def yuvanidhi_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(YuvaNidhiApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'yuvanidhi_list.html', {'retailer': retailer, 'error': 'Yuva Nidhi Document is not ready yet.'})


# ── SSP Password Change Application ───────────────────────────────

def ssp_password_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'ssp_password_change.html', {'retailer': retailer})


def ssp_password_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    ssp_id = request.POST.get('ssp_id', '').strip()
    new_password = request.POST.get('new_password', '').strip()
    confirm_password = request.POST.get('confirm_password', '').strip()

    if not ssp_id or len(ssp_id) < 3:
        return JsonResponse({'success': False, 'error': 'Valid SSP ID (min 3 characters) is required.'})

    if not new_password or len(new_password) < 6:
        return JsonResponse({'success': False, 'error': 'New Password must be at least 6 characters long.'})

    if new_password != confirm_password:
        return JsonResponse({'success': False, 'error': 'New Password and Confirm Password do not match.'})

    cost = Decimal('30.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = SSPPasswordChangeApplication.objects.create(
            retailer=retailer,
            ssp_id=ssp_id,
            new_password=new_password,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'SSP Password Change — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'SSP Password Change request submitted successfully!', 'order_id': app_obj.order_id})


def ssp_password_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = SSPPasswordChangeApplication.objects.filter(retailer=retailer)
    return render(request, 'ssp_password_change_list.html', {'retailer': retailer, 'applications': applications})


def ssp_password_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(SSPPasswordChangeApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'ssp_password_change_list.html', {'retailer': retailer, 'error': 'SSP Password Confirmation Document is not ready yet.'})


# ── SSP Mobile Link Application ───────────────────────────────────

def ssp_mobile_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'ssp_mobile_link.html', {'retailer': retailer})


def ssp_mobile_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    name = request.POST.get('name', '').strip().upper()
    new_mobile = request.POST.get('new_mobile', '').strip()
    ssp_id = request.POST.get('ssp_id', '').strip()

    if not name or len(name) < 2:
        return JsonResponse({'success': False, 'error': 'Applicant Name is required.'})

    if not new_mobile or len(new_mobile) != 10 or not re.match(r'^[6-9]\d{9}$', new_mobile):
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number starting with 6-9 is required.'})

    if not ssp_id or len(ssp_id) < 3:
        return JsonResponse({'success': False, 'error': 'Valid SSP ID (min 3 characters) is required.'})

    cost = Decimal('50.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    with transaction.atomic():
        retailer.wallet_balance -= cost
        retailer.save()

        app_obj = SSPMobileLinkApplication.objects.create(
            retailer=retailer,
            applicant_name=name,
            new_mobile=new_mobile,
            ssp_id=ssp_id,
            amount=cost,
            status='PENDING'
        )

        WalletTransaction.objects.create(
            retailer=retailer,
            amount=cost,
            tx_type='debit',
            status='completed',
            note=f'SSP Mobile Link Application — Order ID: {app_obj.order_id}'
        )

    return JsonResponse({'success': True, 'message': 'SSP Mobile Link request submitted successfully!', 'order_id': app_obj.order_id})


def ssp_mobile_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = SSPMobileLinkApplication.objects.filter(retailer=retailer)
    return render(request, 'ssp_mobile_link_list.html', {'retailer': retailer, 'applications': applications})


def ssp_mobile_download(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    app_obj = get_object_or_404(SSPMobileLinkApplication, order_id=order_id, retailer=retailer)
    if app_obj.output_pdf:
        return redirect(app_obj.output_pdf.url)
    return render(request, 'ssp_mobile_link_list.html', {'retailer': retailer, 'error': 'SSP Mobile Link Confirmation Document is not ready yet.'})


# ── Mobile to PAN Find Application (Surepass API) ─────────────────

def mobile_to_pan_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'mobile_to_pan.html', {'retailer': retailer})


def mobile_to_pan_submit(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expired. Please log in again.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    name = request.POST.get('name', '').strip()
    mobile_no = request.POST.get('mobile_no', '').strip()

    if not name or len(name) < 2:
        return JsonResponse({'success': False, 'error': 'Full Name (as registered with PAN) is required.'})

    if not mobile_no or len(mobile_no) != 10 or not re.match(r'^[6-9]\d{9}$', mobile_no):
        return JsonResponse({'success': False, 'error': 'Valid 10-digit Mobile Number starting with 6-9 is required.'})

    cost = Decimal('15.00')
    if retailer.wallet_balance < cost:
        return JsonResponse({'success': False, 'error': f'Insufficient Wallet Balance! Requires ₹{cost}, your balance is ₹{retailer.wallet_balance}. Please recharge.'})

    surepass_token = getattr(settings, 'SUREPASS_TOKEN', '').strip()
    if not surepass_token:
        return JsonResponse({'success': False, 'error': 'Surepass API token is not configured.'}, status=500)

    # Surepass API Endpoint
    api_url = "https://kyc-api.surepass.io/api/v1/pan/mobile-to-pan"
    headers = {
        "Authorization": f"Bearer {surepass_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": name,
        "mobile_no": mobile_no
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        res_data = response.json()
        logger.info(f"Mobile to PAN API Response for {mobile_no}: {res_data}")

        is_success = res_data.get('success', False)
        status_code = res_data.get('status_code', 400)

        if is_success and status_code == 200:
            data_obj = res_data.get('data', {})
            pan_number = data_obj.get('pan_number', '').strip()
            client_id = data_obj.get('client_id', '')
            matched_name = data_obj.get('name', name)

            if not pan_number:
                return JsonResponse({'success': False, 'error': 'PAN Number not found in API response.'})

            with transaction.atomic():
                retailer.wallet_balance -= cost
                retailer.save()

                app_obj = MobileToPanApplication.objects.create(
                    retailer=retailer,
                    applicant_name=matched_name or name,
                    mobile_no=mobile_no,
                    pan_number=pan_number,
                    client_id=client_id,
                    response_message=res_data.get('message', 'Success'),
                    amount=cost,
                    status='COMPLETED'
                )

                WalletTransaction.objects.create(
                    retailer=retailer,
                    amount=cost,
                    tx_type='debit',
                    status='completed',
                    note=f'Mobile to PAN Search — Order ID: {app_obj.order_id}'
                )

            return JsonResponse({
                'success': True,
                'message': 'PAN details retrieved successfully!',
                'pan_number': pan_number,
                'name': matched_name,
                'mobile_no': mobile_no,
                'order_id': app_obj.order_id
            })

        else:
            msg = res_data.get('message', 'Verification Failed. PAN details could not be retrieved.')
            MobileToPanApplication.objects.create(
                retailer=retailer,
                applicant_name=name,
                mobile_no=mobile_no,
                response_message=msg,
                amount=cost,
                status='FAILED'
            )
            return JsonResponse({'success': False, 'error': msg})

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Surepass API Request Error: {req_err}")
        return JsonResponse({'success': False, 'error': 'API Gateway timeout or connection error. Please try again.'})
    except Exception as e:
        logger.error(f"Unexpected error in mobile_to_pan_submit: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def mobile_to_pan_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    applications = MobileToPanApplication.objects.filter(retailer=retailer)
    return render(request, 'mobile_to_pan_list.html', {'retailer': retailer, 'applications': applications})




































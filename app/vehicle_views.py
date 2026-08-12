import json
import uuid
import requests
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction


def _get_retailer_from_session(request):
    from app.models import Retailer
    retailer_id = request.session.get('retailer_id')
    if not retailer_id:
        return None
    try:
        return Retailer.objects.get(retailer_id=retailer_id)
    except Retailer.DoesNotExist:
        return None


def vehicle_rc_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    return render(request, 'vehicle_rc.html', {'retailer': retailer})


def vehicle_rc_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expire. Login karo.'}, status=401)

    try:
        body = json.loads(request.body)
        vehicle_number = body.get('vehicle_number', '').strip().upper()

        if not vehicle_number:
            return JsonResponse({'success': False, 'error': 'Vehicle number required'})

        # Wallet check
        RC_CHARGE = Decimal('25.00')
        current_balance = retailer.wallet_balance or Decimal('0')
        if current_balance < RC_CHARGE:
            shortage = RC_CHARGE - current_balance
            return JsonResponse({
                'success': False,
                'error': f'Wallet balance kam hai. Rs.25 chahiye, aapke paas sirf Rs.{current_balance} hain. Rs.{shortage} add karein.'
            })

        order_id = f"RCADV{uuid.uuid4().hex[:16].upper()}"

        from app.models import RCAdvanceApplication, WalletTransaction
        rc_app = RCAdvanceApplication.objects.create(
            retailer=retailer,
            order_id=order_id,
            vehicle_number=vehicle_number,
            amount=RC_CHARGE,
            status='pending',
        )

        # DUMMY MODE
        if vehicle_number.startswith('TEST'):
            result = {
                'success': True,
                'data': {
                    'registration_number':     vehicle_number,
                    'owner_name':              'Ramesh Kumar Sharma',
                    'father_name':             'Suresh Kumar Sharma',
                    'permanent_address':       '123, MG Road, Bangalore, Karnataka - 560001',
                    'vehicle_class':           'LMV-NT',
                    'maker_description':       'MARUTI SUZUKI',
                    'model':                   'SWIFT VXI',
                    'fuel_type':               'PETROL',
                    'color':                   'WHITE',
                    'engine_number':           'K12MN1234567',
                    'chassis_number':          'MA3EWDE1S00123456',
                    'registration_date':       '2020-03-15',
                    'registration_valid_upto': '2035-03-14',
                    'fitness_upto':            '2035-03-14',
                    'insurance_upto':          '2026-03-14',
                    'financer':                'HDFC BANK LTD',
                    'office_name':             'RTO Bangalore East (KA-23)',
                }
            }
        else:
            SUREPASS_TOKEN = getattr(settings, 'SUREPASS_TOKEN', '')
            if not SUREPASS_TOKEN:
                rc_app.status = 'failed'
                rc_app.save()
                return JsonResponse({'success': False, 'error': 'SurePass token configure nahi hai.'})

            resp = requests.post(
                'https://kyc-api.surepass.app/api/v1/rc/rc-full',
                headers={
                    'Authorization': f'Bearer {SUREPASS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                json={'id_number': vehicle_number},
                timeout=20
            )
            result = resp.json()

        if result.get('success') and result.get('data'):
            d = result['data']
            rc = {
                'reg_no':         d.get('registration_number', ''),
                'owner_name':     d.get('owner_name', ''),
                'father_name':    d.get('father_name', ''),
                'address':        d.get('permanent_address', ''),
                'vehicle_class':  d.get('vehicle_class', ''),
                'maker_model':    f"{d.get('maker_description','')} / {d.get('model','')}",
                'fuel_type':      d.get('fuel_type', ''),
                'colour':         d.get('color', ''),
                'engine_no':      d.get('engine_number', ''),
                'chassis_no':     d.get('chassis_number', ''),
                'reg_date':       d.get('registration_date', ''),
                'validity':       d.get('registration_valid_upto', ''),
                'fitness_upto':   d.get('fitness_upto', ''),
                'insurance_upto': d.get('insurance_upto', ''),
                'financer':       d.get('financer', ''),
                'rto':            d.get('office_name', ''),
            }

            with transaction.atomic():
                rc_app.owner_name    = rc['owner_name']
                rc_app.vehicle_class = rc['vehicle_class']
                rc_app.maker_model   = rc['maker_model']
                rc_app.fuel_type     = rc['fuel_type']
                rc_app.rc_data       = rc
                rc_app.status        = 'success'
                rc_app.save()

                retailer.wallet_balance = current_balance - RC_CHARGE
                retailer.save(update_fields=['wallet_balance'])

                WalletTransaction.objects.create(
                    retailer=retailer,
                    amount=RC_CHARGE,
                    tx_type='debit',
                    status='completed',
                    payment_provider='internal',
                    note=f'RC Advance � {vehicle_number} � {order_id}',
                )

            return JsonResponse({
                'success': True,
                'rc': rc,
                'order_id': order_id,
                'wallet_balance': str(retailer.wallet_balance)
            })

        else:
            err = result.get('message', 'RC nahi mili')
            rc_app.status = 'failed'
            rc_app.save()
            return JsonResponse({'success': False, 'error': err})

    except requests.Timeout:
        return JsonResponse({'success': False, 'error': 'API timeout. Dobara try karo.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def vehicle_rc_list(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from app.models import RCAdvanceApplication
    applications = RCAdvanceApplication.objects.filter(retailer=retailer).order_by('-id')
    return render(request, 'vehicle_rc_list.html', {'retailer': retailer, 'applications': applications})


# -------------------------------------------------------
# Vehicle RC All India PVC
# -------------------------------------------------------

def vehicle_rc_allindia_page(request):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from app.models import RCAdvanceApplication
    history = RCAdvanceApplication.objects.filter(
        retailer=retailer, service_type='allindia'
    ).order_by('-id')
    return render(request, 'vehicle_rc_allindia.html', {
        'retailer': retailer,
        'history': history,
    })


def vehicle_rc_allindia_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return JsonResponse({'success': False, 'error': 'Session expire. Login karo.'}, status=401)

    try:
        body = json.loads(request.body)
        vehicle_number   = body.get('vehicle_number', '').strip().upper()
        card_background  = body.get('card_background', 'New Background')
        chip_type        = body.get('chip_type', 'Chip')

        if not vehicle_number:
            return JsonResponse({'success': False, 'error': 'Vehicle number required'})

        RC_CHARGE = Decimal('25.00')
        current_balance = retailer.wallet_balance or Decimal('0')
        if current_balance < RC_CHARGE:
            return JsonResponse({
                'success': False,
                'error': f'Wallet balance kam hai. Rs.25 chahiye, aapke paas sirf Rs.{current_balance} hain.'
            })

        order_id = f"RCAI{uuid.uuid4().hex[:16].upper()}"

        from app.models import RCAdvanceApplication, WalletTransaction
        rc_app = RCAdvanceApplication.objects.create(
            retailer=retailer,
            order_id=order_id,
            vehicle_number=vehicle_number,
            amount=RC_CHARGE,
            status='pending',
            service_type='allindia',
        )

        # DUMMY MODE
        if vehicle_number.startswith('TEST'):
            result = {
                'success': True,
                'data': {
                    'registration_number':     vehicle_number,
                    'owner_name':              'KHANU BORGUNDE',
                    'father_name':             'RAMA BORGUNDE',
                    'permanent_address':       'Belgaum, 591219',
                    'vehicle_class':           'M-Cycle/Scooter(2WN)',
                    'maker_description':       'HERO MOTOCORP LTD',
                    'model':                   'SPLENDOR+ BLACK AND ACCENTSS',
                    'fuel_type':               'PETROL',
                    'color':                   'BLACK AND ACCENT',
                    'body_type':               'SOLO WITH PILLION',
                    'engine_number':           'HA11EDN4C30572',
                    'chassis_number':          'MBLHAW129N4C31808',
                    'registration_date':       '25/07/2022',
                    'registration_valid_upto': '24/07/2037',
                    'fitness_upto':            '24/07/2037',
                    'insurance_upto':          '24/07/2026',
                    'financer':                'BERAR FINANCE LTD',
                    'office_name':             'CHIKKODI RTO, Karnataka',
                    'seating_capacity':        '2',
                    'unladen_weight':          '242',
                    'cubic_capacity':          '97',
                    'no_of_cylinders':         '1',
                    'wheel_base':              '1236',
                    'mfg_month_year':          '03/2022',
                    'emission_norms':          'BHARAT STAGE VI',
                    'owner_serial':            '1',
                    'norms_type':              'NT',
                    'state_code':              'KA',
                }
            }
        else:
            SUREPASS_TOKEN = getattr(settings, 'SUREPASS_TOKEN', '')
            if not SUREPASS_TOKEN:
                rc_app.status = 'failed'
                rc_app.save()
                return JsonResponse({'success': False, 'error': 'SurePass token configure nahi hai.'})
            resp = requests.post(
                'https://kyc-api.surepass.app/api/v1/rc/rc-full',
                headers={'Authorization': f'Bearer {SUREPASS_TOKEN}', 'Content-Type': 'application/json'},
                json={'id_number': vehicle_number},
                timeout=20
            )
            result = resp.json()

        if result.get('success') and result.get('data'):
            d = result['data']
            rc = {
                'reg_no':          d.get('registration_number', ''),
                'owner_name':      d.get('owner_name', ''),
                'father_name':     d.get('father_name', ''),
                'address':         d.get('permanent_address', ''),
                'vehicle_class':   d.get('vehicle_class', ''),
                'maker':           d.get('maker_description', ''),
                'model':           d.get('model', ''),
                'fuel_type':       d.get('fuel_type', ''),
                'colour':          d.get('color', ''),
                'body_type':       d.get('body_type', ''),
                'engine_no':       d.get('engine_number', ''),
                'chassis_no':      d.get('chassis_number', ''),
                'reg_date':        d.get('registration_date', ''),
                'validity':        d.get('registration_valid_upto', ''),
                'fitness_upto':    d.get('fitness_upto', ''),
                'insurance_upto':  d.get('insurance_upto', ''),
                'financer':        d.get('financer', ''),
                'rto':             d.get('office_name', ''),
                'seating':         d.get('seating_capacity', ''),
                'unladen_weight':  d.get('unladen_weight', ''),
                'cubic_cap':       d.get('cubic_capacity', ''),
                'cylinders':       d.get('no_of_cylinders', ''),
                'wheel_base':      d.get('wheel_base', ''),
                'mfg_date':        d.get('mfg_month_year', ''),
                'emission':        d.get('emission_norms', ''),
                'owner_serial':    d.get('owner_serial', '1'),
                'norms_type':      d.get('norms_type', 'NT'),
                'state_code':      d.get('state_code', 'KA'),
                'card_background': card_background,
                'chip_type':       chip_type,
            }

            with transaction.atomic():
                rc_app.owner_name    = rc['owner_name']
                rc_app.vehicle_class = rc['vehicle_class']
                rc_app.maker_model   = f"{rc['maker']} / {rc['model']}"
                rc_app.fuel_type     = rc['fuel_type']
                rc_app.rc_data       = rc
                rc_app.status        = 'success'
                rc_app.save()

                retailer.wallet_balance = current_balance - RC_CHARGE
                retailer.save(update_fields=['wallet_balance'])

                WalletTransaction.objects.create(
                    retailer=retailer,
                    amount=RC_CHARGE,
                    tx_type='debit',
                    status='completed',
                    payment_provider='internal',
                    note=f'RC All India PVC � {vehicle_number} � {order_id}',
                )

            return JsonResponse({
                'success': True,
                'rc': rc,
                'order_id': order_id,
                'wallet_balance': str(retailer.wallet_balance)
            })
        else:
            rc_app.status = 'failed'
            rc_app.save()
            return JsonResponse({'success': False, 'error': result.get('message', 'RC nahi mili')})

    except requests.Timeout:
        return JsonResponse({'success': False, 'error': 'API timeout.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def vehicle_rc_allindia_pdf(request, order_id):
    retailer = _get_retailer_from_session(request)
    if retailer is None:
        return redirect('retailer_login')
    from app.models import RCAdvanceApplication
    try:
        rc_app = RCAdvanceApplication.objects.get(order_id=order_id, retailer=retailer)
    except RCAdvanceApplication.DoesNotExist:
        from django.http import HttpResponse
        return HttpResponse('Not found', status=404)
    return render(request, 'vehicle_rc_pvc_pdf.html', {
        'rc': rc_app.rc_data,
        'order_id': order_id,
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from .models import Retailer, TailoringCertificateApplication, BasicComputerCertificateApplication, UdyamRegistrationApplication, PVCMakerApplication, CibilScoreApplication, WalletTransaction, PANApplication, AadhaarPdfApplication, EidToUidApplication, LMSCertificateApplication, PanToAadhaarApplication

logger = logging.getLogger(__name__)


def _check_admin(request):
    return request.session.get('is_admin') is True


def admin_login(request):
    if _check_admin(request):
        return redirect('admin_dashboard')

    context = {}
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Default admin login check (user: admin / pass: admin123)
        if username == 'admin' and password == 'admin123':
            request.session['is_admin'] = True
            request.session['admin_user'] = username
            return redirect('admin_dashboard')
        else:
            context['error'] = 'Invalid Admin credentials.'

    return render(request, 'admin_login.html', context)


def admin_logout(request):
    request.session.pop('is_admin', None)
    request.session.pop('admin_user', None)
    return redirect('admin_login')


def admin_dashboard(request):
    if not _check_admin(request):
        return redirect('admin_login')

    total_retailers = Retailer.objects.count()

    tailoring_pending = TailoringCertificateApplication.objects.filter(status='PENDING').count()
    computer_pending = BasicComputerCertificateApplication.objects.filter(status='PENDING').count()
    udyam_pending = UdyamRegistrationApplication.objects.filter(status='PENDING').count()
    pvc_pending = PVCMakerApplication.objects.filter(status='PENDING').count()
    total_pending = tailoring_pending + computer_pending + udyam_pending + pvc_pending

    tailoring_completed = TailoringCertificateApplication.objects.filter(status='COMPLETED').count()
    computer_completed = BasicComputerCertificateApplication.objects.filter(status='COMPLETED').count()
    udyam_completed = UdyamRegistrationApplication.objects.filter(status='COMPLETED').count()
    pvc_completed = PVCMakerApplication.objects.filter(status='COMPLETED').count()
    total_completed = tailoring_completed + computer_completed + udyam_completed + pvc_completed

    tailoring_rejected = TailoringCertificateApplication.objects.filter(status='REJECTED').count()
    computer_rejected = BasicComputerCertificateApplication.objects.filter(status='REJECTED').count()
    udyam_rejected = UdyamRegistrationApplication.objects.filter(status='REJECTED').count()
    pvc_rejected = PVCMakerApplication.objects.filter(status='REJECTED').count()
    total_rejected = tailoring_rejected + computer_rejected + udyam_rejected + pvc_rejected

    recent_tailoring = list(TailoringCertificateApplication.objects.all().order_by('-created_at')[:10])
    recent_computer = list(BasicComputerCertificateApplication.objects.all().order_by('-created_at')[:10])
    recent_udyam = list(UdyamRegistrationApplication.objects.all().order_by('-created_at')[:10])
    recent_pvc = list(PVCMakerApplication.objects.all().order_by('-created_at')[:10])

    recent_all = []
    for item in recent_tailoring:
        item.service_type = 'Tailoring'
        item.service_icon = '✂️'
        item.applicant_name = item.full_name
        item.mobile = item.mobile_number
        item.detail_url_name = 'admin_tailoring_detail'
        recent_all.append(item)

    for item in recent_computer:
        item.service_type = 'Basic Computer'
        item.service_icon = '💻'
        item.applicant_name = item.student_name
        item.mobile = item.mobile_no
        item.detail_url_name = 'admin_computer_detail'
        recent_all.append(item)

    for item in recent_udyam:
        item.service_type = 'Udyam Registration'
        item.service_icon = '🏭'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile_no
        item.detail_url_name = 'admin_udyam_detail'
        recent_all.append(item)

    for item in recent_pvc:
        item.service_type = 'PVC Card Maker'
        item.service_icon = '🪪'
        item.applicant_name = item.full_name
        item.mobile = item.customer_mobile
        item.detail_url_name = 'admin_pvc_detail'
        recent_all.append(item)

    recent_all.sort(key=lambda x: x.created_at, reverse=True)
    recent_all = recent_all[:10]

    return render(request, 'admin_dashboard.html', {
        'total_retailers': total_retailers,
        'tailoring_pending': tailoring_pending,
        'computer_pending': computer_pending,
        'udyam_pending': udyam_pending,
        'pvc_pending': pvc_pending,
        'total_pending': total_pending,
        'total_completed': total_completed,
        'total_rejected': total_rejected,
        'recent_applications': recent_all,
    })





def admin_tailoring_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip()

    apps = TailoringCertificateApplication.objects.all().order_by('-created_at')

    if status_filter:
        apps = apps.filter(status=status_filter)

    if search_q:
        apps = apps.filter(full_name__icontains=search_q) | apps.filter(order_id__icontains=search_q) | apps.filter(mobile_number__icontains=search_q)

    return render(request, 'admin_tailoring_list.html', {
        'applications': apps,
        'status_filter': status_filter,
        'search_q': search_q,
    })


def admin_tailoring_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(TailoringCertificateApplication, order_id=order_id)
    return render(request, 'admin_tailoring_detail.html', {'app': app_obj})


def admin_tailoring_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(TailoringCertificateApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        # Check if already refunded to prevent double refund
        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    # AUTOMATIC WALLET REFUND
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        payment_provider='internal',
                        note=f'Refund for Rejected Tailoring Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_computer_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip()

    apps = BasicComputerCertificateApplication.objects.all().order_by('-created_at')

    if status_filter:
        apps = apps.filter(status=status_filter)

    if search_q:
        apps = apps.filter(student_name__icontains=search_q) | apps.filter(order_id__icontains=search_q) | apps.filter(mobile_no__icontains=search_q)

    return render(request, 'admin_computer_list.html', {
        'applications': apps,
        'status_filter': status_filter,
        'search_q': search_q,
    })


def admin_computer_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(BasicComputerCertificateApplication, order_id=order_id)
    return render(request, 'admin_computer_detail.html', {'app': app_obj})


def admin_computer_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(BasicComputerCertificateApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'Basic Computer Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        payment_provider='internal',
                        note=f'Refund for Rejected Basic Computer Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_udyam_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip()

    apps = UdyamRegistrationApplication.objects.all().order_by('-created_at')

    if status_filter:
        apps = apps.filter(status=status_filter)

    if search_q:
        apps = apps.filter(applicant_name__icontains=search_q) | apps.filter(order_id__icontains=search_q) | apps.filter(mobile_no__icontains=search_q)

    return render(request, 'admin_udyam_list.html', {
        'applications': apps,
        'status_filter': status_filter,
        'search_q': search_q,
    })


def admin_udyam_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(UdyamRegistrationApplication, order_id=order_id)
    return render(request, 'admin_udyam_detail.html', {'app': app_obj})


def admin_udyam_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(UdyamRegistrationApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'Udyam Registration Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        payment_provider='internal',
                        note=f'Refund for Rejected Udyam Registration Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_pvc_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip()

    apps = PVCMakerApplication.objects.all().order_by('-created_at')

    if status_filter:
        apps = apps.filter(status=status_filter)

    if search_q:
        apps = apps.filter(full_name__icontains=search_q) | apps.filter(order_id__icontains=search_q) | apps.filter(customer_mobile__icontains=search_q)

    return render(request, 'admin_pvc_list.html', {
        'applications': apps,
        'status_filter': status_filter,
        'search_q': search_q,
    })


def admin_pvc_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(PVCMakerApplication, order_id=order_id)
    return render(request, 'admin_pvc_detail.html', {'app': app_obj})


def admin_pvc_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(PVCMakerApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'PVC Card Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        payment_provider='internal',
                        note=f'Refund for Rejected PVC Card Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_other_services(request):
    if not _check_admin(request):
        return redirect('admin_login')

    service_filter = request.GET.get('service', '').strip().lower()
    status_filter  = request.GET.get('status', '').strip().upper()
    search_q       = request.GET.get('q', '').strip().lower()

    combined_list = []

    # 1. Tailoring Applications
    if not service_filter or service_filter == 'tailoring':
        qs = TailoringCertificateApplication.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        for item in qs:
            if search_q and (search_q not in item.full_name.lower() and search_q not in item.order_id.lower() and search_q not in item.mobile_number.lower()):
                continue
            item.service_key = 'tailoring'
            item.service_name = 'Tailoring Certificate'
            item.service_icon = '✂️'
            item.applicant_name = item.full_name
            item.mobile = item.mobile_number
            item.detail_url = f"/admin-portal/tailoring/{item.order_id}/"
            combined_list.append(item)

    # 2. Basic Computer Applications
    if not service_filter or service_filter == 'computer':
        qs = BasicComputerCertificateApplication.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        for item in qs:
            if search_q and (search_q not in item.student_name.lower() and search_q not in item.order_id.lower() and search_q not in item.mobile_no.lower()):
                continue
            item.service_key = 'computer'
            item.service_name = 'Basic Computer Cert'
            item.service_icon = '💻'
            item.applicant_name = item.student_name
            item.mobile = item.mobile_no
            item.detail_url = f"/admin-portal/computer/{item.order_id}/"
            combined_list.append(item)

    # 3. Udyam Registration Applications
    if not service_filter or service_filter == 'udyam':
        qs = UdyamRegistrationApplication.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        for item in qs:
            if search_q and (search_q not in item.applicant_name.lower() and search_q not in item.order_id.lower() and search_q not in item.mobile_no.lower()):
                continue
            item.service_key = 'udyam'
            item.service_name = 'Udyam Registration'
            item.service_icon = '🏭'
            item.applicant_name = item.applicant_name
            item.mobile = item.mobile_no
            item.detail_url = f"/admin-portal/udyam/{item.order_id}/"
            combined_list.append(item)

    # 4. PVC Card Maker Applications
    if not service_filter or service_filter == 'pvc':
        qs = PVCMakerApplication.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        for item in qs:
            if search_q and (search_q not in item.full_name.lower() and search_q not in item.order_id.lower() and search_q not in item.customer_mobile.lower()):
                continue
            item.service_key = 'pvc'
            item.service_name = 'PVC Card Maker'
            item.service_icon = '🪪'
            item.applicant_name = item.full_name
            item.mobile = item.customer_mobile
            item.detail_url = f"/admin-portal/pvc-maker/{item.order_id}/"
            combined_list.append(item)

    # 5. CIBIL Score Applications
    if not service_filter or service_filter == 'cibil':
        qs = CibilScoreApplication.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        for item in qs:
            fullName = f"{item.first_name} {item.last_name}"
            if search_q and (search_q not in fullName.lower() and search_q not in item.order_id.lower() and search_q not in item.mobile_number.lower()):
                continue
            item.service_key = 'cibil'
            item.service_name = 'CIBIL Score Report'
            item.service_icon = '📈'
            item.applicant_name = fullName
            item.mobile = item.mobile_number
            item.detail_url = f"/admin-portal/cibil-score/{item.order_id}/"
            combined_list.append(item)

    # Sort combined by created_at descending
    combined_list.sort(key=lambda x: x.created_at, reverse=True)

    # Counts
    tailoring_count = TailoringCertificateApplication.objects.count()
    computer_count  = BasicComputerCertificateApplication.objects.count()
    udyam_count     = UdyamRegistrationApplication.objects.count()
    pvc_count       = PVCMakerApplication.objects.count()
    cibil_count     = CibilScoreApplication.objects.count()
    total_count     = tailoring_count + computer_count + udyam_count + pvc_count + cibil_count

    return render(request, 'admin_other_services.html', {
        'applications': combined_list,
        'service_filter': service_filter,
        'status_filter': status_filter,
        'search_q': search_q,
        'tailoring_count': tailoring_count,
        'computer_count': computer_count,
        'udyam_count': udyam_count,
        'pvc_count': pvc_count,
        'cibil_count': cibil_count,
        'total_count': total_count,
    })


def admin_cibil_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip()

    apps = CibilScoreApplication.objects.all().order_by('-created_at')

    if status_filter:
        apps = apps.filter(status=status_filter)

    if search_q:
        apps = apps.filter(first_name__icontains=search_q) | apps.filter(last_name__icontains=search_q) | apps.filter(order_id__icontains=search_q) | apps.filter(mobile_number__icontains=search_q)

    return render(request, 'admin_cibil_list.html', {
        'applications': apps,
        'status_filter': status_filter,
        'search_q': search_q,
    })


def admin_cibil_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(CibilScoreApplication, order_id=order_id)
    return render(request, 'admin_cibil_detail.html', {'app': app_obj})


def admin_cibil_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(CibilScoreApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'CIBIL Score Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        payment_provider='internal',
                        note=f'Refund for Rejected CIBIL Score Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_aadhaar_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status = request.GET.get('status', '').strip().upper()
    search = request.GET.get('q', '').strip()

    qs = AadhaarPdfApplication.objects.select_related('retailer').all().order_by('-created_at')

    if status and status in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(order_id__icontains=search) | qs.filter(name__icontains=search) | qs.filter(uid_number__icontains=search)

    return render(request, 'admin_aadhaar_list.html', {
        'applications': qs,
        'current_status': status,
        'search': search,
    })


def admin_aadhaar_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(AadhaarPdfApplication, order_id=order_id)
    return render(request, 'admin_aadhaar_detail.html', {'app': app_obj})


def admin_aadhaar_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(AadhaarPdfApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'Aadhaar PDF Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Aadhaar PDF Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_eid_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status = request.GET.get('status', '').strip().upper()
    search = request.GET.get('q', '').strip()

    qs = EidToUidApplication.objects.select_related('retailer').all().order_by('-created_at')

    if status and status in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(order_id__icontains=search) | qs.filter(eid_number__icontains=search)

    return render(request, 'admin_eid_list.html', {
        'applications': qs,
        'current_status': status,
        'search': search,
    })


def admin_eid_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(EidToUidApplication, order_id=order_id)
    return render(request, 'admin_eid_detail.html', {'app': app_obj})


def admin_eid_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(EidToUidApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'EID to UID Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected EID to UID Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_lms_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status = request.GET.get('status', '').strip().upper()
    search = request.GET.get('q', '').strip()

    qs = LMSCertificateApplication.objects.select_related('retailer').all().order_by('-created_at')

    if status and status in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(order_id__icontains=search) | qs.filter(full_name__icontains=search) | qs.filter(aadhaar_number__icontains=search)

    return render(request, 'admin_lms_list.html', {
        'applications': qs,
        'current_status': status,
        'search': search,
    })


def admin_lms_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(LMSCertificateApplication, order_id=order_id)
    return render(request, 'admin_lms_detail.html', {'app': app_obj})


def admin_lms_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(LMSCertificateApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if output_pdf:
            app_obj.output_pdf = output_pdf

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'LMS Certificate Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected LMS Certificate Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


def admin_pan_to_aadhaar_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status = request.GET.get('status', '').strip().upper()
    search = request.GET.get('q', '').strip()

    qs = PanToAadhaarApplication.objects.select_related('retailer').all().order_by('-created_at')

    if status and status in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(order_id__icontains=search) | qs.filter(pan_number__icontains=search)

    return render(request, 'admin_pan_to_aadhaar_list.html', {
        'applications': qs,
        'current_status': status,
        'search': search,
    })


def admin_pan_to_aadhaar_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(PanToAadhaarApplication, order_id=order_id)
    return render(request, 'admin_pan_to_aadhaar_detail.html', {'app': app_obj})


def admin_pan_to_aadhaar_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(PanToAadhaarApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        aadhaar_number = request.POST.get('aadhaar_number', '').strip()
        if aadhaar_number:
            app_obj.aadhaar_number = aadhaar_number

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'PAN to Aadhaar Application {order_id} approved & marked COMPLETED!'
        })

    elif action == 'REJECT':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a rejection reason.'}, status=400)

        already_refunded = (app_obj.status == 'REJECTED')

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = rejection_reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                if not already_refunded and app_obj.retailer:
                    retailer = app_obj.retailer
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected PAN to Aadhaar Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)






from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from .models import Retailer, TailoringCertificateApplication, BasicComputerCertificateApplication, UdyamRegistrationApplication, PVCMakerApplication, CibilScoreApplication, WalletTransaction, PANApplication, AadhaarPdfApplication, EidToUidApplication, LMSCertificateApplication, PanToAadhaarApplication, SeniorCitizenApplication, GruhaLaxmiApplication, GruhaLaxmiStatusApplication, GruhaLaxmiKYCApplication, GruhaLaxmiSanctionApplication, GruhaJyothiApplication, GruhaJyothiDlinkApplication, BhoomiPahaniLinkApplication, RTCDownloadApplication, AbhaCardApplication, AyushCardApplication, AyushDownloadApplication, EShramApplication, EShramDownloadApplication, PMKisanApplication, NaadaKacheriDownloadApplication, YuvaNidhiApplication, SSPPasswordChangeApplication, SSPMobileLinkApplication, MobileToPanApplication

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
    senior_pending = SeniorCitizenApplication.objects.filter(status='PENDING').count()
    gruha_laxmi_pending = GruhaLaxmiApplication.objects.filter(status='PENDING').count()
    gruha_laxmi_status_pending = GruhaLaxmiStatusApplication.objects.filter(status='PENDING').count()
    gruha_laxmi_kyc_pending = GruhaLaxmiKYCApplication.objects.filter(status='PENDING').count()
    gruha_laxmi_sanction_pending = GruhaLaxmiSanctionApplication.objects.filter(status='PENDING').count()
    gruha_jyothi_pending = GruhaJyothiApplication.objects.filter(status='PENDING').count()
    gruha_jyothi_dlink_pending = GruhaJyothiDlinkApplication.objects.filter(status='PENDING').count()
    bhoomi_pahani_link_pending = BhoomiPahaniLinkApplication.objects.filter(status='PENDING').count()
    rtc_download_pending = RTCDownloadApplication.objects.filter(status='PENDING').count()
    abha_card_pending = AbhaCardApplication.objects.filter(status='PENDING').count()
    ayush_card_pending = AyushCardApplication.objects.filter(status='PENDING').count()
    ayush_dwnld_pending = AyushDownloadApplication.objects.filter(status='PENDING').count()
    eshram_pending = EShramApplication.objects.filter(status='PENDING').count()
    eshram_dwnld_pending = EShramDownloadApplication.objects.filter(status='PENDING').count()
    pmkisan_pending = PMKisanApplication.objects.filter(status='PENDING').count()
    naadakacheri_dwnld_pending = NaadaKacheriDownloadApplication.objects.filter(status='PENDING').count()
    yuvanidhi_pending = YuvaNidhiApplication.objects.filter(status='PENDING').count()
    ssp_password_pending = SSPPasswordChangeApplication.objects.filter(status='PENDING').count()
    ssp_mobile_pending = SSPMobileLinkApplication.objects.filter(status='PENDING').count()
    total_pending = tailoring_pending + computer_pending + udyam_pending + pvc_pending + senior_pending + gruha_laxmi_pending + gruha_laxmi_status_pending + gruha_laxmi_kyc_pending + gruha_laxmi_sanction_pending + gruha_jyothi_pending + gruha_jyothi_dlink_pending + bhoomi_pahani_link_pending + rtc_download_pending + abha_card_pending + ayush_card_pending + ayush_dwnld_pending + eshram_pending + eshram_dwnld_pending + pmkisan_pending + naadakacheri_dwnld_pending + yuvanidhi_pending + ssp_password_pending + ssp_mobile_pending

    tailoring_completed = TailoringCertificateApplication.objects.filter(status='COMPLETED').count()
    computer_completed = BasicComputerCertificateApplication.objects.filter(status='COMPLETED').count()
    udyam_completed = UdyamRegistrationApplication.objects.filter(status='COMPLETED').count()
    pvc_completed = PVCMakerApplication.objects.filter(status='COMPLETED').count()
    senior_completed = SeniorCitizenApplication.objects.filter(status='COMPLETED').count()
    gruha_laxmi_completed = GruhaLaxmiApplication.objects.filter(status='COMPLETED').count()
    gruha_laxmi_status_completed = GruhaLaxmiStatusApplication.objects.filter(status='COMPLETED').count()
    gruha_laxmi_kyc_completed = GruhaLaxmiKYCApplication.objects.filter(status='COMPLETED').count()
    gruha_laxmi_sanction_completed = GruhaLaxmiSanctionApplication.objects.filter(status='COMPLETED').count()
    gruha_jyothi_completed = GruhaJyothiApplication.objects.filter(status='COMPLETED').count()
    gruha_jyothi_dlink_completed = GruhaJyothiDlinkApplication.objects.filter(status='COMPLETED').count()
    bhoomi_pahani_link_completed = BhoomiPahaniLinkApplication.objects.filter(status='COMPLETED').count()
    rtc_download_completed = RTCDownloadApplication.objects.filter(status='COMPLETED').count()
    abha_card_completed = AbhaCardApplication.objects.filter(status='COMPLETED').count()
    ayush_card_completed = AyushCardApplication.objects.filter(status='COMPLETED').count()
    ayush_dwnld_completed = AyushDownloadApplication.objects.filter(status='COMPLETED').count()
    eshram_completed = EShramApplication.objects.filter(status='COMPLETED').count()
    eshram_dwnld_completed = EShramDownloadApplication.objects.filter(status='COMPLETED').count()
    pmkisan_completed = PMKisanApplication.objects.filter(status='COMPLETED').count()
    naadakacheri_dwnld_completed = NaadaKacheriDownloadApplication.objects.filter(status='COMPLETED').count()
    yuvanidhi_completed = YuvaNidhiApplication.objects.filter(status='COMPLETED').count()
    ssp_password_completed = SSPPasswordChangeApplication.objects.filter(status='COMPLETED').count()
    ssp_mobile_completed = SSPMobileLinkApplication.objects.filter(status='COMPLETED').count()
    total_completed = tailoring_completed + computer_completed + udyam_completed + pvc_completed + senior_completed + gruha_laxmi_completed + gruha_laxmi_status_completed + gruha_laxmi_kyc_completed + gruha_laxmi_sanction_completed + gruha_jyothi_completed + gruha_jyothi_dlink_completed + bhoomi_pahani_link_completed + rtc_download_completed + abha_card_completed + ayush_card_completed + ayush_dwnld_completed + eshram_completed + eshram_dwnld_completed + pmkisan_completed + naadakacheri_dwnld_completed + yuvanidhi_completed + ssp_password_completed + ssp_mobile_completed

    tailoring_rejected = TailoringCertificateApplication.objects.filter(status='REJECTED').count()
    computer_rejected = BasicComputerCertificateApplication.objects.filter(status='REJECTED').count()
    udyam_rejected = UdyamRegistrationApplication.objects.filter(status='REJECTED').count()
    pvc_rejected = PVCMakerApplication.objects.filter(status='REJECTED').count()
    senior_rejected = SeniorCitizenApplication.objects.filter(status='REJECTED').count()
    gruha_laxmi_rejected = GruhaLaxmiApplication.objects.filter(status='REJECTED').count()
    gruha_laxmi_status_rejected = GruhaLaxmiStatusApplication.objects.filter(status='REJECTED').count()
    gruha_laxmi_kyc_rejected = GruhaLaxmiKYCApplication.objects.filter(status='REJECTED').count()
    gruha_laxmi_sanction_rejected = GruhaLaxmiSanctionApplication.objects.filter(status='REJECTED').count()
    gruha_jyothi_rejected = GruhaJyothiApplication.objects.filter(status='REJECTED').count()
    gruha_jyothi_dlink_rejected = GruhaJyothiDlinkApplication.objects.filter(status='REJECTED').count()
    bhoomi_pahani_link_rejected = BhoomiPahaniLinkApplication.objects.filter(status='REJECTED').count()
    rtc_download_rejected = RTCDownloadApplication.objects.filter(status='REJECTED').count()
    abha_card_rejected = AbhaCardApplication.objects.filter(status='REJECTED').count()
    ayush_card_rejected = AyushCardApplication.objects.filter(status='REJECTED').count()
    ayush_dwnld_rejected = AyushDownloadApplication.objects.filter(status='REJECTED').count()
    eshram_rejected = EShramApplication.objects.filter(status='REJECTED').count()
    eshram_dwnld_rejected = EShramDownloadApplication.objects.filter(status='REJECTED').count()
    pmkisan_rejected = PMKisanApplication.objects.filter(status='REJECTED').count()
    naadakacheri_dwnld_rejected = NaadaKacheriDownloadApplication.objects.filter(status='REJECTED').count()
    yuvanidhi_rejected = YuvaNidhiApplication.objects.filter(status='REJECTED').count()
    ssp_password_rejected = SSPPasswordChangeApplication.objects.filter(status='REJECTED').count()
    ssp_mobile_rejected = SSPMobileLinkApplication.objects.filter(status='REJECTED').count()
    total_rejected = tailoring_rejected + computer_rejected + udyam_rejected + pvc_rejected + senior_rejected + gruha_laxmi_rejected + gruha_laxmi_status_rejected + gruha_laxmi_kyc_rejected + gruha_laxmi_sanction_rejected + gruha_jyothi_rejected + gruha_jyothi_dlink_rejected + bhoomi_pahani_link_rejected + rtc_download_rejected + abha_card_rejected + ayush_card_rejected + ayush_dwnld_rejected + eshram_rejected + eshram_dwnld_rejected + pmkisan_rejected + naadakacheri_dwnld_rejected + yuvanidhi_rejected + ssp_password_rejected + ssp_mobile_rejected

    recent_tailoring = list(TailoringCertificateApplication.objects.all().order_by('-created_at')[:10])
    recent_computer = list(BasicComputerCertificateApplication.objects.all().order_by('-created_at')[:10])
    recent_udyam = list(UdyamRegistrationApplication.objects.all().order_by('-created_at')[:10])
    recent_pvc = list(PVCMakerApplication.objects.all().order_by('-created_at')[:10])
    recent_senior = list(SeniorCitizenApplication.objects.all().order_by('-created_at')[:10])
    recent_gruha_laxmi = list(GruhaLaxmiApplication.objects.all().order_by('-created_at')[:10])
    recent_gruha_laxmi_status = list(GruhaLaxmiStatusApplication.objects.all().order_by('-created_at')[:10])
    recent_gruha_laxmi_kyc = list(GruhaLaxmiKYCApplication.objects.all().order_by('-created_at')[:10])
    recent_gruha_laxmi_sanction = list(GruhaLaxmiSanctionApplication.objects.all().order_by('-created_at')[:10])
    recent_gruha_jyothi = list(GruhaJyothiApplication.objects.all().order_by('-created_at')[:10])
    recent_gruha_jyothi_dlink = list(GruhaJyothiDlinkApplication.objects.all().order_by('-created_at')[:10])
    recent_bhoomi_pahani_link = list(BhoomiPahaniLinkApplication.objects.all().order_by('-created_at')[:10])
    recent_rtc_download = list(RTCDownloadApplication.objects.all().order_by('-created_at')[:10])
    recent_abha_card = list(AbhaCardApplication.objects.all().order_by('-created_at')[:10])
    recent_ayush_card = list(AyushCardApplication.objects.all().order_by('-created_at')[:10])
    recent_ayush_dwnld = list(AyushDownloadApplication.objects.all().order_by('-created_at')[:10])
    recent_eshram = list(EShramApplication.objects.all().order_by('-created_at')[:10])
    recent_eshram_dwnld = list(EShramDownloadApplication.objects.all().order_by('-created_at')[:10])
    recent_pmkisan = list(PMKisanApplication.objects.all().order_by('-created_at')[:10])
    recent_naadakacheri_dwnld = list(NaadaKacheriDownloadApplication.objects.all().order_by('-created_at')[:10])
    recent_yuvanidhi = list(YuvaNidhiApplication.objects.all().order_by('-created_at')[:10])
    recent_ssp_password = list(SSPPasswordChangeApplication.objects.all().order_by('-created_at')[:10])
    recent_ssp_mobile = list(SSPMobileLinkApplication.objects.all().order_by('-created_at')[:10])

    recent_all = []
    for item in recent_ssp_mobile:
        item.service_type = 'SSP Mobile Link'
        item.service_icon = '📱'
        item.applicant_name = item.applicant_name
        item.mobile = item.new_mobile
        item.location_display = f"SSP ID: {item.ssp_id}"
        item.detail_url_name = 'admin_ssp_mobile_detail'
        recent_all.append(item)

    for item in recent_ssp_password:
        item.service_type = 'SSP Password Change'
        item.service_icon = '🔑'
        item.applicant_name = f"SSP ID: {item.ssp_id}"
        item.mobile = '-'
        item.location_display = '-'
        item.detail_url_name = 'admin_ssp_password_detail'
        recent_all.append(item)

    for item in recent_yuvanidhi:
        item.service_type = 'Yuva Nidhi Scheme'
        item.service_icon = '🎓'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = f"{item.talluk}, {item.district}"
        item.detail_url_name = 'admin_yuvanidhi_detail'
        recent_all.append(item)

    for item in recent_naadakacheri_dwnld:
        item.service_type = f"Naada Kacheri ({item.certificate_type})"
        item.service_icon = '📜'
        item.applicant_name = item.applicant_name
        item.mobile = '-'
        item.location_display = item.rd_number
        item.detail_url_name = 'admin_naadakacheri_dwnld_detail'
        recent_all.append(item)

    for item in recent_pmkisan:
        item.service_type = f"PM Kisan ({item.application_type})"
        item.service_icon = '🚜'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = item.state
        item.detail_url_name = 'admin_pmkisan_detail'
        recent_all.append(item)

    for item in recent_eshram_dwnld:
        item.service_type = 'e-Shram Download'
        item.service_icon = '📇'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = item.state
        item.detail_url_name = 'admin_eshram_dwnld_detail'
        recent_all.append(item)

    for item in recent_eshram:
        item.service_type = 'e-Shram Card'
        item.service_icon = '👷'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = f"{item.district}, {item.state}"
        item.detail_url_name = 'admin_eshram_detail'
        recent_all.append(item)

    for item in recent_ayush_dwnld:
        item.service_type = 'Ayushman Card Download'
        item.service_icon = '💳'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = f"{item.district}, {item.state}"
        item.detail_url_name = 'admin_ayush_dwnld_detail'
        recent_all.append(item)

    for item in recent_ayush_card:
        item.service_type = 'Ayushman Bharat Card'
        item.service_icon = '🏥'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = f"{item.district}, {item.state}"
        item.detail_url_name = 'admin_ayush_card_detail'
        recent_all.append(item)

    for item in recent_abha_card:
        item.service_type = 'ABHA Health Card'
        item.service_icon = '🛡️'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = item.state
        item.detail_url_name = 'admin_abha_card_detail'
        recent_all.append(item)

    for item in recent_rtc_download:
        item.service_type = 'RTC / Pahani Download'
        item.service_icon = '📜'
        item.applicant_name = item.applicant_name
        item.mobile = '-'
        item.location_display = f"{item.district} / {item.talluk}"
        item.detail_url_name = 'admin_rtc_download_detail'
        recent_all.append(item)

    for item in recent_bhoomi_pahani_link:
        item.service_type = 'Aadhaar to Pahani Link'
        item.service_icon = '🔗'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = f"{item.district} / {item.talluk}"
        item.detail_url_name = 'admin_bhoomi_pahani_link_detail'
        recent_all.append(item)

    for item in recent_gruha_jyothi_dlink:
        item.service_type = 'Gruha Jyothi D-Link'
        item.service_icon = '🔗'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = item.district or 'Karnataka'
        item.detail_url_name = 'admin_gruha_jyothi_dlink_detail'
        recent_all.append(item)
    for item in recent_gruha_jyothi:
        item.service_type = 'Gruha Jyothi'
        item.service_icon = '💡'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = 'Karnataka'
        item.detail_url_name = 'admin_gruha_jyothi_detail'
        recent_all.append(item)

    for item in recent_gruha_laxmi_sanction:
        item.service_type = 'Gruha Laxmi Sanction'
        item.service_icon = '📜'
        item.applicant_name = item.applicant_name
        item.mobile = item.ration_number
        item.location_display = 'Karnataka'
        item.detail_url_name = 'admin_gruha_laxmi_sanction_detail'
        recent_all.append(item)

    for item in recent_gruha_laxmi_kyc:
        item.service_type = 'Gruha Laxmi KYC'
        item.service_icon = '🏠'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = 'Karnataka'
        item.detail_url_name = 'admin_gruha_laxmi_kyc_detail'
        recent_all.append(item)

    for item in recent_gruha_laxmi_status:
        item.service_type = 'Gruha Laxmi Status'
        item.service_icon = '🔍'
        item.applicant_name = item.applicant_name
        item.mobile = item.ration_number
        item.location_display = 'Karnataka'
        item.detail_url_name = 'admin_gruha_laxmi_status_detail'
        recent_all.append(item)

    for item in recent_gruha_laxmi:
        item.service_type = 'Gruha Laxmi'
        item.service_icon = '🌸'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = 'Karnataka'
        item.detail_url_name = 'admin_gruha_laxmi_detail'
        recent_all.append(item)

    for item in recent_senior:
        item.service_type = 'Senior Citizen'
        item.service_icon = '🛡️'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile
        item.location_display = f"{item.district} / {item.talluk}"
        item.detail_url_name = 'admin_senior_detail'
        recent_all.append(item)

    for item in recent_tailoring:
        item.service_type = 'Tailoring'
        item.service_icon = '✂️'
        item.applicant_name = item.full_name
        item.mobile = item.mobile_number
        item.location_display = getattr(item, 'state', '-')
        item.detail_url_name = 'admin_tailoring_detail'
        recent_all.append(item)

    for item in recent_computer:
        item.service_type = 'Basic Computer'
        item.service_icon = '💻'
        item.applicant_name = item.student_name
        item.mobile = item.mobile_no
        item.location_display = getattr(item, 'state', '-')
        item.detail_url_name = 'admin_computer_detail'
        recent_all.append(item)

    for item in recent_udyam:
        item.service_type = 'Udyam Registration'
        item.service_icon = '🏭'
        item.applicant_name = item.applicant_name
        item.mobile = item.mobile_no
        item.location_display = getattr(item, 'state', '-')
        item.detail_url_name = 'admin_udyam_detail'
        recent_all.append(item)

    for item in recent_pvc:
        item.service_type = 'PVC Card Maker'
        item.service_icon = '🪪'
        item.applicant_name = item.full_name
        item.mobile = item.customer_mobile
        item.location_display = 'Karnataka'
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
        'senior_pending': senior_pending,
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


# ── Senior Citizen Admin Portal ─────────────────────────────────────

def admin_senior_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status = request.GET.get('status', '').strip().upper()
    search = request.GET.get('q', '').strip()

    qs = SeniorCitizenApplication.objects.select_related('retailer').all().order_by('-created_at')

    if status and status in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(order_id__icontains=search) | qs.filter(applicant_name__icontains=search) | qs.filter(aadhaar_number__icontains=search) | qs.filter(mobile__icontains=search)

    return render(request, 'admin_senior_list.html', {
        'applications': qs,
        'current_status': status,
        'search': search,
    })


def admin_senior_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(SeniorCitizenApplication, order_id=order_id)
    return render(request, 'admin_senior_detail.html', {'app': app_obj})


def admin_senior_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    app_obj = get_object_or_404(SeniorCitizenApplication, order_id=order_id)
    action = request.POST.get('action', '').strip().upper()

    if action == 'APPROVE':
        output_file = request.FILES.get('output_pdf')
        if output_file:
            app_obj.output_pdf = output_file

        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'Senior Citizen Application {order_id} approved & marked COMPLETED!'
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
                        note=f'Refund for Rejected Senior Citizen Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Gruha Laxmi Applications ──────────────────────────────

def admin_gruha_laxmi_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = GruhaLaxmiApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_gruha_laxmi_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_gruha_laxmi_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(GruhaLaxmiApplication, order_id=order_id)
    return render(request, 'admin_gruha_laxmi_detail.html', {'app_obj': app_obj})


def admin_gruha_laxmi_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(GruhaLaxmiApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Gruha Laxmi Sanction/Document PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Gruha Laxmi Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Gruha Laxmi Status Applications ───────────────────────

def admin_gruha_laxmi_status_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = GruhaLaxmiStatusApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_gruha_laxmi_status_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_gruha_laxmi_status_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(GruhaLaxmiStatusApplication, order_id=order_id)
    return render(request, 'admin_gruha_laxmi_status_detail.html', {'app_obj': app_obj})


def admin_gruha_laxmi_status_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(GruhaLaxmiStatusApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Gruha Laxmi Status Report PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Status Request {order_id} approved and report uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Gruha Laxmi Status Request — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Status Request {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Gruha Laxmi KYC Applications ───────────────────────────

def admin_gruha_laxmi_kyc_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = GruhaLaxmiKYCApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_gruha_laxmi_kyc_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_gruha_laxmi_kyc_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(GruhaLaxmiKYCApplication, order_id=order_id)
    return render(request, 'admin_gruha_laxmi_kyc_detail.html', {'app_obj': app_obj})


def admin_gruha_laxmi_kyc_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(GruhaLaxmiKYCApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Gruha Laxmi e-KYC Document PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Gruha Laxmi e-KYC Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Gruha Laxmi Sanction Applications ────────────────────────

def admin_gruha_laxmi_sanction_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = GruhaLaxmiSanctionApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_gruha_laxmi_sanction_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_gruha_laxmi_sanction_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(GruhaLaxmiSanctionApplication, order_id=order_id)
    return render(request, 'admin_gruha_laxmi_sanction_detail.html', {'app_obj': app_obj})


def admin_gruha_laxmi_sanction_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(GruhaLaxmiSanctionApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Gruha Laxmi Sanction Order PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and sanction order uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Gruha Laxmi Sanction Order Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Gruha Jyothi Applications ────────────────────────────────

def admin_gruha_jyothi_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = GruhaJyothiApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_gruha_jyothi_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_gruha_jyothi_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(GruhaJyothiApplication, order_id=order_id)
    return render(request, 'admin_gruha_jyothi_detail.html', {'app_obj': app_obj})


def admin_gruha_jyothi_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(GruhaJyothiApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Gruha Jyothi Document PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Gruha Jyothi Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Gruha Jyothi D-Link Applications ─────────────────────────

def admin_gruha_jyothi_dlink_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = GruhaJyothiDlinkApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_gruha_jyothi_dlink_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_gruha_jyothi_dlink_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(GruhaJyothiDlinkApplication, order_id=order_id)
    return render(request, 'admin_gruha_jyothi_dlink_detail.html', {'app_obj': app_obj})


def admin_gruha_jyothi_dlink_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(GruhaJyothiDlinkApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Gruha Jyothi D-Link Document PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Gruha Jyothi D-Link Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Bhoomi Pahani Link Applications ──────────────────────────

def admin_bhoomi_pahani_link_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = BhoomiPahaniLinkApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_bhoomi_pahani_link_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_bhoomi_pahani_link_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(BhoomiPahaniLinkApplication, order_id=order_id)
    return render(request, 'admin_bhoomi_pahani_link_detail.html', {'app_obj': app_obj})


def admin_bhoomi_pahani_link_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(BhoomiPahaniLinkApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Bhoomi Pahani Link Document PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Bhoomi Pahani Link Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin RTC Download Applications ───────────────────────────────

def admin_rtc_download_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = RTCDownloadApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_rtc_download_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_rtc_download_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(RTCDownloadApplication, order_id=order_id)
    return render(request, 'admin_rtc_download_detail.html', {'app_obj': app_obj})


def admin_rtc_download_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(RTCDownloadApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated RTC / Pahani Document PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected RTC Download Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin ABHA Card Applications ──────────────────────────────────

def admin_abha_card_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = AbhaCardApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_abha_card_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_abha_card_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(AbhaCardApplication, order_id=order_id)
    return render(request, 'admin_abha_card_detail.html', {'app_obj': app_obj})


def admin_abha_card_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(AbhaCardApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Ayushman Bharat Health Card PDF/Image.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected ABHA Card Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Ayushman Card (₹100 Insurance Scheme) Applications ─────

def admin_ayush_card_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = AyushCardApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_ayush_card_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_ayush_card_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(AyushCardApplication, order_id=order_id)
    return render(request, 'admin_ayush_card_detail.html', {'app_obj': app_obj})


def admin_ayush_card_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(AyushCardApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Ayushman Card PDF.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Ayushman Card Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Ayushman Card Download Only Applications ────────────────

def admin_ayush_dwnld_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = AyushDownloadApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_ayush_dwnld_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_ayush_dwnld_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(AyushDownloadApplication, order_id=order_id)
    return render(request, 'admin_ayush_dwnld_detail.html', {'app_obj': app_obj})


def admin_ayush_dwnld_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(AyushDownloadApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Ayushman Smart Card PDF.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Ayushman Download Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin e-Shram Card Applications ──────────────────────────────

def admin_eshram_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = EShramApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_eshram_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_eshram_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(EShramApplication, order_id=order_id)
    return render(request, 'admin_eshram_detail.html', {'app_obj': app_obj})


def admin_eshram_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(EShramApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated e-Shram Card PDF.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected e-Shram Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin e-Shram Download Only Applications ──────────────────────

def admin_eshram_dwnld_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = EShramDownloadApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_eshram_dwnld_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_eshram_dwnld_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(EShramDownloadApplication, order_id=order_id)
    return render(request, 'admin_eshram_dwnld_detail.html', {'app_obj': app_obj})


def admin_eshram_dwnld_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(EShramDownloadApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated e-Shram Smart Card PDF.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected e-Shram Download Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin PM Kisan Services Applications ──────────────────────────

def admin_pmkisan_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = PMKisanApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_pmkisan_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_pmkisan_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(PMKisanApplication, order_id=order_id)
    return render(request, 'admin_pmkisan_detail.html', {'app_obj': app_obj})


def admin_pmkisan_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(PMKisanApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated PM Kisan Document/Receipt.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected PM Kisan Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Naada Kacheri Certificate Download Applications ────────

def admin_naadakacheri_dwnld_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = NaadaKacheriDownloadApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_naadakacheri_dwnld_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_naadakacheri_dwnld_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(NaadaKacheriDownloadApplication, order_id=order_id)
    return render(request, 'admin_naadakacheri_dwnld_detail.html', {'app_obj': app_obj})


def admin_naadakacheri_dwnld_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(NaadaKacheriDownloadApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Naada Kacheri Certificate PDF.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Naada Kacheri Certificate Download — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Yuva Nidhi Scheme Applications ──────────────────────────

def admin_yuvanidhi_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = YuvaNidhiApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_yuvanidhi_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_yuvanidhi_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(YuvaNidhiApplication, order_id=order_id)
    return render(request, 'admin_yuvanidhi_detail.html', {'app_obj': app_obj})


def admin_yuvanidhi_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(YuvaNidhiApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload generated Yuva Nidhi Document/Receipt.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected Yuva Nidhi Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin SSP Password Change Applications ────────────────────────

def admin_ssp_password_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = SSPPasswordChangeApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_ssp_password_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_ssp_password_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(SSPPasswordChangeApplication, order_id=order_id)
    return render(request, 'admin_ssp_password_detail.html', {'app_obj': app_obj})


def admin_ssp_password_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(SSPPasswordChangeApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload confirmation document/receipt.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected SSP Password Change — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin SSP Mobile Link Applications ────────────────────────────

def admin_ssp_mobile_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = SSPMobileLinkApplication.objects.all()

    if status_filter in ['PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_ssp_mobile_list.html', {
        'applications': applications,
        'current_status': status_filter
    })


def admin_ssp_mobile_detail(request, order_id):
    if not _check_admin(request):
        return redirect('admin_login')

    app_obj = get_object_or_404(SSPMobileLinkApplication, order_id=order_id)
    return render(request, 'admin_ssp_mobile_detail.html', {'app_obj': app_obj})


def admin_ssp_mobile_process(request, order_id):
    if not _check_admin(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    app_obj = get_object_or_404(SSPMobileLinkApplication, order_id=order_id)
    action = request.POST.get('action')

    if action == 'APPROVE':
        output_pdf = request.FILES.get('output_pdf')
        if not output_pdf:
            return JsonResponse({'success': False, 'error': 'Please upload confirmation document/receipt.'}, status=400)

        app_obj.output_pdf = output_pdf
        app_obj.status = 'COMPLETED'
        app_obj.processed_at = timezone.now()
        app_obj.save()

        return JsonResponse({'success': True, 'message': f'Application {order_id} approved and document uploaded!'})

    elif action == 'REJECT':
        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        try:
            with transaction.atomic():
                app_obj.status = 'REJECTED'
                app_obj.rejection_reason = reason
                app_obj.processed_at = timezone.now()
                app_obj.save()

                # Refund wallet
                retailer = app_obj.retailer
                if retailer:
                    refund_amount = app_obj.amount
                    retailer.wallet_balance += refund_amount
                    retailer.save(update_fields=['wallet_balance'])

                    WalletTransaction.objects.create(
                        retailer=retailer,
                        amount=refund_amount,
                        tx_type='credit',
                        status='completed',
                        note=f'Refund for Rejected SSP Mobile Link Application — Order ID: {app_obj.order_id}'
                    )

            return JsonResponse({
                'success': True,
                'message': f'Application {order_id} rejected. ₹{app_obj.amount} refunded to retailer wallet.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


# ── Admin Govt Services Directory Boxes View ───────────────────────

def admin_govt_services_directory(request):
    if not _check_admin(request):
        return redirect('admin_login')

    services_list = [
        {
            'title': 'Senior Citizen Card',
            'code': 'senior',
            'icon': 'fa-solid fa-landmark',
            'color': '#ea580c',
            'badge_bg': '#fff7ed',
            'badge_color': '#ea580c',
            'url_name': 'admin_senior_list',
            'pending_count': SeniorCitizenApplication.objects.filter(status='PENDING').count(),
            'total_count': SeniorCitizenApplication.objects.count(),
        },
        {
            'title': 'Gruha Laxmi Application',
            'code': 'gruha_laxmi',
            'icon': 'fa-solid fa-hand-holding-heart',
            'color': '#db2777',
            'badge_bg': '#fce7f3',
            'badge_color': '#db2777',
            'url_name': 'admin_gruha_laxmi_list',
            'pending_count': GruhaLaxmiApplication.objects.filter(status='PENDING').count(),
            'total_count': GruhaLaxmiApplication.objects.count(),
        },
        {
            'title': 'Gruha Laxmi Status Search',
            'code': 'gruha_laxmi_status',
            'icon': 'fa-solid fa-magnifying-glass',
            'color': '#0284c7',
            'badge_bg': '#e0f2fe',
            'badge_color': '#0284c7',
            'url_name': 'admin_gruha_laxmi_status_list',
            'pending_count': GruhaLaxmiStatusApplication.objects.filter(status='PENDING').count(),
            'total_count': GruhaLaxmiStatusApplication.objects.count(),
        },
        {
            'title': 'Gruha Laxmi Direct KYC',
            'code': 'gruha_laxmi_kyc',
            'icon': 'fa-solid fa-id-card',
            'color': '#7c3aed',
            'badge_bg': '#f3e8ff',
            'badge_color': '#7c3aed',
            'url_name': 'admin_gruha_laxmi_kyc_list',
            'pending_count': GruhaLaxmiKYCApplication.objects.filter(status='PENDING').count(),
            'total_count': GruhaLaxmiKYCApplication.objects.count(),
        },
        {
            'title': 'Gruha Laxmi Sanction Print',
            'code': 'gruha_laxmi_sanction',
            'icon': 'fa-solid fa-print',
            'color': '#059669',
            'badge_bg': '#d1fae5',
            'badge_color': '#059669',
            'url_name': 'admin_gruha_laxmi_sanction_list',
            'pending_count': GruhaLaxmiSanctionApplication.objects.filter(status='PENDING').count(),
            'total_count': GruhaLaxmiSanctionApplication.objects.count(),
        },
        {
            'title': 'Gruha Jyothi Application',
            'code': 'gruha_jyothi',
            'icon': 'fa-solid fa-lightbulb',
            'color': '#ca8a04',
            'badge_bg': '#fef9c3',
            'badge_color': '#ca8a04',
            'url_name': 'admin_gruha_jyothi_list',
            'pending_count': GruhaJyothiApplication.objects.filter(status='PENDING').count(),
            'total_count': GruhaJyothiApplication.objects.count(),
        },
        {
            'title': 'Gruha Jyothi D-Link',
            'code': 'gruha_jyothi_dlink',
            'icon': 'fa-solid fa-link',
            'color': '#2563eb',
            'badge_bg': '#dbeafe',
            'badge_color': '#2563eb',
            'url_name': 'admin_gruha_jyothi_dlink_list',
            'pending_count': GruhaJyothiDlinkApplication.objects.filter(status='PENDING').count(),
            'total_count': GruhaJyothiDlinkApplication.objects.count(),
        },
        {
            'title': 'Bhoomi Pahani Link',
            'code': 'bhoomi_pahani_link',
            'icon': 'fa-solid fa-wheat-awn',
            'color': '#65a30d',
            'badge_bg': '#ecfccb',
            'badge_color': '#65a30d',
            'url_name': 'admin_bhoomi_pahani_link_list',
            'pending_count': BhoomiPahaniLinkApplication.objects.filter(status='PENDING').count(),
            'total_count': BhoomiPahaniLinkApplication.objects.count(),
        },
        {
            'title': 'RTC Download',
            'code': 'rtc_download',
            'icon': 'fa-solid fa-file-invoice',
            'color': '#0d9488',
            'badge_bg': '#ccfbf1',
            'badge_color': '#0d9488',
            'url_name': 'admin_rtc_download_list',
            'pending_count': RTCDownloadApplication.objects.filter(status='PENDING').count(),
            'total_count': RTCDownloadApplication.objects.count(),
        },
        {
            'title': 'ABHA Health Card',
            'code': 'abha_card',
            'icon': 'fa-solid fa-shield-halved',
            'color': '#4f46e5',
            'badge_bg': '#e0e7ff',
            'badge_color': '#4f46e5',
            'url_name': 'admin_abha_card_list',
            'pending_count': AbhaCardApplication.objects.filter(status='PENDING').count(),
            'total_count': AbhaCardApplication.objects.count(),
        },
        {
            'title': 'Ayushman Bharat Card',
            'code': 'ayush_card',
            'icon': 'fa-solid fa-id-card-clip',
            'color': '#16a34a',
            'badge_bg': '#dcfce7',
            'badge_color': '#16a34a',
            'url_name': 'admin_ayush_card_list',
            'pending_count': AyushCardApplication.objects.filter(status='PENDING').count(),
            'total_count': AyushCardApplication.objects.count(),
        },
        {
            'title': 'Ayushman Card Download',
            'code': 'ayush_dwnld',
            'icon': 'fa-solid fa-download',
            'color': '#0891b2',
            'badge_bg': '#cffaff',
            'badge_color': '#0891b2',
            'url_name': 'admin_ayush_dwnld_list',
            'pending_count': AyushDownloadApplication.objects.filter(status='PENDING').count(),
            'total_count': AyushDownloadApplication.objects.count(),
        },
        {
            'title': 'e-Shram Card',
            'code': 'eshram',
            'icon': 'fa-solid fa-helmet-safety',
            'color': '#d97706',
            'badge_bg': '#fef3c7',
            'badge_color': '#d97706',
            'url_name': 'admin_eshram_list',
            'pending_count': EShramApplication.objects.filter(status='PENDING').count(),
            'total_count': EShramApplication.objects.count(),
        },
        {
            'title': 'e-Shram Download',
            'code': 'eshram_dwnld',
            'icon': 'fa-solid fa-file-arrow-down',
            'color': '#475569',
            'badge_bg': '#f1f5f9',
            'badge_color': '#475569',
            'url_name': 'admin_eshram_dwnld_list',
            'pending_count': EShramDownloadApplication.objects.filter(status='PENDING').count(),
            'total_count': EShramDownloadApplication.objects.count(),
        },
        {
            'title': 'PM Kisan Application',
            'code': 'pmkisan',
            'icon': 'fa-solid fa-tractor',
            'color': '#15803d',
            'badge_bg': '#dcfce7',
            'badge_color': '#15803d',
            'url_name': 'admin_pmkisan_list',
            'pending_count': PMKisanApplication.objects.filter(status='PENDING').count(),
            'total_count': PMKisanApplication.objects.count(),
        },
        {
            'title': 'Naada Kacheri Download',
            'code': 'naadakacheri_dwnld',
            'icon': 'fa-solid fa-certificate',
            'color': '#9333ea',
            'badge_bg': '#f3e8ff',
            'badge_color': '#9333ea',
            'url_name': 'admin_naadakacheri_dwnld_list',
            'pending_count': NaadaKacheriDownloadApplication.objects.filter(status='PENDING').count(),
            'total_count': NaadaKacheriDownloadApplication.objects.count(),
        },
        {
            'title': 'Yuva Nidhi Scheme',
            'code': 'yuvanidhi',
            'icon': 'fa-solid fa-graduation-cap',
            'color': '#2563eb',
            'badge_bg': '#dbeafe',
            'badge_color': '#2563eb',
            'url_name': 'admin_yuvanidhi_list',
            'pending_count': YuvaNidhiApplication.objects.filter(status='PENDING').count(),
            'total_count': YuvaNidhiApplication.objects.count(),
        },
        {
            'title': 'SSP Password Change',
            'code': 'ssp_password',
            'icon': 'fa-solid fa-key',
            'color': '#e05e12',
            'badge_bg': '#ffedd5',
            'badge_color': '#e05e12',
            'url_name': 'admin_ssp_password_list',
            'pending_count': SSPPasswordChangeApplication.objects.filter(status='PENDING').count(),
            'total_count': SSPPasswordChangeApplication.objects.count(),
        },
        {
            'title': 'SSP Mobile Link',
            'code': 'ssp_mobile',
            'icon': 'fa-solid fa-mobile-screen-button',
            'color': '#0284c7',
            'badge_bg': '#e0f2fe',
            'badge_color': '#0284c7',
            'url_name': 'admin_ssp_mobile_list',
            'pending_count': SSPMobileLinkApplication.objects.filter(status='PENDING').count(),
            'total_count': SSPMobileLinkApplication.objects.count(),
        },
    ]

    total_pending_all = sum(s['pending_count'] for s in services_list)

    return render(request, 'admin_govt_services_directory.html', {
        'services': services_list,
        'total_pending_all': total_pending_all
    })


# ── Admin Mobile to PAN Applications ──────────────────────────────

def admin_mobile_to_pan_applications(request):
    if not _check_admin(request):
        return redirect('admin_login')

    status_filter = request.GET.get('status', 'ALL').upper()
    applications = MobileToPanApplication.objects.all()

    if status_filter in ['COMPLETED', 'FAILED']:
        applications = applications.filter(status=status_filter)

    return render(request, 'admin_mobile_to_pan_list.html', {
        'applications': applications,
        'current_status': status_filter
    })



























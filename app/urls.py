# Apne existing urls.py ko IS se replace karo

from django.urls import path
from . import views, vehicle_views, admin_views
from .views import (
    retailer_login, retailer_logout,
    retailer_signup, retailer_dashboard,
)
from .views import create_razorpay_order, verify_razorpay_payment
from .views import retailer_wallet

urlpatterns = [
    # ── Retailer Auth ──────────────────────────────────────────────────
    path('',           retailer_login,     name='retailer_login'),
    path('signup/',    retailer_signup,    name='retailer_signup'),
    path('logout/', views.retailer_logout, name='retailer_logout'),
    path('wallet/', retailer_wallet, name='wallet'),
    path('pricing/', views.pricing_page, name='pricing'),
    path('profile/', views.profile_page, name='profile'),
    path('dashboard/', retailer_dashboard, name='retailer_dashboard'),

    # ── PAN App (existing) ─────────────────────────────────────────────
    path('pan/form/',             views.form,               name='form'),
    path('pan/applied-list/',     views.applied_list,       name='applied_list'),
    path('wallet/create-order/',   create_razorpay_order,    name='wallet_create_order'),
    path('wallet/verify/',         verify_razorpay_payment,  name='wallet_verify'),
    path('detail/<str:order_id>/',      views.detail,       name='detail'),
    path('pan/detail/<str:order_id>/',  views.detail,       name='detail_with_prefix'),
    path('pan/print/<str:order_id>/',   views.pan_print,    name='pan_print'),
    path('api/verify-pan/',       views.verify_pan,         name='verify_pan'),
    path('api/submit-application/', views.submit_application, name='submit_application'),
    path('print/<str:order_id>/', views.pan_print, name='print_short'),
    path('vehicle/rc-advance/', vehicle_views.vehicle_rc_page, name='vehicle_rc_page'),
    path('vehicle/rc-advance/fetch/', vehicle_views.vehicle_rc_api, name='vehicle_rc_api'),
    path('vehicle/rc-advance/list/', vehicle_views.vehicle_rc_list, name='vehicle_rc_list'),

    path('vehicle/driving-services/', views.driving_services, name='driving_services'),
    path('vehicle/dl-allindia/', views.dl_allindia_page, name='dl_allindia'),
    path('vehicle/dl-allindia/fetch/', views.dl_allindia_api, name='dl_allindia_api'),
    path('vehicle/rc-allindia/', vehicle_views.vehicle_rc_page, name='vehicle_rc_allindia'),
    path('vehicle/rc/pdf/<str:order_id>/', vehicle_views.vehicle_rc_allindia_pdf, name='vehicle_rc_allindia_pdf'),
    path('vehicle/rc-allindia/pdf/<str:order_id>/', vehicle_views.vehicle_rc_allindia_pdf, name='vehicle_rc_allindia_pdf_alt'),
    path('vehicle/dl-karnataka/', views.dl_karnataka_page, name='dl_karnataka'),
    path('vehicle/dl-karnataka/fetch/', views.dl_karnataka_api, name='dl_karnataka_api'),
    path('vehicle/dl-karnataka/card/<str:order_id>/', views.dl_karnataka_view_card, name='dl_karnataka_card'),

    # ── Tailoring Certificate & Other Services ─────────────────────────
    path('services/kar-gov/', views.kar_gov_services_page, name='kar_gov_services'),
    path('services/kar-gov/senior-citizen/', views.senior_citizen_page, name='senior_citizen'),
    path('services/kar-gov/senior-citizen/submit/', views.senior_citizen_submit, name='senior_citizen_submit'),
    path('services/kar-gov/senior-citizen/list/', views.senior_citizen_list, name='senior_citizen_list'),
    path('services/kar-gov/senior-citizen/download/<str:order_id>/', views.senior_citizen_download, name='senior_citizen_download'),

    path('services/print/', views.print_services_page, name='print_services'),
    path('services/pan/', views.pan_services_page, name='pan_services'),
    path('services/pan/pan-to-aadhaar/', views.pan_to_aadhaar_page, name='pan_to_aadhaar'),
    path('services/pan/pan-to-aadhaar/submit/', views.pan_to_aadhaar_submit, name='pan_to_aadhaar_submit'),
    path('services/voter/', views.voter_services_page, name='voter_services'),
    path('services/ration/', views.ration_services_page, name='ration_services'),
    path('services/aadhaar/', views.aadhaar_services_page, name='aadhaar_services'),
    path('services/aadhaar/pdf/', views.aadhaar_pdf_page, name='aadhaar_pdf'),
    path('services/aadhaar/pdf/submit/', views.aadhaar_pdf_submit, name='aadhaar_pdf_submit'),
    path('services/aadhaar/pdf/list/', views.aadhaar_pdf_list, name='aadhaar_pdf_list'),
    path('services/aadhaar/pdf/download/<str:order_id>/', views.aadhaar_pdf_download, name='aadhaar_pdf_download'),
    path('services/aadhaar/eid-to-uid/', views.eid_to_uid_page, name='eid_to_uid'),
    path('services/aadhaar/eid-to-uid/submit/', views.eid_to_uid_submit, name='eid_to_uid_submit'),
    path('services/aadhaar/eid-to-uid/list/', views.eid_to_uid_list, name='eid_to_uid_list'),
    path('services/aadhaar/eid-to-uid/download/<str:order_id>/', views.eid_to_uid_download, name='eid_to_uid_download'),
    path('services/aadhaar/lms-certificate/', views.lms_certificate_page, name='lms_certificate'),
    path('services/aadhaar/lms-certificate/submit/', views.lms_certificate_submit, name='lms_certificate_submit'),
    path('services/aadhaar/lms-certificate/list/', views.lms_certificate_list, name='lms_certificate_list'),
    path('services/aadhaar/lms-certificate/download/<str:order_id>/', views.lms_certificate_download, name='lms_certificate_download'),
    path('services/other/', views.other_services_page, name='other_services'),
    path('services/tailoring/', views.tailoring_certificate_page, name='tailoring_certificate'),
    path('services/tailoring/submit/', views.tailoring_certificate_submit, name='tailoring_certificate_submit'),
    path('services/tailoring/list/', views.tailoring_certificate_list, name='tailoring_certificate_list'),
    path('services/tailoring/download/<str:order_id>/', views.tailoring_certificate_download, name='tailoring_certificate_download'),

    # ── Basic Computer Certificate ───────────────────────────────────
    path('services/basic-computer/', views.basic_computer_certificate_page, name='basic_computer_certificate'),
    path('services/basic-computer/submit/', views.basic_computer_certificate_submit, name='basic_computer_certificate_submit'),
    path('services/basic-computer/list/', views.basic_computer_certificate_list, name='basic_computer_certificate_list'),
    path('services/basic-computer/download/<str:order_id>/', views.basic_computer_certificate_download, name='basic_computer_certificate_download'),

    # ── Udyam Registration ───────────────────────────────────────────
    path('services/udyam/', views.udyam_registration_page, name='udyam_registration'),
    path('services/udyam/submit/', views.udyam_registration_submit, name='udyam_registration_submit'),
    path('services/udyam/list/', views.udyam_registration_list, name='udyam_registration_list'),
    path('services/udyam/download/<str:order_id>/', views.udyam_registration_download, name='udyam_registration_download'),

    # ── PVC Card Maker ───────────────────────────────────────────
    path('services/pvc-maker/', views.pvc_maker_page, name='pvc_maker'),
    path('services/pvc-maker/submit/', views.pvc_maker_submit, name='pvc_maker_submit'),
    path('services/pvc-maker/list/', views.pvc_maker_list, name='pvc_maker_list'),
    path('services/pvc-maker/download/<str:order_id>/', views.pvc_maker_download, name='pvc_maker_download'),

    # ── CIBIL Score ───────────────────────────────────────────
    path('services/cibil-score/', views.cibil_score_page, name='cibil_score'),
    path('services/cibil-score/submit/', views.cibil_score_submit, name='cibil_score_submit'),
    path('services/cibil-score/list/', views.cibil_score_list, name='cibil_score_list'),
    path('services/cibil-score/download/<str:order_id>/', views.cibil_score_download, name='cibil_score_download'),

    # ── Free Tools ───────────────────────────────────────────
    path('services/free-tools/', views.free_tools_page, name='free_tools'),
    path('services/free-tools/resume-maker/', views.free_resume_maker_page, name='free_resume_maker'),
    path('services/free-tools/jpg-to-pdf/', views.free_jpg_to_pdf_page, name='free_jpg_to_pdf'),
    path('services/free-tools/pdf-to-jpg/', views.free_pdf_to_jpg_page, name='free_pdf_to_jpg'),
    path('services/free-tools/photo-maker/', views.free_photo_maker_page, name='free_photo_maker'),
    path('services/free-tools/bg-remover/', views.free_bg_remover_page, name='free_bg_remover'),
    path('services/free-tools/pvc-maker/', views.free_pvc_maker_page, name='free_pvc_maker'),

    # ── Custom Admin Portal ───────────────────────────────────────────
    path('admin-portal/', admin_views.admin_login, name='admin_login'),
    path('admin-portal/logout/', admin_views.admin_logout, name='admin_logout'),
    path('admin-portal/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/other-services/', admin_views.admin_other_services, name='admin_other_services'),
    path('admin-portal/tailoring/', admin_views.admin_tailoring_applications, name='admin_tailoring_list'),
    path('admin-portal/tailoring/<str:order_id>/', admin_views.admin_tailoring_detail, name='admin_tailoring_detail'),
    path('admin-portal/tailoring/<str:order_id>/process/', admin_views.admin_tailoring_process, name='admin_tailoring_process'),
    path('admin-portal/computer/', admin_views.admin_computer_applications, name='admin_computer_list'),
    path('admin-portal/computer/<str:order_id>/', admin_views.admin_computer_detail, name='admin_computer_detail'),
    path('admin-portal/computer/<str:order_id>/process/', admin_views.admin_computer_process, name='admin_computer_process'),
    path('admin-portal/udyam/', admin_views.admin_udyam_applications, name='admin_udyam_list'),
    path('admin-portal/udyam/<str:order_id>/', admin_views.admin_udyam_detail, name='admin_udyam_detail'),
    path('admin-portal/udyam/<str:order_id>/process/', admin_views.admin_udyam_process, name='admin_udyam_process'),
    path('admin-portal/pvc-maker/', admin_views.admin_pvc_applications, name='admin_pvc_list'),
    path('admin-portal/pvc-maker/<str:order_id>/', admin_views.admin_pvc_detail, name='admin_pvc_detail'),
    path('admin-portal/pvc-maker/<str:order_id>/process/', admin_views.admin_pvc_process, name='admin_pvc_process'),
    path('admin-portal/cibil-score/', admin_views.admin_cibil_applications, name='admin_cibil_list'),
    path('admin-portal/cibil-score/<str:order_id>/', admin_views.admin_cibil_detail, name='admin_cibil_detail'),
    path('admin-portal/cibil-score/<str:order_id>/process/', admin_views.admin_cibil_process, name='admin_cibil_process'),
    path('admin-portal/aadhaar/', admin_views.admin_aadhaar_applications, name='admin_aadhaar_list'),
    path('admin-portal/aadhaar/<str:order_id>/', admin_views.admin_aadhaar_detail, name='admin_aadhaar_detail'),
    path('admin-portal/aadhaar/<str:order_id>/process/', admin_views.admin_aadhaar_process, name='admin_aadhaar_process'),
    path('admin-portal/eid-to-uid/', admin_views.admin_eid_applications, name='admin_eid_list'),
    path('admin-portal/eid-to-uid/<str:order_id>/', admin_views.admin_eid_detail, name='admin_eid_detail'),
    path('admin-portal/eid-to-uid/<str:order_id>/process/', admin_views.admin_eid_process, name='admin_eid_process'),
    path('admin-portal/lms-certificate/', admin_views.admin_lms_applications, name='admin_lms_list'),
    path('admin-portal/lms-certificate/<str:order_id>/', admin_views.admin_lms_detail, name='admin_lms_detail'),
    path('admin-portal/lms-certificate/<str:order_id>/process/', admin_views.admin_lms_process, name='admin_lms_process'),
    path('admin-portal/pan-to-aadhaar/', admin_views.admin_pan_to_aadhaar_applications, name='admin_pan_to_aadhaar_list'),
    path('admin-portal/pan-to-aadhaar/<str:order_id>/', admin_views.admin_pan_to_aadhaar_detail, name='admin_pan_to_aadhaar_detail'),
    path('admin-portal/pan-to-aadhaar/<str:order_id>/process/', admin_views.admin_pan_to_aadhaar_process, name='admin_pan_to_aadhaar_process'),
    path('admin-portal/govt-services/', admin_views.admin_govt_services_directory, name='admin_govt_services_list'),
    path('admin-portal/senior-citizen/', admin_views.admin_senior_applications, name='admin_senior_list'),
    path('admin-portal/senior-citizen/<str:order_id>/', admin_views.admin_senior_detail, name='admin_senior_detail'),
    path('admin-portal/senior-citizen/<str:order_id>/process/', admin_views.admin_senior_process, name='admin_senior_process'),

    # ── Gruha Laxmi ─────────────────────────────────────────
    path('services/kar-gov/gruha-laxmi/', views.gruha_laxmi_page, name='gruha_laxmi'),
    path('services/kar-gov/gruha-laxmi/submit/', views.gruha_laxmi_submit, name='gruha_laxmi_submit'),
    path('services/kar-gov/gruha-laxmi/list/', views.gruha_laxmi_list, name='gruha_laxmi_list'),
    path('services/kar-gov/gruha-laxmi/download/<str:order_id>/', views.gruha_laxmi_download, name='gruha_laxmi_download'),

    path('admin-portal/gruha-laxmi/', admin_views.admin_gruha_laxmi_applications, name='admin_gruha_laxmi_list'),
    path('admin-portal/gruha-laxmi/<str:order_id>/', admin_views.admin_gruha_laxmi_detail, name='admin_gruha_laxmi_detail'),
    path('admin-portal/gruha-laxmi/<str:order_id>/process/', admin_views.admin_gruha_laxmi_process, name='admin_gruha_laxmi_process'),

    # ── Gruha Laxmi Status ────────────────────────────────────
    path('services/kar-gov/gruha-laxmi-status/', views.gruha_laxmi_status_page, name='gruha_laxmi_status'),
    path('services/kar-gov/gruha-laxmi-status/submit/', views.gruha_laxmi_status_submit, name='gruha_laxmi_status_submit'),
    path('services/kar-gov/gruha-laxmi-status/list/', views.gruha_laxmi_status_list, name='gruha_laxmi_status_list'),
    path('services/kar-gov/gruha-laxmi-status/download/<str:order_id>/', views.gruha_laxmi_status_download, name='gruha_laxmi_status_download'),

    path('admin-portal/gruha-laxmi-status/', admin_views.admin_gruha_laxmi_status_applications, name='admin_gruha_laxmi_status_list'),
    path('admin-portal/gruha-laxmi-status/<str:order_id>/', admin_views.admin_gruha_laxmi_status_detail, name='admin_gruha_laxmi_status_detail'),
    path('admin-portal/gruha-laxmi-status/<str:order_id>/process/', admin_views.admin_gruha_laxmi_status_process, name='admin_gruha_laxmi_status_process'),

    # ── Gruha Laxmi KYC ───────────────────────────────────────
    path('services/kar-gov/gruha-laxmi-kyc/', views.gruha_laxmi_kyc_page, name='gruha_laxmi_kyc'),
    path('services/kar-gov/gruha-laxmi-kyc/submit/', views.gruha_laxmi_kyc_submit, name='gruha_laxmi_kyc_submit'),
    path('services/kar-gov/gruha-laxmi-kyc/list/', views.gruha_laxmi_kyc_list, name='gruha_laxmi_kyc_list'),
    path('services/kar-gov/gruha-laxmi-kyc/download/<str:order_id>/', views.gruha_laxmi_kyc_download, name='gruha_laxmi_kyc_download'),

    path('admin-portal/gruha-laxmi-kyc/', admin_views.admin_gruha_laxmi_kyc_applications, name='admin_gruha_laxmi_kyc_list'),
    path('admin-portal/gruha-laxmi-kyc/<str:order_id>/', admin_views.admin_gruha_laxmi_kyc_detail, name='admin_gruha_laxmi_kyc_detail'),
    path('admin-portal/gruha-laxmi-kyc/<str:order_id>/process/', admin_views.admin_gruha_laxmi_kyc_process, name='admin_gruha_laxmi_kyc_process'),

    # ── Gruha Laxmi Sanction Order ────────────────────────────
    path('services/kar-gov/gruha-laxmi-sanction/', views.gruha_laxmi_sanction_page, name='gruha_laxmi_sanction'),
    path('services/kar-gov/gruha-laxmi-sanction/submit/', views.gruha_laxmi_sanction_submit, name='gruha_laxmi_sanction_submit'),
    path('services/kar-gov/gruha-laxmi-sanction/list/', views.gruha_laxmi_sanction_list, name='gruha_laxmi_sanction_list'),
    path('services/kar-gov/gruha-laxmi-sanction/download/<str:order_id>/', views.gruha_laxmi_sanction_download, name='gruha_laxmi_sanction_download'),

    path('admin-portal/gruha-laxmi-sanction/', admin_views.admin_gruha_laxmi_sanction_applications, name='admin_gruha_laxmi_sanction_list'),
    path('admin-portal/gruha-laxmi-sanction/<str:order_id>/', admin_views.admin_gruha_laxmi_sanction_detail, name='admin_gruha_laxmi_sanction_detail'),
    path('admin-portal/gruha-laxmi-sanction/<str:order_id>/process/', admin_views.admin_gruha_laxmi_sanction_process, name='admin_gruha_laxmi_sanction_process'),

    # ── Gruha Jyothi ──────────────────────────────────────────
    path('services/kar-gov/gruha-jyothi/', views.gruha_jyothi_page, name='gruha_jyothi'),
    path('services/kar-gov/gruha-jyothi/submit/', views.gruha_jyothi_submit, name='gruha_jyothi_submit'),
    path('services/kar-gov/gruha-jyothi/list/', views.gruha_jyothi_list, name='gruha_jyothi_list'),
    path('services/kar-gov/gruha-jyothi/download/<str:order_id>/', views.gruha_jyothi_download, name='gruha_jyothi_download'),

    path('admin-portal/gruha-jyothi/', admin_views.admin_gruha_jyothi_applications, name='admin_gruha_jyothi_list'),
    path('admin-portal/gruha-jyothi/<str:order_id>/', admin_views.admin_gruha_jyothi_detail, name='admin_gruha_jyothi_detail'),
    path('admin-portal/gruha-jyothi/<str:order_id>/process/', admin_views.admin_gruha_jyothi_process, name='admin_gruha_jyothi_process'),

    # ── Gruha Jyothi D-Link ───────────────────────────────────
    path('services/kar-gov/gruha-jyothi-dlink/', views.gruha_jyothi_dlink_page, name='gruha_jyothi_dlink'),
    path('services/kar-gov/gruha-jyothi-dlink/submit/', views.gruha_jyothi_dlink_submit, name='gruha_jyothi_dlink_submit'),
    path('services/kar-gov/gruha-jyothi-dlink/list/', views.gruha_jyothi_dlink_list, name='gruha_jyothi_dlink_list'),
    path('services/kar-gov/gruha-jyothi-dlink/download/<str:order_id>/', views.gruha_jyothi_dlink_download, name='gruha_jyothi_dlink_download'),

    path('admin-portal/gruha-jyothi-dlink/', admin_views.admin_gruha_jyothi_dlink_applications, name='admin_gruha_jyothi_dlink_list'),
    path('admin-portal/gruha-jyothi-dlink/<str:order_id>/', admin_views.admin_gruha_jyothi_dlink_detail, name='admin_gruha_jyothi_dlink_detail'),
    path('admin-portal/gruha-jyothi-dlink/<str:order_id>/process/', admin_views.admin_gruha_jyothi_dlink_process, name='admin_gruha_jyothi_dlink_process'),

    # ── Bhoomi Pahani Link ────────────────────────────────────
    path('services/kar-gov/bhoomi-pahani-link/', views.bhoomi_pahani_link_page, name='bhoomi_pahani_link'),
    path('services/kar-gov/bhoomi-pahani-link/submit/', views.bhoomi_pahani_link_submit, name='bhoomi_pahani_link_submit'),
    path('services/kar-gov/bhoomi-pahani-link/list/', views.bhoomi_pahani_link_list, name='bhoomi_pahani_link_list'),
    path('services/kar-gov/bhoomi-pahani-link/download/<str:order_id>/', views.bhoomi_pahani_link_download, name='bhoomi_pahani_link_download'),

    path('admin-portal/bhoomi-pahani-link/', admin_views.admin_bhoomi_pahani_link_applications, name='admin_bhoomi_pahani_link_list'),
    path('admin-portal/bhoomi-pahani-link/<str:order_id>/', admin_views.admin_bhoomi_pahani_link_detail, name='admin_bhoomi_pahani_link_detail'),
    path('admin-portal/bhoomi-pahani-link/<str:order_id>/process/', admin_views.admin_bhoomi_pahani_link_process, name='admin_bhoomi_pahani_link_process'),

    # ── RTC Download ──────────────────────────────────────────
    path('services/kar-gov/rtc-download/', views.rtc_download_page, name='rtc_download'),
    path('services/kar-gov/rtc-download/submit/', views.rtc_download_submit, name='rtc_download_submit'),
    path('services/kar-gov/rtc-download/list/', views.rtc_download_list, name='rtc_download_list'),
    path('services/kar-gov/rtc-download/download/<str:order_id>/', views.rtc_download_pdf, name='rtc_download_pdf'),

    path('admin-portal/rtc-download/', admin_views.admin_rtc_download_applications, name='admin_rtc_download_list'),
    path('admin-portal/rtc-download/<str:order_id>/', admin_views.admin_rtc_download_detail, name='admin_rtc_download_detail'),
    path('admin-portal/rtc-download/<str:order_id>/process/', admin_views.admin_rtc_download_process, name='admin_rtc_download_process'),

    # ── ABHA Health Card ──────────────────────────────────────
    path('services/kar-gov/abha-card/', views.abha_card_page, name='abha_card'),
    path('services/kar-gov/abha-card/submit/', views.abha_card_submit, name='abha_card_submit'),
    path('services/kar-gov/abha-card/list/', views.abha_card_list, name='abha_card_list'),
    path('services/kar-gov/abha-card/download/<str:order_id>/', views.abha_card_download, name='abha_card_download'),

    path('admin-portal/abha-card/', admin_views.admin_abha_card_applications, name='admin_abha_card_list'),
    path('admin-portal/abha-card/<str:order_id>/', admin_views.admin_abha_card_detail, name='admin_abha_card_detail'),
    path('admin-portal/abha-card/<str:order_id>/process/', admin_views.admin_abha_card_process, name='admin_abha_card_process'),

    # ── Ayushman Bharat Card (₹100 Scheme) ────────────────────
    path('services/kar-gov/ayush-card/', views.ayush_card_page, name='ayush_card'),
    path('services/kar-gov/ayush-card/submit/', views.ayush_card_submit, name='ayush_card_submit'),
    path('services/kar-gov/ayush-card/list/', views.ayush_card_list, name='ayush_card_list'),
    path('services/kar-gov/ayush-card/download/<str:order_id>/', views.ayush_card_download, name='ayush_card_download'),

    path('admin-portal/ayush-card/', admin_views.admin_ayush_card_applications, name='admin_ayush_card_list'),
    path('admin-portal/ayush-card/<str:order_id>/', admin_views.admin_ayush_card_detail, name='admin_ayush_card_detail'),
    path('admin-portal/ayush-card/<str:order_id>/process/', admin_views.admin_ayush_card_process, name='admin_ayush_card_process'),

    # ── Ayushman Card Download Only Service ───────────────────
    path('services/kar-gov/ayush-download/', views.ayush_dwnld_page, name='ayush_dwnld'),
    path('services/kar-gov/ayush-download/submit/', views.ayush_dwnld_submit, name='ayush_dwnld_submit'),
    path('services/kar-gov/ayush-download/list/', views.ayush_dwnld_list, name='ayush_dwnld_list'),
    path('services/kar-gov/ayush-download/download/<str:order_id>/', views.ayush_dwnld_pdf, name='ayush_dwnld_pdf'),

    path('admin-portal/ayush-download/', admin_views.admin_ayush_dwnld_applications, name='admin_ayush_dwnld_list'),
    path('admin-portal/ayush-download/<str:order_id>/', admin_views.admin_ayush_dwnld_detail, name='admin_ayush_dwnld_detail'),
    path('admin-portal/ayush-download/<str:order_id>/process/', admin_views.admin_ayush_dwnld_process, name='admin_ayush_dwnld_process'),

    # ── e-Shram Card Registration Application ─────────────────
    path('services/kar-gov/eshram/', views.eshram_page, name='eshram'),
    path('services/kar-gov/eshram/submit/', views.eshram_submit, name='eshram_submit'),
    path('services/kar-gov/eshram/list/', views.eshram_list, name='eshram_list'),
    path('services/kar-gov/eshram/download/<str:order_id>/', views.eshram_download, name='eshram_download'),

    path('admin-portal/eshram/', admin_views.admin_eshram_applications, name='admin_eshram_list'),
    path('admin-portal/eshram/<str:order_id>/', admin_views.admin_eshram_detail, name='admin_eshram_detail'),
    path('admin-portal/eshram/<str:order_id>/process/', admin_views.admin_eshram_process, name='admin_eshram_process'),

    # ── e-Shram Card Download Only Application ─────────────────
    path('services/kar-gov/eshram-download/', views.eshram_dwnld_page, name='eshram_dwnld'),
    path('services/kar-gov/eshram-download/submit/', views.eshram_dwnld_submit, name='eshram_dwnld_submit'),
    path('services/kar-gov/eshram-download/list/', views.eshram_dwnld_list, name='eshram_dwnld_list'),
    path('services/kar-gov/eshram-download/download/<str:order_id>/', views.eshram_dwnld_pdf, name='eshram_dwnld_pdf'),

    path('admin-portal/eshram-download/', admin_views.admin_eshram_dwnld_applications, name='admin_eshram_dwnld_list'),
    path('admin-portal/eshram-download/<str:order_id>/', admin_views.admin_eshram_dwnld_detail, name='admin_eshram_dwnld_detail'),
    path('admin-portal/eshram-download/<str:order_id>/process/', admin_views.admin_eshram_dwnld_process, name='admin_eshram_dwnld_process'),

    # ── PM Kisan Services Application ─────────────────────────
    path('services/kar-gov/pmkisan/', views.pmkisan_page, name='pmkisan'),
    path('services/kar-gov/pmkisan/submit/', views.pmkisan_submit, name='pmkisan_submit'),
    path('services/kar-gov/pmkisan/list/', views.pmkisan_list, name='pmkisan_list'),
    path('services/kar-gov/pmkisan/download/<str:order_id>/', views.pmkisan_download, name='pmkisan_download'),

    path('admin-portal/pmkisan/', admin_views.admin_pmkisan_applications, name='admin_pmkisan_list'),
    path('admin-portal/pmkisan/<str:order_id>/', admin_views.admin_pmkisan_detail, name='admin_pmkisan_detail'),
    path('admin-portal/pmkisan/<str:order_id>/process/', admin_views.admin_pmkisan_process, name='admin_pmkisan_process'),

    # ── Naada Kacheri Certificate Download Application ─────────
    path('services/kar-gov/naadakacheri-download/', views.naadakacheri_dwnld_page, name='naadakacheri_dwnld'),
    path('services/kar-gov/naadakacheri-download/submit/', views.naadakacheri_dwnld_submit, name='naadakacheri_dwnld_submit'),
    path('services/kar-gov/naadakacheri-download/list/', views.naadakacheri_dwnld_list, name='naadakacheri_dwnld_list'),
    path('services/kar-gov/naadakacheri-download/download/<str:order_id>/', views.naadakacheri_dwnld_pdf, name='naadakacheri_dwnld_pdf'),

    path('admin-portal/naadakacheri-download/', admin_views.admin_naadakacheri_dwnld_applications, name='admin_naadakacheri_dwnld_list'),
    path('admin-portal/naadakacheri-download/<str:order_id>/', admin_views.admin_naadakacheri_dwnld_detail, name='admin_naadakacheri_dwnld_detail'),
    path('admin-portal/naadakacheri-download/<str:order_id>/process/', admin_views.admin_naadakacheri_dwnld_process, name='admin_naadakacheri_dwnld_process'),

    # ── Yuva Nidhi Scheme Application ─────────────────────────
    path('services/kar-gov/yuvanidhi/', views.yuvanidhi_page, name='yuvanidhi'),
    path('services/kar-gov/yuvanidhi/submit/', views.yuvanidhi_submit, name='yuvanidhi_submit'),
    path('services/kar-gov/yuvanidhi/list/', views.yuvanidhi_list, name='yuvanidhi_list'),
    path('services/kar-gov/yuvanidhi/download/<str:order_id>/', views.yuvanidhi_download, name='yuvanidhi_download'),

    path('admin-portal/yuvanidhi/', admin_views.admin_yuvanidhi_applications, name='admin_yuvanidhi_list'),
    path('admin-portal/yuvanidhi/<str:order_id>/', admin_views.admin_yuvanidhi_detail, name='admin_yuvanidhi_detail'),
    path('admin-portal/yuvanidhi/<str:order_id>/process/', admin_views.admin_yuvanidhi_process, name='admin_yuvanidhi_process'),

    # ── SSP Password Change Application ───────────────────────
    path('services/kar-gov/ssp-password-change/', views.ssp_password_page, name='ssp_password_page'),
    path('services/kar-gov/ssp-password-change/submit/', views.ssp_password_submit, name='ssp_password_submit'),
    path('services/kar-gov/ssp-password-change/list/', views.ssp_password_list, name='ssp_password_list'),
    path('services/kar-gov/ssp-password-change/download/<str:order_id>/', views.ssp_password_download, name='ssp_password_download'),

    path('admin-portal/ssp-password-change/', admin_views.admin_ssp_password_applications, name='admin_ssp_password_list'),
    path('admin-portal/ssp-password-change/<str:order_id>/', admin_views.admin_ssp_password_detail, name='admin_ssp_password_detail'),
    path('admin-portal/ssp-password-change/<str:order_id>/process/', admin_views.admin_ssp_password_process, name='admin_ssp_password_process'),

    # ── SSP Mobile Link Application ───────────────────────────
    path('services/kar-gov/ssp-mobile-link/', views.ssp_mobile_page, name='ssp_mobile_page'),
    path('services/kar-gov/ssp-mobile-link/submit/', views.ssp_mobile_submit, name='ssp_mobile_submit'),
    path('services/kar-gov/ssp-mobile-link/list/', views.ssp_mobile_list, name='ssp_mobile_list'),
    path('services/kar-gov/ssp-mobile-link/download/<str:order_id>/', views.ssp_mobile_download, name='ssp_mobile_download'),

    path('admin-portal/ssp-mobile-link/', admin_views.admin_ssp_mobile_applications, name='admin_ssp_mobile_list'),
    path('admin-portal/ssp-mobile-link/<str:order_id>/', admin_views.admin_ssp_mobile_detail, name='admin_ssp_mobile_detail'),
    path('admin-portal/ssp-mobile-link/<str:order_id>/process/', admin_views.admin_ssp_mobile_process, name='admin_ssp_mobile_process'),

    # ── Mobile to PAN Find (Surepass API) ─────────────────────
    path('services/pan/mobile-to-pan/', views.mobile_to_pan_page, name='mobile_to_pan_page'),
    path('services/pan/mobile-to-pan/submit/', views.mobile_to_pan_submit, name='mobile_to_pan_submit'),
    path('services/pan/mobile-to-pan/list/', views.mobile_to_pan_list, name='mobile_to_pan_list'),

    path('admin-portal/mobile-to-pan/', admin_views.admin_mobile_to_pan_applications, name='admin_mobile_to_pan_list'),
]
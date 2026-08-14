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
]
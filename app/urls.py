# Apne existing urls.py ko IS se replace karo

from django.urls import path
from . import views, vehicle_views
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
    path('logout/',    retailer_logout,    name='retailer_logout'),
    path('dashboard/', retailer_dashboard, name='retailer_dashboard'),

    # ── PAN App (existing) ─────────────────────────────────────────────
    path('pan/form/',             views.form,               name='form'),
    path('pan/applied-list/',     views.applied_list,       name='applied_list'),
    path('wallet/',                retailer_wallet,          name='wallet'),
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

    path('vehicle/driving-services/', vehicle_views.driving_services, name='driving_services'),
    path('vehicle/dl-allindia/', vehicle_views.dl_allindia_page, name='dl_allindia'),
    path('vehicle/dl-allindia/fetch/', vehicle_views.dl_allindia_api, name='dl_allindia_api'),
    path('vehicle/rc-allindia/', vehicle_views.vehicle_rc_page, name='vehicle_rc_allindia'),
    path('vehicle/rc/pdf/<str:order_id>/', vehicle_views.vehicle_rc_allindia_pdf, name='vehicle_rc_allindia_pdf'),
    path('vehicle/rc-allindia/pdf/<str:order_id>/', vehicle_views.vehicle_rc_allindia_pdf, name='vehicle_rc_allindia_pdf_alt'),
    path('vehicle/dl-karnataka/', vehicle_views.dl_karnataka_page, name='dl_karnataka'),
    path('vehicle/dl-karnataka/fetch/', vehicle_views.dl_karnataka_api, name='dl_karnataka_api'),
    path('vehicle/dl-karnataka/card/<str:order_id>/', vehicle_views.dl_karnataka_view_card, name='dl_karnataka_card'),
]
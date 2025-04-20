from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('book/<int:event_id>/', views.book_ticket, name='book_ticket'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('complete/<int:booking_id>/', views.complete_booking, name='complete_booking'),
    path('complete/', views.complete_booking, name='complete_booking_no_id'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<int:booking_id>/', views.ticket_detail, name='ticket_detail'),
    path('ticket/<int:booking_id>/cancel/', views.cancel_ticket, name='cancel_ticket'),
    path('ticket/<int:booking_id>/cancel-pending/', views.cancel_pending_booking, name='cancel_pending_booking'),
    path('delete-booking/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('payment/<str:order_id>/', views.payment_page, name='payment_page'),
    path('check-payment-status/<str:order_id>/', views.check_payment_status, name='check_payment_status'),
]
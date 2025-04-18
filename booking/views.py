from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from app.models import Event, EventSession, TicketType
from .models import Booking
import json
import logging
import hashlib
import hmac
import urllib
import urllib.parse
import urllib.request
import random
import requests
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from urllib.parse import quote as urlquote
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.db import connection
import qrcode
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

# Tạo một hàm riêng để sinh order_id
def generate_order_id(event_id, user_id):
    """Sinh mã order_id theo định dạng chuẩn"""
    user_part = user_id if user_id else 'GUEST'
    timestamp = timezone.now().strftime('%d%m%y%H%M%S')
    return f"EV{event_id}U{user_part}_T{timestamp}"

def book_ticket(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == "GET":
        session_id = request.GET.get('session')
        
        if session_id:
            session = get_object_or_404(EventSession, pk=session_id, event=event)
            ticket_types = TicketType.objects.filter(session=session)
        else:
            session = event.sessions.first()
            ticket_types = TicketType.objects.filter(session=session) if session else []
        
        return render(request, 'booking/book_ticket.html', {
            'event': event,
            'session': session,
            'ticket_types': ticket_types
        })
    elif request.method == "POST":
        session_id = request.POST.get('session_id')
        selected_tickets_json = request.POST.get('selected_tickets')
        order_id = request.POST.get('order_id')
        
        if not session_id or not selected_tickets_json:
            messages.error(request, "Thông tin đặt vé không hợp lệ.")
            return redirect('event_detail', event_id=event_id)
        
        try:
            selected_tickets = json.loads(selected_tickets_json)
            session = get_object_or_404(EventSession, pk=session_id, event=event)
            
            # Tạo booking mới hoặc tìm booking hiện có nếu có order_id
            if order_id:
                booking = get_object_or_404(Booking, order_id=order_id)
                # Kiểm tra nếu đã thanh toán thì chuyển đến trang hoàn tất
                if booking.payment_status == 'Paid':
                    return redirect('booking:complete_booking', booking_id=booking.id)
            else:
                # Tạo mã đơn hàng nếu chưa có
                order_id = generate_order_id(event.id, request.user.id if request.user.is_authenticated else None)

                # Tạo booking mới
                booking = Booking(
                    user=request.user if request.user.is_authenticated else None,
                    event=event,
                    session=session,
                    booking_date=timezone.now(),
                    payment_status='Pending',
                    order_id=order_id
                )
                booking.save()
            
            # Lưu chi tiết vé được đặt nếu là đơn hàng mới
            if booking.ticket_type is None:
                total_amount = 0
                total_quantity = 0
                
                # Hiện tại chỉ hỗ trợ một loại vé cho mỗi đơn hàng
                for ticket_id, quantity in selected_tickets.items():
                    ticket_type = get_object_or_404(TicketType, pk=ticket_id)
                    booking.ticket_type = ticket_type
                    booking.quantity = int(quantity)
                    total_amount += ticket_type.price * int(quantity)
                    total_quantity += int(quantity)
                
                booking.total_price = total_amount
                booking.save()
            
            # Chuyển đến trang thanh toán
            return render(request, 'booking/payment.html', {
                'booking': booking,
                'event': event,
                'session': session,
                'order_id': order_id
            })
            
        except Exception as e:
            logger.error(f"Error in booking: {str(e)}")
            messages.error(request, f"Lỗi khi xử lý đặt vé: {str(e)}")
            return redirect('event_detail', event_id=event_id)
    
    # Nếu có lỗi, hiển thị lại trang đặt vé
    session = event.sessions.first()
    ticket_types = TicketType.objects.filter(session=session) if session else []
    return render(request, 'booking/book_ticket.html', {
        'event': event,
        'session': session,
        'ticket_types': ticket_types
    })

@require_POST
def create_booking(request, event_id):
    """API endpoint để tạo hoặc lấy order_id cho booking"""
    if request.POST.get('get_order_id') == 'true':
        session_id = request.POST.get('session_id')
        selected_tickets_json = request.POST.get('selected_tickets')
        
        if not session_id or not selected_tickets_json:
            return JsonResponse({'success': False, 'message': 'Thông tin không hợp lệ'})
            
        try:
            # Logic tương tự như trong book_ticket
            selected_tickets = json.loads(selected_tickets_json)
            event = get_object_or_404(Event, pk=event_id)
            session = get_object_or_404(EventSession, pk=session_id, event=event)
            
            # Tạo order_id
            order_id = generate_order_id(event.id, request.user.id if request.user.is_authenticated else None)
            
            # Lưu booking vào database với trạng thái Pending
            booking = Booking(
                user=request.user if request.user.is_authenticated else None,
                event=event,
                session=session,
                booking_date=timezone.now(),
                payment_status='Pending',
                order_id=order_id
            )
            booking.save()
            
            # Lưu chi tiết vé
            total_amount = 0
            for ticket_id, quantity in selected_tickets.items():
                ticket_type = get_object_or_404(TicketType, pk=ticket_id)
                booking.ticket_type = ticket_type
                booking.quantity = int(quantity)
                total_amount += ticket_type.price * int(quantity)
            
            booking.total_price = total_amount
            booking.save()
            
            return JsonResponse({
                'success': True, 
                'order_id': order_id
            })
        except Exception as e:
            logger.error(f"Lỗi khi tạo booking: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_POST
def verify_payment(request):
    """API endpoint để xác thực thanh toán"""
    try:
        # Lấy order_id từ request
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu order_id'}, status=400)
        
        # Thêm logging để debug
        logger.info(f"Đang xác thực thanh toán với order_id: {order_id}")
        
        # Tìm booking tương ứng 
        try:
            # Thử tìm với order_id chính xác
            booking = Booking.objects.get(order_id=order_id)
            logger.info(f"Đã tìm thấy booking với order_id: {order_id}")
        except Booking.DoesNotExist:
            logger.warning(f"Không tìm thấy booking với order_id chính xác: {order_id}")
            
            # Thử các biến thể order_id
            found = False
            
            # Trường hợp 1: Nếu order_id không có dấu gạch dưới, thử thêm vào
            if 'U' in order_id and 'T' in order_id and '_T' not in order_id:
                try:
                    # Tìm vị trí của U và T để chèn dấu gạch dưới vào đúng vị trí
                    u_pos = order_id.find('U')
                    t_pos = order_id.find('T', u_pos)
                    if t_pos > 0:
                        modified_order_id = f"{order_id[:t_pos]}_{order_id[t_pos:]}"
                        logger.info(f"Thử tìm với order_id đã thêm dấu gạch: {modified_order_id}")
                        booking = Booking.objects.get(order_id=modified_order_id)
                        logger.info(f"Đã tìm thấy booking với order_id biến thể: {modified_order_id}")
                        found = True
                except Booking.DoesNotExist:
                    pass
            
            # Trường hợp 2: Nếu order_id có dấu gạch dưới, thử bỏ đi
            if not found and '_' in order_id:
                try:
                    modified_order_id = order_id.replace('_', '')
                    logger.info(f"Thử tìm với order_id đã bỏ dấu gạch: {modified_order_id}")
                    booking = Booking.objects.get(order_id=modified_order_id)
                    logger.info(f"Đã tìm thấy booking với order_id biến thể: {modified_order_id}")
                    found = True
                except Booking.DoesNotExist:
                    pass
            
            # Trường hợp 3: Tìm kiếm linh hoạt hơn - chỉ dùng phần EV và số phiên bản
            if not found and order_id.startswith('EV'):
                try:
                    ev_part = order_id.split('U')[0]  # Lấy phần "EV11"
                    # Tìm tất cả bookings bắt đầu bằng phần này
                    potential_bookings = Booking.objects.filter(order_id__startswith=ev_part)
                    if potential_bookings.exists():
                        # Lấy booking mới nhất
                        booking = potential_bookings.order_by('-booking_date').first()
                        logger.info(f"Dùng phương pháp tìm kiếm mở rộng, đã tìm thấy booking với order_id: {booking.order_id}")
                        found = True
                except Exception as e:
                    logger.error(f"Lỗi khi tìm kiếm mở rộng: {str(e)}")
            
            if not found:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Không tìm thấy booking với order_id: {order_id}. Vui lòng thử lại.'
                }, status=404)
        
        # Kiểm tra nếu booking đã thanh toán rồi thì trả về thành công luôn
        if booking.payment_status == 'Paid':
            return JsonResponse({
                'status': 'success',
                'message': 'Đơn hàng đã được thanh toán trước đó',
                'redirect_url': reverse('booking:complete_booking', args=[booking.id])
            })
        
        # TODO: Ở đây bạn có thể thêm logic xác thực thanh toán thực tế với API ngân hàng
        # Nếu thanh toán thành công, cập nhật trạng thái
        booking.payment_status = 'Paid'
        booking.payment_date = timezone.now()
        booking.save()
        
        # Cập nhật số lượng vé còn lại
        ticket_type = booking.ticket_type
        if ticket_type and ticket_type.available_quantity >= booking.quantity:
            ticket_type.available_quantity -= booking.quantity
            ticket_type.save()
        
        # Gửi email xác nhận đơn hàng
        try:
            send_booking_confirmation_email(booking)
        except Exception as e:
            logger.error(f"Không thể gửi email xác nhận: {str(e)}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thanh toán thành công',
            'redirect_url': reverse('booking:complete_booking', args=[booking.id])
        })
    except Exception as e:
        logger.error(f"Lỗi xác thực thanh toán: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def complete_booking(request, booking_id=None):
    """Trang hoàn tất đặt vé"""
    # Nếu không có booking_id, kiểm tra trong session
    if not booking_id:
        order_id = request.session.get('last_order_id')
        if order_id:
            try:
                booking = Booking.objects.get(order_id=order_id)
                return redirect('booking:complete_booking', booking_id=booking.id)
            except Booking.DoesNotExist:
                messages.error(request, "Không tìm thấy thông tin đặt vé.")
                return redirect('home')
        else:
            messages.error(request, "Không tìm thấy thông tin đặt vé.")
            return redirect('home')
    
    # Lấy thông tin booking
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Kiểm tra quyền truy cập
    if booking.user and booking.user != request.user:
        messages.error(request, "Bạn không có quyền xem thông tin đặt vé này.")
        return redirect('home')
    
    # Render trang hoàn tất đặt vé
    return render(request, 'booking/booking_complete.html', {
        'booking': booking,
        'event': booking.event,
        'session': booking.session,
    })

def send_booking_confirmation_email(booking):
    """Gửi email xác nhận đặt vé thành công"""
    subject = f'Xác nhận đặt vé: {booking.event.title}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booking.email
    
    # Chuẩn bị context cho template email
    context = {
        'booking': booking,
        'event': booking.event,
        'session': booking.session
    }
    
    # Tạo nội dung email (HTML)
    html_content = render_to_string('booking/email/booking_confirmation_email.html', context)
    text_content = strip_tags(html_content)  # Phiên bản text của email
    
    # Tạo email
    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    
    # Gửi email
    email.send()

@login_required
def my_tickets(request):
    """Hiển thị danh sách vé của người dùng đã đăng nhập"""
    # Lấy tất cả đơn đặt vé của người dùng hiện tại
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    
    # Phân loại theo trạng thái thanh toán
    paid_bookings = bookings.filter(payment_status='Paid')
    pending_bookings = bookings.filter(payment_status='Pending')
    cancelled_bookings = bookings.filter(payment_status__in=['Cancelled', 'Refunded'])
    
    # Phân loại theo thời gian sự kiện
    now = timezone.now()
    upcoming_events = []
    past_events = []
    
    for booking in paid_bookings:
        if booking.session.start_time > now:
            upcoming_events.append(booking)
        else:
            past_events.append(booking)
    
    context = {
        'paid_bookings': paid_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    
    return render(request, 'booking/my_tickets.html', context)

@login_required
def ticket_detail(request, booking_id):
    """Hiển thị chi tiết một vé"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Kiểm tra quyền truy cập (chỉ owner mới được xem)
    if booking.user != request.user:
        messages.error(request, "Bạn không có quyền xem thông tin đặt vé này.")
        return redirect('booking:my_tickets')
    
    return render(request, 'booking/ticket_detail.html', {
        'booking': booking,
        'event': booking.event,
        'session': booking.session
    })

@login_required
def cancel_ticket(request, booking_id):
    """Xử lý yêu cầu hủy vé"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Kiểm tra quyền truy cập (chỉ owner mới được hủy)
    if booking.user != request.user:
        messages.error(request, "Bạn không có quyền hủy vé này.")
        return redirect('booking:my_tickets')
    
    # Kiểm tra xem vé có thể hủy hay không
    if not booking.can_cancel:
        messages.error(request, "Vé này không thể hủy. Vui lòng kiểm tra điều kiện hủy vé.")
        return redirect('booking:ticket_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        reason = request.POST.get('cancel_reason', '')
        try:
            # Kiểm tra điều kiện hủy vé
            if booking.session.start_time <= timezone.now():
                messages.error(request, "Không thể hủy vé cho sự kiện đã diễn ra.")
                return redirect('booking:ticket_detail', booking_id=booking_id)
            
            # Tính số ngày còn lại trước khi sự kiện diễn ra
            remaining_days = (booking.session.start_time - timezone.now()).days
            
            # Tính toán tỷ lệ hoàn tiền
            if remaining_days > 7:
                refund_percentage = 0.8  # Hoàn 80% nếu hủy trước 7+ ngày
            else:
                refund_percentage = 0.5  # Hoàn 50% nếu hủy trong khoảng 3-7 ngày
            
            refund_amount = booking.total_price * refund_percentage
            
            # Cập nhật thông tin hủy vé
            booking.payment_status = 'Cancelled'
            booking.cancelled_at = timezone.now()
            booking.refund_amount = refund_amount
            booking.cancel_reason = reason
            booking.save()
            
            # Hoàn trả số lượng vé vào hệ thống
            if booking.ticket_type:
                booking.ticket_type.quantity += booking.quantity
                booking.ticket_type.save()
                
                logger.info(f"Đã hoàn trả {booking.quantity} vé loại {booking.ticket_type.name} vào hệ thống")
            
            # Gửi email thông báo hủy vé
            try:
                send_cancellation_email(booking)
            except Exception as e:
                logger.error(f"Lỗi khi gửi email hủy vé: {str(e)}")
            
            messages.success(request, f"Vé đã được hủy thành công. Bạn sẽ nhận được hoàn tiền {int(refund_percentage*100)}% ({int(refund_amount):,}đ) trong 3-5 ngày làm việc.")
            return redirect('booking:my_tickets')
            
        except Exception as e:
            logger.error(f"Lỗi khi hủy vé: {str(e)}")
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
            return redirect('booking:ticket_detail', booking_id=booking_id)
    
    # Hiển thị form xác nhận hủy vé
    return render(request, 'booking/cancel_ticket.html', {
        'booking': booking,
        'event': booking.event,
        'session': booking.session
    })

def send_cancellation_email(booking):
    """Gửi email xác nhận hủy vé"""
    if not booking.email:
        return
    
    subject = f"Xác nhận hủy vé - {booking.event.title}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booking.email
    
    # Tính toán tỷ lệ hoàn tiền
    refund_percentage = booking.refund_amount / booking.total_price * 100
    
    # Chuẩn bị context cho email template
    context = {
        'booking': booking,
        'event': booking.event,
        'session': booking.session,
        'refund_percentage': int(refund_percentage),
        'refund_amount': booking.refund_amount,
    }
    
    # Tạo nội dung email
    text_content = f"""
    Xin chào {booking.name},
    
    Yêu cầu hủy vé của bạn cho sự kiện {booking.event.title} đã được xử lý thành công.
    
    Thông tin đặt vé:
    - Mã đơn hàng: {booking.order_id}
    - Loại vé: {booking.ticket_type.name}
    - Số lượng: {booking.quantity} vé
    - Tổng tiền: {booking.total_price} đ
    - Số tiền hoàn lại: {booking.refund_amount} đ ({int(refund_percentage)}%)
    
    Số tiền hoàn lại sẽ được chuyển về tài khoản của bạn trong vòng 3-5 ngày làm việc.
    
    Trân trọng,
    MyTicket Team
    """
    
    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.send()
        logger.info(f"Đã gửi email xác nhận hủy vé cho {booking.email}")
    except Exception as e:
        logger.error(f"Lỗi khi gửi email: {str(e)}")
        raise







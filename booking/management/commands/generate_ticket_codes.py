from django.core.management.base import BaseCommand
from booking.models import Booking, BookingItem, Ticket
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tạo mã vé cho tất cả các booking item, bao gồm cả các đơn chưa thanh toán'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Tạo lại mã vé cho tất cả các booking item, kể cả đã có mã vé')
        parser.add_argument('--paid-only', action='store_true', help='Chỉ tạo mã vé cho các đơn hàng đã thanh toán')

    def handle(self, *args, **options):
        recreate_all = options['all']
        paid_only = options['paid_only']
        
        # Lấy tất cả các booking, có thể lọc theo trạng thái thanh toán
        if paid_only:
            bookings = Booking.objects.filter(payment_status='Paid')
            self.stdout.write(f"Tìm thấy {bookings.count()} booking đã thanh toán")
        else:
            bookings = Booking.objects.all()
            self.stdout.write(f"Tìm thấy {bookings.count()} booking (cả đã thanh toán và chưa thanh toán)")
        
        total_tickets_created = 0
        
        for booking in bookings:
            booking_items = booking.booking_items.all()
            
            # Hiển thị thông tin booking
            self.stdout.write(f"Xử lý booking ID: {booking.id}, Order ID: {booking.order_id}, Trạng thái: {booking.payment_status}")
            
            # Nếu không có booking items, thử tạo booking item cho ticket_type và quantity trong booking
            if not booking_items.exists() and booking.ticket_type and booking.quantity > 0:
                self.stdout.write(f"  Booking {booking.id} không có booking items, tạo từ thông tin khác")
                booking_item = BookingItem.objects.create(
                    booking=booking,
                    ticket_type=booking.ticket_type,
                    quantity=booking.quantity,
                    unit_price=booking.ticket_type.price,
                    subtotal=booking.ticket_type.price * booking.quantity
                )
                booking_items = [booking_item]
                
            for item in booking_items:
                # Kiểm tra xem đã có vé hay chưa
                existing_tickets = item.tickets.all()
                
                # Nếu đã có vé và không yêu cầu tạo lại, bỏ qua
                if existing_tickets.exists() and not recreate_all:
                    self.stdout.write(f"  Booking item {item.id} đã có {existing_tickets.count()} vé, bỏ qua")
                    continue
                
                # Nếu yêu cầu tạo lại, xóa vé cũ
                if existing_tickets.exists() and recreate_all:
                    self.stdout.write(f"  Xóa {existing_tickets.count()} vé cũ của booking item {item.id}")
                    existing_tickets.delete()
                
                # Tạo vé mới
                tickets_created = []
                for i in range(item.quantity):
                    ticket = Ticket(
                        booking_item=item,
                        ticket_code=Ticket.generate_ticket_code(),
                        is_used=False,
                        created_at=timezone.now()
                    )
                    ticket.save()
                    tickets_created.append(ticket)
                
                self.stdout.write(f"  Đã tạo {len(tickets_created)} vé cho booking item {item.id} (Loại: {item.ticket_type.name})")
                total_tickets_created += len(tickets_created)
        
        self.stdout.write(self.style.SUCCESS(f'Thành công! Đã tạo {total_tickets_created} vé mới'))
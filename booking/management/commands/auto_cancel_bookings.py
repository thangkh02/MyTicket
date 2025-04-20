import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from booking.models import Booking

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tự động hủy các đơn hàng chưa thanh toán sau 24 giờ'

    def handle(self, *args, **options):
        # Thời điểm 24 giờ trước
        deadline = timezone.now() - timedelta(hours=24)
        
        # Tìm các đơn hàng chưa thanh toán và đã tạo trước deadline
        pending_bookings = Booking.objects.filter(
            payment_status='Pending',
            booking_date__lt=deadline,
            cancelled_at__isnull=True
        )
        
        count = 0
        
        for booking in pending_bookings:
            try:
                # Cập nhật trạng thái đơn hàng thành đã hủy
                booking.payment_status = 'Cancelled'
                booking.cancelled_at = timezone.now()
                booking.cancel_reason = "Tự động hủy - quá 24h chưa thanh toán"
                booking.save()
                count += 1
                logger.info(f"Đã tự động hủy đơn hàng: {booking.order_id} (ID: {booking.id}) - " 
                           f"Đặt lúc: {booking.booking_date}")
                
            except Exception as e:
                logger.error(f"Lỗi khi hủy đơn hàng {booking.order_id}: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Đã tự động hủy {count} đơn hàng chưa thanh toán quá 24 giờ.')
        )
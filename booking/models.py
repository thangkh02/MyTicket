from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from app.models import Event, TicketType, EventSession
import uuid

class Booking(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Đang chờ thanh toán'),
        ('Paid', 'Đã thanh toán'),
        ('Failed', 'Thanh toán thất bại'),
        ('Cancelled', 'Đã hủy'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='booking_events', null=True, blank=True)
    session = models.ForeignKey(EventSession, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='booking_tickets', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Họ tên")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=15, verbose_name="Số điện thoại")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng vé")
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, default="Pending", choices=PAYMENT_STATUS_CHOICES)
    
    # Thêm các trường mới để lưu thông tin thanh toán
    total_price = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Tổng tiền")
    order_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mã đơn hàng")
    payment_method = models.CharField(max_length=50, blank=True, null=True, verbose_name="Phương thức thanh toán")
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name="Thời gian thanh toán")
    
    # Các trường bổ sung cho đơn hàng hủy
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name="Thời gian hủy")
    refund_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Số tiền hoàn lại")
    cancel_reason = models.TextField(blank=True, null=True, verbose_name="Lý do hủy")
    
    def __str__(self):
        ticket_info = f"{self.ticket_type.name}" if self.ticket_type else ""
        event_info = f"{self.event.title}" if self.event else ""
        return f"{self.name} - {event_info} {ticket_info} ({self.quantity} vé)"
    
    def save(self, *args, **kwargs):
        # Tự động tính tổng giá nếu chưa được đặt
        if self.ticket_type and not self.total_price:
            self.total_price = self.ticket_type.price * self.quantity
        super().save(*args, **kwargs)
    
    def mark_as_paid(self):
        """Đánh dấu đơn hàng đã thanh toán thành công"""
        self.payment_status = 'Paid'
        self.payment_date = timezone.now()
        self.save()
    
    @property
    def can_cancel(self):
        """Kiểm tra xem vé có thể hủy không (chỉ có thể hủy trước 3 ngày)"""
        if not self.session or self.payment_status != 'Paid':
            return False
        
        # Chỉ cho phép hủy vé nếu còn ít nhất 3 ngày trước khi sự kiện diễn ra
        now = timezone.now()
        time_diff = self.session.start_time - now
        return time_diff.days >= 3
    
    @property
    def get_booking_items(self):
        """Lấy các BookingItem thuộc booking này"""
        return self.booking_items.all()
    
    @property
    def get_total_quantity(self):
        """Tính tổng số lượng vé từ các booking items"""
        return self.booking_items.aggregate(total=models.Sum('quantity'))['total'] or 0


class BookingItem(models.Model):
    """
    Model để lưu trữ chi tiết của từng loại vé trong đơn hàng
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_items')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='booking_items')
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    unit_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Đơn giá")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Thành tiền")
    
    def __str__(self):
        return f"{self.ticket_type.name} x {self.quantity} ({self.booking.order_id})"
    
    def save(self, *args, **kwargs):
        # Tự động tính thành tiền
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Ticket(models.Model):
    """
    Model để lưu trữ thông tin của từng vé cụ thể trong đơn hàng
    """
    booking_item = models.ForeignKey(BookingItem, on_delete=models.CASCADE, related_name='tickets')
    ticket_code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.ticket_code
    
    @staticmethod
    def generate_ticket_code():
        """Tạo mã vé duy nhất với định dạng cải tiến"""
        import uuid
        import time
        from datetime import datetime
        
        # Tạo tiền tố dựa trên ngày hiện tại (định dạng: YYMM)
        date_prefix = datetime.now().strftime('%y%m')
        
        # Tạo hậu tố ngẫu nhiên (8 ký tự)
        random_suffix = uuid.uuid4().hex[:8].upper()
        
        # Tạo mã vé với định dạng: TIX-YYMM-XXXXXXXX
        ticket_code = f"TIX-{date_prefix}-{random_suffix}"
        
        # Kiểm tra xem mã đã tồn tại trong database chưa
        while Ticket.objects.filter(ticket_code=ticket_code).exists():
            # Nếu đã tồn tại, tạo mã mới
            time.sleep(0.01)  # Tạm dừng để đảm bảo mã mới khác với mã cũ
            random_suffix = uuid.uuid4().hex[:8].upper()
            ticket_code = f"TIX-{date_prefix}-{random_suffix}"
        
        return ticket_code

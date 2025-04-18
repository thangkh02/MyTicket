from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from app.models import Event, TicketType, EventSession

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

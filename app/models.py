from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Event(models.Model):
    CATEGORY_CHOICES = [
        ('concert', 'Âm nhạc'),
        ('theater', 'Sân khấu & Nghệ Thuật'),
        ('sports', 'Thể thao'),
        ('conference', ''),
        ('other', 'Khác'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Tên sự kiện")
    description = models.TextField(verbose_name="Mô tả")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', verbose_name="Thể loại")
    location = models.CharField(max_length=200, verbose_name="Địa điểm")
    image = models.ImageField(upload_to='events/', blank=True, null=True, verbose_name="Ảnh sự kiện")
    
    def __str__(self):
        return self.title
        
    @property
    def earliest_date(self):
        session = self.sessions.order_by('start_time').first()
        return session.start_time if session else None
        
    @property
    def lowest_price(self):
        sessions = self.sessions.all()
        min_price = None
        for session in sessions:
            ticket_types = session.ticket_types.all()
            for ticket in ticket_types:
                if min_price is None or ticket.price < min_price:
                    min_price = ticket.price
        return min_price

class EventSession(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions', verbose_name="Sự kiện")
    start_time = models.DateTimeField(verbose_name="Thời gian bắt đầu")
    end_time = models.DateTimeField(verbose_name="Thời gian kết thúc", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    class Meta:
        verbose_name = "Mốc thời gian"
        verbose_name_plural = "Mốc thời gian"
        ordering = ['start_time']

    def __str__(self):
        return f"{self.event.title} - {self.start_time.strftime('%d/%m/%Y %H:%M')}"

    @property
    def is_past(self):
        return self.end_time < timezone.now()

    @property
    def is_upcoming(self):
        return self.start_time > timezone.now()

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class TicketType(models.Model):
    session = models.ForeignKey(EventSession, on_delete=models.CASCADE, related_name='ticket_types', verbose_name="Mốc thời gian")
    name = models.CharField(max_length=100, verbose_name="Tên loại vé")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá vé")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")

    quantity = models.PositiveIntegerField(default=100, verbose_name="Số lượng vé")
    min_quantity_per_order = models.PositiveIntegerField(default=1, verbose_name="Số lượng vé tối thiểu mỗi đơn")
    max_quantity_per_order = models.PositiveIntegerField(default=10, verbose_name="Số lượng vé tối đa mỗi đơn")

    sale_start_time = models.DateTimeField(verbose_name="Thời gian bắt đầu bán vé", default=timezone.now)
    sale_end_time = models.DateTimeField(verbose_name="Thời gian kết thúc bán vé")

    ticket_info = models.TextField(blank=True, null=True, verbose_name="Thông tin vé bổ sung")
    ticket_image = models.ImageField(upload_to='tickets/images/', verbose_name="Hình ảnh vé", blank=True, null=True)

    class Meta:
        verbose_name = "Loại vé"
        verbose_name_plural = "Loại vé"

    def __str__(self):
        return f"{self.name} - {self.session.event.title} ({self.session.start_time.strftime('%d/%m/%Y')})"

    @property
    def available_quantity(self):
        from django.db.models import Sum
        from booking.models import Booking
        sold = Booking.objects.filter(ticket_type=self, payment_status='Paid').aggregate(Sum('quantity'))['quantity__sum'] or 0
        return self.quantity - sold

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Nam'),
        ('F', 'Nữ'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Ngày sinh")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="Giới tính")
    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ")

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Event, EventSession, TicketType
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Creates sample data for events, sessions, and ticket types'

    def handle(self, *args, **kwargs):
        # Tạo sự kiện âm nhạc
        music_event = Event.objects.create(
            title='Concert Hà Nội 2025',
            description='Buổi hòa nhạc đặc biệt với các nghệ sĩ nổi tiếng',
            location='Nhà hát lớn Hà Nội',
            category='music',
            image='events/concert.jpg'
        )
        
        # Tạo các buổi diễn cho sự kiện âm nhạc
        for i in range(3):
            start_time = timezone.now() + timedelta(days=random.randint(1, 30))
            session = EventSession.objects.create(
                event=music_event,
                start_time=start_time,
                end_time=start_time + timedelta(hours=3)
            )
            
            # Tạo các loại vé cho mỗi buổi diễn
            TicketType.objects.create(
                session=session,
                name='VIP',
                price=1000000,
                quantity=50,
                sale_start_time=timezone.now(),
                sale_end_time=start_time - timedelta(days=1)
            )
            
            TicketType.objects.create(
                session=session,
                name='Thường',
                price=500000,
                quantity=200,
                sale_start_time=timezone.now(),
                sale_end_time=start_time - timedelta(days=1)
            )

        # Tạo sự kiện thể thao
        sports_event = Event.objects.create(
            title='Giải bóng đá vô địch quốc gia 2025',
            description='Giải đấu bóng đá chuyên nghiệp hàng đầu Việt Nam',
            location='Sân vận động Mỹ Đình',
            category='sports',
            image='events/football.jpg'
        )
        
        # Tạo các buổi diễn cho sự kiện thể thao và các loại vé tương ứng
        # ... tương tự như trên
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Họ tên')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('phone', models.CharField(max_length=15, verbose_name='Số điện thoại')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Số lượng vé')),
                ('booking_date', models.DateTimeField(auto_now_add=True)),
                ('payment_status', models.CharField(choices=[('Pending', 'Đang chờ thanh toán'), ('Paid', 'Đã thanh toán'), ('Cancelled', 'Đã hủy')], default='Pending', max_length=20)),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='booking_events', to='app.event')),
                ('ticket_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='booking_tickets', to='app.tickettype')),
            ],
        ),
    ]

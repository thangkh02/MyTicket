# Generated by Django 5.1.7 on 2025-04-17 16:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_alter_event_category_alter_eventsession_event'),
        ('booking', '0003_remove_booking_vnpay_bank_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='order_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Mã đơn hàng'),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Thời gian thanh toán'),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_method',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Phương thức thanh toán'),
        ),
        migrations.AddField(
            model_name='booking',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='app.eventsession'),
        ),
        migrations.AddField(
            model_name='booking',
            name='total_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name='Tổng tiền'),
        ),
    ]

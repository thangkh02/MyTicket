from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('booking', '0005_add_session_field'),  # Điều chỉnh theo migration cuối cùng của bạn
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL - Thêm các cột còn thiếu
            """
            ALTER TABLE booking_booking 
            ADD COLUMN total_price decimal(12, 0) NOT NULL DEFAULT 0;
            
            ALTER TABLE booking_booking 
            ADD COLUMN order_id varchar(100) NULL;
            
            ALTER TABLE booking_booking 
            ADD COLUMN payment_method varchar(50) NULL;
            
            ALTER TABLE booking_booking 
            ADD COLUMN payment_date datetime NULL;
            
            ALTER TABLE booking_booking 
            ADD COLUMN cancelled_at datetime NULL;
            
            ALTER TABLE booking_booking 
            ADD COLUMN cancel_reason text NULL;
            
            ALTER TABLE booking_booking 
            ADD COLUMN refund_amount decimal(12, 0) NULL;
            """,
            
            # Reverse SQL - Xóa các cột nếu rollback
            """
            ALTER TABLE booking_booking DROP COLUMN total_price;
            ALTER TABLE booking_booking DROP COLUMN order_id;
            ALTER TABLE booking_booking DROP COLUMN payment_method;
            ALTER TABLE booking_booking DROP COLUMN payment_date;
            ALTER TABLE booking_booking DROP COLUMN cancelled_at;
            ALTER TABLE booking_booking DROP COLUMN cancel_reason;
            ALTER TABLE booking_booking DROP COLUMN refund_amount;
            """
        ),
    ]
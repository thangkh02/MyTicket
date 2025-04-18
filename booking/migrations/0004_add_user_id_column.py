from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),  # Điều chỉnh nếu cần
        ('booking', '0003_add_user_field_again'),  # Điều chỉnh theo migration cuối cùng của bạn
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL - Thêm cột user_id
            """
            ALTER TABLE booking_booking 
            ADD COLUMN user_id integer NULL 
            REFERENCES auth_user(id) ON DELETE SET NULL;
            """,
            
            # Reverse SQL - Xóa cột nếu rollback
            """
            ALTER TABLE booking_booking 
            DROP COLUMN user_id;
            """
        ),
    ]
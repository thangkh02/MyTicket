from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0001_initial'), 
        ('booking', '0004_add_user_id_column'),  
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL - Thêm cột session_id
            """
            ALTER TABLE booking_booking 
            ADD COLUMN session_id integer NULL 
            REFERENCES app_eventsession(id) ON DELETE SET NULL;
            """,
            
      
            """
            ALTER TABLE booking_booking 
            DROP COLUMN session_id;
            """
        ),
    ]
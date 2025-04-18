from django.db import migrations

def clean_duplicate_sessions(apps, schema_editor):
    """
    Giữ lại session đầu tiên cho mỗi Event, xóa các session khác
    """
    Event = apps.get_model('app', 'Event')
    EventSession = apps.get_model('app', 'EventSession')
    
    # Lặp qua từng Event
    for event in Event.objects.all():
        # Lấy tất cả các session của Event
        sessions = EventSession.objects.filter(event=event).order_by('start_time')
        
        # Nếu có nhiều hơn 1 session
        if sessions.count() > 1:
            # Giữ lại session đầu tiên
            first_session = sessions.first()
            # Xóa tất cả các session khác
            sessions.exclude(id=first_session.id).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_alter_eventsession_event'),  # Thay thế bằng migration trước đó
    ]

    operations = [
        migrations.RunPython(clean_duplicate_sessions),
    ]
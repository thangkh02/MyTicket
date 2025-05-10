from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count, Sum, Q
from app.models import Event, EventSession, TicketType
from booking.models import Booking, BookingItem
import datetime
from django.forms import modelform_factory, inlineformset_factory, TextInput, Textarea, Select, DateTimeInput, ClearableFileInput, NumberInput

@login_required(login_url='/admin-custom/login/')
def dashboard(request):
    """
    Hiển thị trang dashboard của admin tùy chỉnh
    """
    # Thống kê tổng quan
    total_events = Event.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.filter(payment_status='Paid').aggregate(Sum('total_price'))['total_price__sum'] or 0
    recent_bookings = Booking.objects.order_by('-booking_date')[:5]
    
    # Sự kiện sắp diễn ra
    today = datetime.date.today()
    upcoming_events = Event.objects.filter(
        sessions__start_time__date__gte=today
    ).distinct().order_by('sessions__start_time')[:5]
    
    context = {
        'total_events': total_events,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'admin_custom/dashboard.html', context)

def admin_login(request):
    """
    Xử lý đăng nhập vào admin tùy chỉnh
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_custom:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_custom:dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    
    return render(request, 'admin_custom/login.html')

@login_required(login_url='/admin-custom/login/')
def admin_logout(request):
    """
    Xử lý đăng xuất khỏi admin tùy chỉnh
    """
    logout(request)
    return redirect('admin_custom:login')

@login_required(login_url='/admin-custom/login/')
def event_list(request):
    """
    Hiển thị danh sách sự kiện
    """
    events = Event.objects.all().order_by('-id')
    
    # Tìm kiếm
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) | 
            Q(location__icontains=search_query) |
            Q(organizer_name__icontains=search_query)
        )
    
    context = {
        'events': events,
        'search_query': search_query
    }
    return render(request, 'admin_custom/event_list.html', context)

@login_required(login_url='/admin-custom/login/')
def event_detail(request, event_id):
    """
    Hiển thị chi tiết sự kiện
    """
    event = get_object_or_404(Event, id=event_id)
    sessions = event.sessions.all()
    
    # Tính tổng số vé đã bán và doanh thu
    ticket_sold = BookingItem.objects.filter(
        ticket_type__session__event=event, 
        booking__payment_status='Paid'
    ).count()
    
    revenue = BookingItem.objects.filter(
        ticket_type__session__event=event, 
        booking__payment_status='Paid'
    ).aggregate(Sum('subtotal'))['subtotal__sum'] or 0
    
    # Lấy thông tin đặt vé cho sự kiện này
    booking_items = BookingItem.objects.filter(
        ticket_type__session__event=event
    ).select_related('booking', 'ticket_type', 'ticket_type__session')
    
    context = {
        'event': event,
        'sessions': sessions,
        'ticket_sold': ticket_sold,
        'revenue': revenue,
        'booking_items': booking_items
    }
    return render(request, 'admin_custom/event_detail.html', context)

@login_required(login_url='/admin-custom/login/')
def event_create(request):
    """
    Tạo sự kiện mới
    """
    EventForm = modelform_factory(Event, fields=[
        'title', 'description', 'category', 'location', 'image',
        'organizer_name', 'organizer_description', 'organizer_logo', 'description_image'
    ], widgets={
        'title': TextInput(attrs={'class': 'form-control'}),
        'description': Textarea(attrs={'class': 'form-control wysiwyg-editor', 'rows': 10}),
        'category': Select(attrs={'class': 'form-select'}),
        'location': TextInput(attrs={'class': 'form-control'}),
        'image': ClearableFileInput(attrs={'class': 'form-control'}),
        'organizer_name': TextInput(attrs={'class': 'form-control'}),
        'organizer_description': Textarea(attrs={'class': 'form-control wysiwyg-editor', 'rows': 5}),
        'organizer_logo': ClearableFileInput(attrs={'class': 'form-control'}),
        'description_image': ClearableFileInput(attrs={'class': 'form-control'})
    })
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Sự kiện "{event.title}" đã được tạo thành công.')
            return redirect('admin_custom:event_detail', event_id=event.id)
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'title': 'Thêm sự kiện mới'
    }
    return render(request, 'admin_custom/event_form.html', context)

@login_required(login_url='/admin-custom/login/')
def event_edit(request, event_id):
    """
    Chỉnh sửa sự kiện 
    """
    event = get_object_or_404(Event, id=event_id)
    
    EventForm = modelform_factory(Event, fields=[
        'title', 'description', 'category', 'location', 'image',
        'organizer_name', 'organizer_description', 'organizer_logo', 'description_image'
    ], widgets={
        'title': TextInput(attrs={'class': 'form-control'}),
        'description': Textarea(attrs={'class': 'form-control wysiwyg-editor', 'rows': 10}),
        'category': Select(attrs={'class': 'form-select'}),
        'location': TextInput(attrs={'class': 'form-control'}),
        'image': ClearableFileInput(attrs={'class': 'form-control'}),
        'organizer_name': TextInput(attrs={'class': 'form-control'}),
        'organizer_description': Textarea(attrs={'class': 'form-control wysiwyg-editor', 'rows': 5}),
        'organizer_logo': ClearableFileInput(attrs={'class': 'form-control'}),
        'description_image': ClearableFileInput(attrs={'class': 'form-control'})
    })
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Sự kiện "{event.title}" đã được cập nhật thành công.')
            return redirect('admin_custom:event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'title': f'Chỉnh sửa sự kiện: {event.title}'
    }
    return render(request, 'admin_custom/event_form.html', context)

@login_required(login_url='/admin-custom/login/')
def event_delete(request, event_id):
    """
    Xóa sự kiện
    """
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Sự kiện "{event_title}" đã được xóa thành công.')
        return redirect('admin_custom:event_list')
    
    # Nếu không phải POST request, redirect về trang chi tiết sự kiện
    return redirect('admin_custom:event_detail', event_id=event.id)

@login_required(login_url='/admin-custom/login/')
def session_create(request, event_id):
    """
    Thêm mốc thời gian mới cho sự kiện
    """
    event = get_object_or_404(Event, id=event_id)
    
    SessionForm = modelform_factory(EventSession, exclude=['event'], widgets={
        'start_time': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        'end_time': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        'is_active': Select(attrs={'class': 'form-select'}, choices=[(True, 'Có'), (False, 'Không')])
    })
    
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.event = event
            session.save()
            messages.success(request, f'Mốc thời gian mới đã được thêm cho sự kiện "{event.title}".')
            return redirect('admin_custom:event_detail', event_id=event.id)
    else:
        form = SessionForm()
    
    context = {
        'form': form,
        'event': event,
        'title': f'Thêm mốc thời gian cho: {event.title}'
    }
    return render(request, 'admin_custom/session_form.html', context)

@login_required(login_url='/admin-custom/login/')
def session_edit(request, session_id):
    """
    Chỉnh sửa mốc thời gian của sự kiện
    """
    session = get_object_or_404(EventSession, id=session_id)
    event = session.event
    
    SessionForm = modelform_factory(EventSession, exclude=['event'], widgets={
        'start_time': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        'end_time': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        'is_active': Select(attrs={'class': 'form-select'}, choices=[(True, 'Có'), (False, 'Không')])
    })
    
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, f'Mốc thời gian đã được cập nhật.')
            return redirect('admin_custom:event_detail', event_id=event.id)
    else:
        form = SessionForm(instance=session)
    
    context = {
        'form': form,
        'event': event,
        'session': session,
        'title': f'Chỉnh sửa mốc thời gian: {session}'
    }
    return render(request, 'admin_custom/session_form.html', context)

@login_required(login_url='/admin-custom/login/')
def ticket_type_create(request, session_id):
    """
    Thêm loại vé mới cho mốc thời gian
    """
    session = get_object_or_404(EventSession, id=session_id)
    event = session.event
    
    TicketTypeForm = modelform_factory(TicketType, exclude=['session'], widgets={
        'name': TextInput(attrs={'class': 'form-control'}),
        'price': NumberInput(attrs={'class': 'form-control'}),
        'description': Textarea(attrs={'class': 'form-control wysiwyg-editor', 'rows': 3}),
        'quantity': NumberInput(attrs={'class': 'form-control'}),
        'min_quantity_per_order': NumberInput(attrs={'class': 'form-control'})
    })
    
    if request.method == 'POST':
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            ticket_type = form.save(commit=False)
            ticket_type.session = session
            ticket_type.save()
            messages.success(request, f'Loại vé "{ticket_type.name}" đã được thêm thành công.')
            return redirect('admin_custom:event_detail', event_id=event.id)
    else:
        form = TicketTypeForm()
    
    context = {
        'form': form,
        'event': event,
        'session': session,
        'title': f'Thêm loại vé cho: {session}'
    }
    return render(request, 'admin_custom/ticket_type_form.html', context)

@login_required(login_url='/admin-custom/login/')
def ticket_type_edit(request, ticket_type_id):
    """
    Chỉnh sửa loại vé
    """
    ticket_type = get_object_or_404(TicketType, id=ticket_type_id)
    session = ticket_type.session
    event = session.event
    TicketTypeForm = modelform_factory(TicketType, exclude=['session'], widgets={
        'name': TextInput(attrs={'class': 'form-control'}),
        'price': NumberInput(attrs={'class': 'form-control'}),
        'description': Textarea(attrs={'class': 'form-control wysiwyg-editor', 'rows': 3}),
        'quantity': NumberInput(attrs={'class': 'form-control'}),
        'min_quantity_per_order': NumberInput(attrs={'class': 'form-control'})
    })
    
    if request.method == 'POST':
        form = TicketTypeForm(request.POST, instance=ticket_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Loại vé "{ticket_type.name}" đã được cập nhật.')
            return redirect('admin_custom:event_detail', event_id=event.id)
    else:
        form = TicketTypeForm(instance=ticket_type)
    
    context = {
        'form': form,
        'event': event,
        'session': session,
        'ticket_type': ticket_type,
        'title': f'Chỉnh sửa loại vé: {ticket_type.name}'
    }
    return render(request, 'admin_custom/ticket_type_form.html', context)

@login_required(login_url='/admin-custom/login/')
def booking_list(request):
    """
    Hiển thị danh sách đặt vé
    """
    bookings = Booking.objects.all().order_by('-booking_date')
    
    # Lọc theo trạng thái
    status = request.GET.get('status', '')
    if status:
        bookings = bookings.filter(payment_status=status)
    
    context = {
        'bookings': bookings,
        'current_status': status
    }
    return render(request, 'admin_custom/booking_list.html', context)

@login_required(login_url='/admin-custom/login/')
def booking_detail(request, booking_id):
    """
    Hiển thị chi tiết đặt vé và cập nhật trạng thái đơn
    """
    booking = get_object_or_404(Booking, id=booking_id)
    booking_items = booking.booking_items.all()
    # Xử lý cập nhật trạng thái
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'complete':
            booking.payment_status = 'Paid'
            booking.payment_date = datetime.datetime.now()
            booking.save()
            messages.success(request, f'Đơn hàng #{booking.id} đã được đánh dấu là hoàn thành.')
        elif action == 'cancel':
            booking.payment_status = 'Cancelled'
            booking.cancelled_at = datetime.datetime.now()
            booking.save()
            messages.success(request, f'Đơn hàng #{booking.id} đã được hủy.')
        return redirect('admin_custom:booking_detail', booking_id=booking.id)
    
    context = {
        'booking': booking,
        'booking_items': booking_items
    }
    return render(request, 'admin_custom/booking_detail.html', context)

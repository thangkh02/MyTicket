from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import connection
import logging
from .forms import LoginForm, RegisterForm
from booking.models import Booking
from .models import Event, UserProfile
from django.urls import reverse
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def home_view(request):
    try:
        # Lấy các tham số từ request
        search_query = request.GET.get('q', '')
        category_filter = request.GET.get('category', '')
        
        # Xác định tên hiển thị cho thể loại
        category_display_map = {
            'concert': 'Âm nhạc',
            'theater': 'Sân khấu & Nghệ thuật',
            'sports': 'Thể thao',
            'conference': 'Hội nghị',
            'other': 'Khác',
        }
        active_category_display = category_display_map.get(category_filter, '')
        
        # Truy vấn sự kiện sắp diễn ra và đang mở bán
        now = timezone.now()
        upcoming_events = Event.objects.filter(
            sessions__start_time__gte=now,
            sessions__is_active=True
        ).distinct().order_by('sessions__start_time')
        
        # Truy vấn banner sự kiện - lấy 4 sự kiện sắp diễn ra gần nhất
        banner_events = upcoming_events[:4]
        
        # Truy vấn sự kiện nổi bật - lấy 3 sự kiện tiếp theo
        featured_events = upcoming_events[4:7] if len(upcoming_events) > 4 else []
        
        # Xử lý tìm kiếm và lọc thể loại
        search_results = []
        if search_query or category_filter:
            base_query = Event.objects.filter(
                sessions__start_time__gte=now,
                sessions__is_active=True
            ).distinct()
            
            # Áp dụng bộ lọc tìm kiếm nếu có
            if search_query:
                base_query = base_query.filter(
                    Q(title__icontains=search_query) | 
                    Q(description__icontains=search_query) | 
                    Q(location__icontains=search_query)
                )
            
            # Áp dụng bộ lọc thể loại nếu có
            if category_filter:
                base_query = base_query.filter(category=category_filter)
                
            # Sắp xếp kết quả và giới hạn số lượng
            search_results = base_query.order_by('sessions__start_time')[:12]
            
            # Nếu đang lọc theo thể loại hoặc tìm kiếm, không cần hiển thị các phần theo thể loại
            music_events = []
            arts_events = []
            sports_events = []
            other_events = []
        else:
            # Sự kiện theo từng loại - chỉ hiển thị khi không có tìm kiếm/lọc
            # Đảm bảo ID duy nhất và sắp xếp theo thời gian bắt đầu sớm nhất
            music_events = Event.objects.filter(
                category='concert', 
                sessions__start_time__gte=now,
                sessions__is_active=True
            ).distinct().order_by('sessions__start_time')[:4]
            
            arts_events = Event.objects.filter(
                category='theater', 
                sessions__start_time__gte=now,
                sessions__is_active=True
            ).distinct().order_by('sessions__start_time')[:4]
            
            sports_events = Event.objects.filter(
                category='sports', 
                sessions__start_time__gte=now,
                sessions__is_active=True
            ).distinct().order_by('sessions__start_time')[:4]
            
            other_events = Event.objects.filter(
                category='other', 
                sessions__start_time__gte=now,
                sessions__is_active=True
            ).distinct().order_by('sessions__start_time')[:4]
        
        # Thêm tham số để biết đây là trang lọc hay trang chủ
        is_filtered = 'category' in request.GET or 'q' in request.GET
        
        return render(request, 'app/home.html', {
            'banner_events': banner_events,
            'featured_events': featured_events,
            'music_events': music_events,
            'arts_events': arts_events,
            'sports_events': sports_events,
            'other_events': other_events,
            'search_query': search_query,
            'active_category': category_filter,
            'active_category_display': active_category_display,
            'search_results': search_results,
            'is_filtered': is_filtered,
        })
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra khi tải trang chủ: {str(e)}. Vui lòng thử lại sau.")
        return render(request, 'app/home.html', {
            'banner_events': [],
            'featured_events': [],
            'music_events': [],
            'arts_events': [],
            'sports_events': [],
            'other_events': [],
            'search_results': [],
        })

def event_detail(request, event_id):
    try:
        event = get_object_or_404(Event, pk=event_id)
        
        # Lấy các sự kiện cùng loại, không bao gồm sự kiện hiện tại
        related_events = Event.objects.filter(
            category=event.category, 
            sessions__start_time__gte=timezone.now()
        ).exclude(id=event_id).distinct().order_by('sessions__start_time')[:4]
        
        # Lấy tất cả các mốc thời gian của sự kiện
        event_sessions = event.sessions.filter(is_active=True).order_by('start_time')
        
        # Lấy tất cả loại vé cho mỗi mốc thời gian
        sessions_with_tickets = []
        for session in event_sessions:
            tickets = session.ticket_types.filter(
                sale_start_time__lte=timezone.now(),
                sale_end_time__gte=timezone.now()
            )
            if tickets.exists():
                sessions_with_tickets.append({
                    'session': session,
                    'tickets': tickets
                })
        
        if not sessions_with_tickets:
            messages.warning(request, "Hiện tại không có vé nào đang được bán cho sự kiện này.")
        
        return render(request, 'app/event_detail.html', {
            'event': event,
            'related_events': related_events,
            'sessions_with_tickets': sessions_with_tickets
        })
    except Exception as e:
        return redirect('home')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Context to preserve values
        context = {
            'form': form,
            'username_value': username,
            'show_password': False
        }
        
        # Check for empty fields
        if not username:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': ["Vui lòng nhập tên đăng nhập."]})
            messages.error(request, "Vui lòng nhập tên đăng nhập.")
            return render(request, 'app/login_enhanced.html', context)
        
        if not password:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': ["Vui lòng nhập mật khẩu."]})
            messages.error(request, "Vui lòng nhập mật khẩu.")
            return render(request, 'app/login_enhanced.html', context)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                UserProfile.objects.get_or_create(user=user)
                
                login(request, user)
                if is_ajax:
                    return JsonResponse({'success': True, 'redirect_url': reverse('home')})
                return redirect('home')
        else:
            errors = []
            captcha_error = False
            auth_error = False
            
            if 'captcha' in form.errors:
                captcha_error = True
                errors.append("Bạn cần hoàn thành kiểm tra CAPTCHA để tiếp tục.")
            else:
                # Kiểm tra lỗi xác thực
                user = authenticate(username=username, password=password)
                if user is None:
                    auth_error = True
                    errors.append("Tên đăng nhập hoặc mật khẩu không chính xác.")
            
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'captcha_error': captcha_error,
                    'auth_error': auth_error,
                    'errors': errors
                })
            else:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'app/login_enhanced.html', context)
    else:   
        form = LoginForm()
    
    return render(request, 'app/login_enhanced.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        # Get form fields to validate
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Chuẩn bị context với các giá trị đã nhập
        context = {
            'form': form,
            'username_value': username,
            'email_value': email,
            # Không lưu giá trị mật khẩu vì lý do bảo mật
        }
        
        # Collect errors
        errors = []
        
        # Validate required fields
        if not username:
            errors.append("Vui lòng nhập tên đăng nhập.")
            if not is_ajax:
                messages.error(request, "Vui lòng nhập tên đăng nhập.")
                return render(request, 'app/login_enhanced.html', context)
        
        if not email:
            errors.append("Vui lòng nhập email.")
            if not is_ajax:
                messages.error(request, "Vui lòng nhập email.")
                return render(request, 'app/login_enhanced.html', context)
        
        if not password1:
            errors.append("Vui lòng nhập mật khẩu.")
            if not is_ajax:
                messages.error(request, "Vui lòng nhập mật khẩu.")
                return render(request, 'app/login_enhanced.html', context)
        
        if not password2:
            errors.append("Vui lòng xác nhận mật khẩu.")
            if not is_ajax:
                messages.error(request, "Vui lòng xác nhận mật khẩu.")
                return render(request, 'app/login_enhanced.html', context)
        
        # Additional validations
        if password1 != password2:
            errors.append("Mật khẩu xác nhận không khớp.")
            if not is_ajax:
                messages.error(request, "Mật khẩu xác nhận không khớp.")
                return render(request, 'app/login_enhanced.html', context)
            
        # Check if username already exists
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            errors.append("Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.")
            if not is_ajax:
                messages.error(request, "Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.")
                return render(request, 'app/login_enhanced.html', context)
            
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            errors.append("Email này đã được đăng ký. Vui lòng sử dụng email khác.")
            if not is_ajax:
                messages.error(request, "Email này đã được đăng ký. Vui lòng sử dụng email khác.")
                return render(request, 'app/login_enhanced.html', context)
        
        # If there are already errors, return them for AJAX requests
        if errors and is_ajax:
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        
        if form.is_valid():
            user = form.save()
            # Tạo profile cho người dùng mới
            UserProfile.objects.get_or_create(user=user)
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('login')
                })
            else:
                messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
                return redirect('login')
        else:
            captcha_error = False
            # Check for CAPTCHA errors
            if 'captcha' in form.errors:
                captcha_error = True
                errors.append("Vui lòng xác nhận bạn không phải là robot.")
                
            # Handle other validation errors from the form
            for field, error_list in form.errors.items():
                for error in error_list:
                    if field != 'captcha':  # Skip captcha errors as we've already handled them
                        if "password" in field.lower() and "too short" in error.lower():
                            errors.append("Mật khẩu quá ngắn. Tối thiểu 8 ký tự.")
                        elif "password" in field.lower() and "numeric" in error.lower():
                            errors.append("Mật khẩu không được chỉ chứa số.")
                        else:
                            errors.append(error)
            
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'captcha_error': captcha_error,
                    'errors': errors
                })
            else:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'app/login_enhanced.html', context)
    else:
        form = RegisterForm()
    
    return render(request, 'app/login_enhanced.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    # Xác định tab active
    active_tab = request.GET.get('tab', 'profile')
    
    if request.method == 'POST':
        try:
            # In ra toàn bộ dữ liệu POST để debug
            print("POST data:", request.POST)
            
            # Xử lý avatar
            if 'avatar' in request.FILES:
                if request.user.profile.avatar:
                    request.user.profile.avatar.delete()
                request.user.profile.avatar = request.FILES['avatar']
            
            # Xử lý thông tin cá nhân
            full_name = request.POST.get('full_name', '').strip()
            if full_name:
                first_name, *last_name_parts = full_name.split(' ', 1)
                last_name = last_name_parts[0] if last_name_parts else ''
                request.user.first_name = first_name
                request.user.last_name = last_name
            
            # Cập nhật thông tin profile
            request.user.profile.phone_number = request.POST.get('phone_number', '')
            request.user.profile.address = request.POST.get('address', '')
            
            # Xử lý ngày sinh
            birth_date = request.POST.get('birth_date')
            if birth_date:
                from datetime import datetime
                try:
                    request.user.profile.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Định dạng ngày sinh không hợp lệ')
                    return redirect('profile')
            
            # Xử lý giới tính
            gender = request.POST.get('gender')
            if gender in ['M', 'F']:
                request.user.profile.gender = gender
            
            # Lưu các thay đổi
            request.user.save()
            request.user.profile.save()
            
            # messages.success(request, f'Thông tin cá nhân đã được cập nhật thành công. Cảm ơn {request.user.first_name or request.user.username} đã cập nhật!')
            return redirect('profile')
            
        except Exception as e:
            import traceback
            print("Error in profile update:", str(e))
            print("Traceback:", traceback.format_exc())
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('profile')
    
    # Lấy danh sách vé của người dùng
    bookings = Booking.objects.filter(email=request.user.email).order_by('-booking_date')
    now = timezone.now()
    
    # Phân loại vé
    upcoming_bookings = [b for b in bookings if b.ticket_type and b.ticket_type.session and b.ticket_type.session.start_time > now]
    past_bookings = [b for b in bookings if b.ticket_type and b.ticket_type.session and b.ticket_type.session.start_time <= now]
    
    # Lấy sự kiện do người dùng tạo (giả sử là chưa có)
    # Hiện tại chưa có chức năng tạo sự kiện, nên chúng ta sẽ để trống
    my_events = Event.objects.none()
    
    context = {
        'active_tab': active_tab,
        'bookings': bookings,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'my_events': my_events,
    }
    return render(request, 'app/user_profile.html', context)

@csrf_exempt
@require_POST
def verify_payment(request):
    """API endpoint để xác thực thanh toán"""
    order_id = request.POST.get('order_id')
    if not order_id:
        return JsonResponse({'success': False, 'message': 'Không có mã đơn hàng'})
    
    try:
        booking = get_object_or_404(Booking, order_id=order_id)
        
        # Chỉ cập nhật nếu chưa thanh toán
        if booking.payment_status != 'Paid':
            # Cập nhật trạng thái thanh toán SỬ DỤNG TRUY VẤN SQL TRỰC TIẾP
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE booking_booking SET payment_status=?, payment_method=?, payment_date=? WHERE id=?", 
                    ['Paid', 'Chuyển khoản ngân hàng', timezone.now(), booking.id]
                )
            
            # Cập nhật số lượng vé còn lại
            if booking.ticket_type:
                ticket_type = booking.ticket_type
                ticket_type.quantity -= booking.quantity
                if ticket_type.quantity < 0:
                    ticket_type.quantity = 0
                ticket_type.save()
                
                logger.info(f"Đã cập nhật số lượng vé cho loại vé {ticket_type.name}: còn lại {ticket_type.quantity}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Thanh toán thành công',
            'redirect_url': f'/booking/complete/{booking.id}/'
        })
    
    except Exception as e:
        logger.error(f"Lỗi khi xử lý verify_payment: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
@login_required
def user_dashboard(request):
    """Hiển thị dashboard của người dùng với thông tin tổng quan"""
    
    # Lấy tất cả các bookings của người dùng
    bookings = Booking.objects.filter(user=request.user)
    
    # Tính toán các số liệu thống kê
    total_tickets = bookings.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_spent = bookings.filter(payment_status='Paid').aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Phân loại bookings theo thời gian
    now = timezone.now()
    upcoming_bookings = bookings.filter(
        session__start_time__gt=now, 
        payment_status='Paid'
    ).select_related('event', 'ticket_type', 'session').order_by('session__start_time')[:5]
    
    past_bookings = bookings.filter(
        session__start_time__lt=now,
        payment_status='Paid'
    ).select_related('event')
    
    past_events = past_bookings.values('event').distinct().count()
    
    # Lấy sự kiện đề xuất dựa trên category của sự kiện đã tham gia
    attended_categories = past_bookings.values_list('event__category', flat=True).distinct()
    recommended_events = Event.objects.filter(
        category__in=attended_categories,
        sessions__start_time__gt=now
    ).exclude(
        id__in=upcoming_bookings.values_list('event_id', flat=True)
    ).distinct()[:3]
    
    context = {
        'total_tickets': total_tickets,
        'total_spent': total_spent,
        'past_events': past_events,
        'upcoming_bookings': upcoming_bookings,
        'recommended_events': recommended_events,
    }
    
    return render(request, 'app/user_dashboard.html', context)
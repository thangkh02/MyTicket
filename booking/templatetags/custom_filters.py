from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def add_7_hours(value):
    """Thêm 7 giờ vào datetime để chuyển về múi giờ Việt Nam (UTC+7)"""
    if value:
        return value + timedelta(hours=7)
    return value

@register.filter
def vn_datetime(value, format_string="H:i, d/m/Y"):
    """Định dạng datetime sau khi đã thêm 7 giờ (múi giờ Việt Nam)"""
    if value:
        vn_time = value + timedelta(hours=7)
        return vn_time.strftime(format_string)
    return ""
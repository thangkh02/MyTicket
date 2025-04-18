from django.contrib import admin
from .models import Event, EventSession, TicketType

class EventSessionInline(admin.TabularInline):
    model = EventSession
    extra = 1

class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 1

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'category')
    list_filter = ('category', 'location')
    search_fields = ('title', 'description')
    inlines = [EventSessionInline]

class EventSessionAdmin(admin.ModelAdmin):
    list_display = ('event', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'start_time')
    search_fields = ('event__title',)
    inlines = [TicketTypeInline]

class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'price', 'quantity', 'available_quantity', 'min_quantity_per_order', 'max_quantity_per_order')
    list_filter = ('session__event', 'price')
    search_fields = ('name', 'session__event__title')
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('session', 'name', 'price', 'description')
        }),
        ('Số lượng vé', {
            'fields': ('quantity', 'min_quantity_per_order', 'max_quantity_per_order')
        }),
        ('Thời gian bán vé', {
            'fields': ('sale_start_time', 'sale_end_time')
        }),
        ('Thông tin bổ sung', {
            'fields': ('ticket_info', 'ticket_image'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(Event, EventAdmin)
admin.site.register(EventSession, EventSessionAdmin)
admin.site.register(TicketType, TicketTypeAdmin)
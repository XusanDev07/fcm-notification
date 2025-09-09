from django.contrib import admin
from .models import Notification, NotificationLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'sent_count', 'success_count', 'failure_count', 'created_at']
    list_filter = ['sent_to_all', 'created_at']
    search_fields = ['title', 'body']
    readonly_fields = ['sent_count', 'success_count', 'failure_count', 'created_at']

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'device', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    readonly_fields = ['sent_at']
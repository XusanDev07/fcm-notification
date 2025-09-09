from django.urls import path
from . import views

urlpatterns = [
    path('register-device/', views.register_device, name='register_device'),
    path('send-notification/', views.send_notification, name='send_notification'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('devices/', views.get_devices, name='get_devices'),
    path('test-token/', views.test_token, name='test_token'),
]

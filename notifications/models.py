from django.db import models
from fcm_django.models import FCMDevice


class Notification(models.Model):
    """
    Model to represent a notification to be sent to devices.
    """
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_all = models.BooleanField(default=False)
    sent_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class NotificationLog(models.Model):
    """
    Model to log the status of each notification sent to a device.
    """
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("delivered", "Delivered")
    ])
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)


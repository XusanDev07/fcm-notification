import json
import logging
import traceback
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from fcm_django.models import FCMDevice
from firebase_admin import messaging

from .models import Notification, NotificationLog

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_device(request):
    """
    Register FCM token
    """
    try:
        token = request.data.get('token')
        user_id = request.data.get('user_id', None)
        device_type = request.data.get('type', 'web')
        
        if not token:
            return Response({'error': 'Token is required'}, status=400)
        
        # Check for existing device
        device, created = FCMDevice.objects.get_or_create(
            registration_id=token,
            defaults={
                'type': device_type,
                'user_id': user_id if user_id else None,
                'active': True
            }
        )
        
        # If it exists, activate it
        if not created and not device.active:
            device.active = True
            device.save()
        
        return Response({
            'success': True,
            'created': created,
            'device_id': device.id,
            'message': 'Token has been successfully registered'
        })
        
    except Exception as e:
        logger.error(f"Device registration error: {str(e)}")
        return Response({'error': 'An internal error has occurred.'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_notification(request):
    """
    Send notification
    """
    try:
        title = request.data.get('title')
        body = request.data.get('body')
        data = request.data.get('data', {})
        send_to_all = request.data.get('send_to_all', True)
        user_ids = request.data.get('user_ids', [])
        
        if not title or not body:
            return Response({'error': 'Title and body are required'}, status=400)
        
        # Save notification to database
        notification = Notification.objects.create(
            title=title,
            body=body,
            data=data,
            sent_to_all=send_to_all
        )
        
        # Get devices
        if send_to_all:
            devices = FCMDevice.objects.filter(active=True)
        else:
            devices = FCMDevice.objects.filter(user_id__in=user_ids, active=True)
        
        if not devices.exists():
            return Response({'error': 'No active devices found'}, status=404)
        
        # Sending notification
        success_count = 0
        failure_count = 0
        
        # Create FCM message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data={
                'notification_id': str(notification.id),
                'timestamp': str(notification.created_at),
                **data  # Extra data
            }
        )
        
        # Send to each device
        for device in devices:
            try:
                # Assign token to message
                message.token = device.registration_id
                
                # Send
                response = messaging.send(message)
                success_count += 1
                
                # Create log
                NotificationLog.objects.create(
                    notification=notification,
                    device=device,
                    status='sent'
                )
                
                logger.info(f"Message sent successfully: {response}")
                
            except messaging.InvalidArgumentError as e:
                failure_count += 1
                logger.error(f"Invalid argument: {str(e)}")
                
                NotificationLog.objects.create(
                    notification=notification,
                    device=device,
                    status='failed',
                    error_message=str(e)
                )
                
            except messaging.UnregisteredError as e:
                failure_count += 1
                logger.error(f"Token unregistered: {str(e)}")
                
                # Deactivate invalid token
                device.active = False
                device.save()
                
                NotificationLog.objects.create(
                    notification=notification,
                    device=device,
                    status='failed',
                    error_message='Token unregistered'
                )
                
            except Exception as e:
                failure_count += 1
                logger.error(f"Send notification error: {str(e)}")
                
                NotificationLog.objects.create(
                    notification=notification,
                    device=device,
                    status='failed',
                    error_message=str(e)
                )
        
        # Update statistics
        notification.sent_count = devices.count()
        notification.success_count = success_count
        notification.failure_count = failure_count
        notification.save()
        
        return Response({
            'success': True,
            'notification_id': notification.id,
            'total_devices': devices.count(),
            'success_count': success_count,
            'failure_count': failure_count,
            'message': f'Notification sent! {success_count} successful, {failure_count} failed'
        })
        
    except Exception as e:
        logger.error(f"Send notification error: {str(e)}")
        return Response({'error': 'An internal error has occurred.'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_notifications(request):
    """
    List of sent notifications
    """
    try:
        notifications = Notification.objects.all()[:20]
        data = []
        
        for notif in notifications:
            data.append({
                'id': notif.id,
                'title': notif.title,
                'body': notif.body,
                'data': notif.data,
                'created_at': notif.created_at.isoformat(),
                'sent_count': notif.sent_count,
                'success_count': notif.success_count,
                'failure_count': notif.failure_count,
                'sent_to_all': notif.sent_to_all
            })
        
        return Response(data)
    except Exception as e:
        logger.error("Get notifications error: %s", traceback.format_exc())
        return Response({'error': 'An internal error has occurred.'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_devices(request):
    """
    Registered devices
    """
    try:
        devices = FCMDevice.objects.all().order_by('-date_created')
        data = []
        
        for device in devices:
            data.append({
                'id': device.id,
                'user_id': device.user_id,
                'type': device.type,
                'active': device.active,
                'date_created': device.date_created.isoformat()
            })
        
        return Response(data)
    except Exception as e:
        logger.error("Get devices error: %s", traceback.format_exc())
        return Response({'error': 'An internal error has occurred.'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def test_token(request):
    """
    Test token
    """
    try:
        token = request.data.get('token')
        
        if not token:
            return Response({'error': 'Token is required'}, status=400)
        
        # Send test message
        message = messaging.Message(
            notification=messaging.Notification(
                title='Test Notification',
                body='This is a test message - token is working!'
            ),
            token=token
        )
        
        response = messaging.send(message)
        
        return Response({
            'success': True,
            'message_id': response,
            'message': 'Test notification has been sent!'
        })
        
    except messaging.InvalidArgumentError:
        return Response({'error': 'Invalid token'}, status=400)
    except messaging.UnregisteredError:
        return Response({'error': 'Token is not registered'}, status=400)
    except Exception as e:
        logger.error("Test token error: %s", traceback.format_exc())
        return Response({'error': 'An internal error has occurred.'}, status=500)

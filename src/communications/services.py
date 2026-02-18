from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_notification(user, subject, template_name, context=None):
    """
    Send an email notification to a user.
    """
    if context is None:
        context = {}
    
    context['user'] = user
    
    # Render email body
    # For now, we'll just use simple text or HTML if template exists
    # But since we haven't created templates yet, we'll just send text.
    message = f"Hello {user.first_name},\n\n This is a notification from Green Grid Platform."
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@greengrid.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email to {user.email}: {e}")
        return False

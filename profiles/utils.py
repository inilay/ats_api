from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

server_domain = '127.0.0.1:8000'
front_domain = '127.0.0.1:3000'


def send_email_for_verify(user):
    use_https = False
    context = {
        "domain": server_domain,
        "user": user,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "user": user,
        "token": default_token_generator.make_token(user),
        "protocol": "https" if use_https else "http"
    }
    message = render_to_string('registration/verify_email.html', context=context)
    send_mail( 'Verify email',
        '',
        'ilya.savelev.2001@gmail.com',
        [user.email],
        html_message = message,
        fail_silently=False)

def send_email_for_reset(user):
    use_https = False
    context = {
                "email": user.email,
                "domain": front_domain,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user.username,
                "token": default_token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                
            }
    print(user)
    message = render_to_string('registration/password_reset.html', context=context)
    send_mail( 'Change password',
        '',
        'ilya.savelev.2001@gmail.com',
        [user.email],
        html_message = message,
        fail_silently=False)

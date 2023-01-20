from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings


def send_email(to, subject, template, context):
    html_content = render_to_string(template, context)
    msg = EmailMessage(subject, html_content, settings.EMAIL_HOST_USER, [to])
    msg.content_subtype = "html"
    msg.send()

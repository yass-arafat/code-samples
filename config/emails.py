from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django_rq import job


@shared_task
def send_midnight_calculation_email_notification(
    user_count, timestamp, total_time_in_microseconds, error
):
    subject = "Midnight Calculation Cron job Update"
    message = (
        f"Cron job has run at {timestamp}.\n"
        f"Total {user_count} users data were updated.\n"
        f"Total time taken was {total_time_in_microseconds} microseconds.\n"
    )
    if error:
        message += f"Error: {error}"
    else:
        message += "No error occurred."
    sender = settings.CRON_EMAIL_SENDER
    recipient_list = settings.EMAIL_NOTIFICATION_RECEPIENT_LIST
    send_mail(subject, message, sender, recipient_list, fail_silently=False)


@shared_task
def send_morning_calculation_email_notification(
    user_count, timestamp, total_time_in_microseconds, error
):
    subject = "Morning Calculation Cron job Update"
    message = (
        f"Cron job has run at {timestamp}.\n"
        f"Total {user_count} users data were updated.\n"
        f"Total time taken was {total_time_in_microseconds} microseconds.\n"
    )
    if error:
        message += f"Error: {error}"
    else:
        message += "No error occurred."
    sender = settings.CRON_EMAIL_SENDER
    recipient_list = settings.EMAIL_NOTIFICATION_RECEPIENT_LIST
    send_mail(subject, message, sender, recipient_list, fail_silently=False)


@shared_task
def send_unusual_load_drop_email(user_list, cron_name, timezone_offset):
    timestamp = datetime.now()
    subject = "Actual Load or SQS changed more than change limit for Some Users"
    message = (
        f"{cron_name} cron job for {timezone_offset} has run at {timestamp}.\n"
        f"Total {len(user_list)} users load or SQS has changed more than change limit.\n"
        f"User IDs:"
    )
    for user in user_list:
        message += f"\n {user}"

    sender = settings.CRON_EMAIL_SENDER
    recipient_list = settings.EMAIL_NOTIFICATION_RECEPIENT_LIST
    send_mail(subject, message, sender, recipient_list, fail_silently=False)


@job
def email_password_reset_otp(receiver, html_content):
    subject = "Pillar forgotten password"
    sender = settings.OTP_EMAIL_SENDER
    recipient_list = [receiver]

    mail = EmailMessage(subject, html_content, sender, recipient_list)
    mail.content_subtype = "html"  # Main content is now text/html
    mail.send()


@shared_task
def user_support_mail(receiver, support_id, name):
    subject = f"Pillar Support : Support ID #{support_id}"
    sender = settings.USER_SUPPORT_EMAIL_SENDER
    recipient_list = [receiver]
    message = (
        f"Hello {name},\n"
        "Thanks for contacting us \n"
        f"We would like to let you know that we’ve received your message with Support ID #{support_id}. We have kept "
        f"your request on top-priority and will get back to you with an update within the next 48 hours by email. We "
        f"appreciate your patience \n\n"
        "Regards,\n"
        "Pillar Support Team"
    )
    send_mail(subject, message, sender, recipient_list, fail_silently=False)
    print("Mail sent")

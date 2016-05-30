"""Handles the actual emailing."""
from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText
from config import MY_EMAIL, EMAIL_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD, confirmation, password_change, \
    sent_to_tutor, sent_to_student, reminder, tutoring_service_name

confirmation_message = confirmation

password_change_message = password_change

tutor_message = sent_to_tutor

student_message = sent_to_student

reminder = reminder

def send_email(recipients, message=confirmation_message, **kwargs):
    """Sends an email to the recipient containing the message specified.

        kwargs are used to fill in things like {{username}} or {{email}}

        recipients is a list of arbitrary length, however a check has been added
        just in case.
    """

    text_to_send = message.format(**kwargs)

    if type(recipients) is not list:
        recipient_list = [recipients]
    else:
        recipient_list = recipients

    msg = MIMEText(text_to_send, 'plain')
    msg['Subject'] = tutoring_service_name
    msg['To'] = ', '.join(recipient_list)

    connection = SMTP("smtp.gmail.com")
    connection.login(EMAIL_USERNAME, EMAIL_PASSWORD)

    connection.sendmail(MY_EMAIL, recipient_list, msg.as_string())

    connection.close()




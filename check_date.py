"""Script that checks the date and compares it to the dates stored in the Calendar database."""
#!flask/bin/python
import app
from app.models import Calendar
import app.emailing as e


def main():
    check_calendar_expiration()
    send_emails()


def send_emails():
    """Sends reminder emails to all the tutors/students who are engaged on the day the script is run.

        Includes the period and other person (tutor/student)
    """
    calendars = Calendar.query.filter_by(cal_type=1).all()
    for calendar in calendars:
        periods = calendar.check_weekday()
        for period in periods:
            message = e.reminder.format(period=period)
            e.send_email(calendar.tutor.email, message)


def check_calendar_expiration():
    """Makes the calendar expire if there's a tutoring that lasts longer than 1 week.

        This shouldn't happen naturally, but is included for robustness.

        This was originally going to be a feature, with tutors scheduled for a number of weeks
        as selected by the student, however this made the code too complex for a feature that
        would be too infrequently used.
    """
    app.data.update_calendar()
    calendars = Calendar.query.filter_by(cal_type=1).all()

    for calendar in calendars:
        calendar.check_expiration()

if __name__ == '__main__':
    main()
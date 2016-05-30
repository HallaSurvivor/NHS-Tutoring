"""Helper functions that get called in views.py"""
from .models import Calendar, Subjects, User, StudentTutorPairings
from config import periods, days_attended, basedir, display_tutor_name, period_names, subjects, labels
from app import db
import os
import datetime
from random import shuffle


def update_environment_variables(app):
    """Adds variables to be accessed in html."""
    app.jinja_env.globals.update(user=User,
                                 stp=StudentTutorPairings,
                                 exists=os.path.exists(os.path.join(basedir, 'app/static/images/banner.jpg')),
                                 period_names=period_names,
                                 day_names=days_attended,
                                 period_lists=periods
                                 )


def _jinja2_datetime_filter(weeks):
    monday = datetime.datetime.utcnow().date() - datetime.timedelta(days=datetime.datetime.utcnow().weekday())
    delta = datetime.timedelta(weeks=weeks)
    future = monday+delta
    return future


def update_subjects():
    """Add subject fields based on config."""
    for i in range(len(subjects)):
        for x in range(len(subjects[i])):
            database_label = subjects[i][x].replace(" ", "")
            setattr(Subjects, database_label, db.Column(db.Integer))

def update_calendar():
    """Add calendar fields based on config."""
    for n in range(len(periods)):
        for i in range(periods[n]):
            label = labels[n]+str(i+1)
            setattr(Calendar, label, db.Column(db.Integer))
            setattr(Calendar, label+'_date', db.Column(db.Date))
        before_label = labels[n]+'B'
        setattr(Calendar, before_label, db.Column(db.Integer))
        setattr(Calendar, before_label+'_date', db.Column(db.Date))
        after_label = labels[n]+'A'
        setattr(Calendar, after_label, db.Column(db.Integer))
        setattr(Calendar, after_label+'_date', db.Column(db.Date))


def create_pairing(subject):
    """Take a subject and the logged in student and return a list of potential tutors.

        Potential tutors are chosen based on the matching calendars, the subject
        required, and how busy each tutor is. A list of max 3 tutors with different
        free periods is returned so that the student can choose a day/period that
        works for their schedule.

    """

    period_names.insert(0, "Before")
    period_names.append("After")

    student = User.query_from_cookie()

    subject = subject.replace(" ", "") # turns the pretty display subject into the one word version used by the database

    schedule_keys = Calendar.sort_attrs()

    day_names = {}  # {"Monday Before", "Monday First", ... "Friday After"}
    x = 0
    for i in range(len(periods)):
        for n in range(periods[i]+2):
            key = schedule_keys[x]
            if n != periods[i] + 1:
                day_names[key] = days_attended[i] + " " + period_names[n]
            else:
                day_names[key] = days_attended[i] + " " + period_names[-1]
            x += 1

    if not student.get_calendar_1():
        new_cal = Calendar(tutor=student, cal_type=1)
        for field in Calendar.get_attrs():
            setattr(new_cal, field, 1)
        db.session.add(new_cal)
        db.session.commit()

    student_schedule_1 = dict(Calendar.query_from_field(tutor=student, cal_type=1))
    student_schedule_0 = dict(Calendar.query_from_field(tutor=student, cal_type=0))

    student_schedule = {key: student_schedule_0[key] and student_schedule_1[key] for key in schedule_keys}
    # This creates a merged calender, saved as a dict.
    # The student is only available (stored as 1) when free, and not being tutored/tutoring

    # The mess below this comment creates a merged calendar, saved as a dict.
    # the tutor is only available (stored as 1) when:
    # signed up to tutor
    # not currently tutoring/being tutored
    #

    all_tutors = User.query.filter_by(user_type='1').all()

    if student in all_tutors:
        all_tutors.remove(student)

    matching_subjects = []
    for tutor in all_tutors:
        tutor_subjects = dict(Subjects.query_from_field(tutor=tutor))
        if tutor_subjects[subject]:
            matching_subjects.append(tutor)

    matching_and_free = []
    for tutor in matching_subjects:
        if not tutor.get_calendar_1():
            new_cal = Calendar(tutor=tutor, cal_type=1)
            for field in Calendar.get_attrs():
                setattr(new_cal, field, 1)
            db.session.add(new_cal)
            db.session.commit()

        tutor_schedule_1 = dict(tutor.get_calendar_1())
        tutor_schedule_0 = dict(tutor.get_calendar_0())
        tutor_schedule = {key: tutor_schedule_0[key] and tutor_schedule_1[key] for key in schedule_keys}

        date = datetime.date.today().strftime('%A')

        if date == 'Monday':
            day_letter = 'M'
        elif date == 'Tuesday':
            day_letter = 'T'
        elif date == 'Wednesday':
            day_letter = 'W'
        elif date == 'Thursday':
            day_letter = 'R'
        elif date == 'Friday':
            day_letter = 'F'
        elif date == 'Saturday':
            day_letter = 'S'
        elif date == 'Sunday':
            day_letter = 'U'
        else:
            day_letter = ''

        for key in schedule_keys:
            if student_schedule[key] == tutor_schedule[key] == 1:
                if not key.startswith(day_letter):
                    matching_and_free.append([tutor, key])

    matching_free_and_minimized = []  # sorts the tutors into which day/period they tutor, then who is least busy
    minimized_buffer = {}  # { "MB": [Tutor, Tutor2], "T5": [Tutor3, Tutor4] }
    for pair in matching_and_free:
        tutor = pair[0]
        day = pair[1]
        if not (day in minimized_buffer):
            minimized_buffer[day] = [tutor]
        else:
            minimized_buffer[day].append(tutor)

    # Tries to find the least busy tutors available
    for day, group in minimized_buffer.items():
        lowest_tutor = None
        shuffle(group)
        for tutor in group:
            if not lowest_tutor:
                lowest_tutor = tutor
            else:
                current_value = tutor.get_business_value()
                if current_value < lowest_tutor.get_business_value():
                    lowest_tutor = tutor
        matching_free_and_minimized.append([lowest_tutor.username, day])

    final_dict = {}
    for pair in matching_free_and_minimized:
        tutor = pair[0]
        day = pair[1]
        if day not in final_dict:  # If there isn't already a tutor for that period, which there shouldn't be anyways
            if display_tutor_name:  # config setting on
                final_dict[day] = [("{name}, {period}".format(name=tutor, period=day_names[day])),
                                   tutor,
                                   subject,
                                   day]
            else:  # config setting off
                final_dict[day] = [("{period}".format(period=day_names[day])),
                                   tutor,
                                   subject,
                                   day]

    period_names.remove("Before")  # Removes the added before/after so it doesn't get added every time
    period_names.remove("After")

    return final_dict
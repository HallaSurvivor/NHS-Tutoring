"""Determines which pages are shown, and what forms are run, when the user navigates to a page.

    For the most part, each particular route works to display a form, and then
    do something based on that input (which occurs post validation).

    Validation occurs once the form recognizes that all of the input is valid, and
    verifies that the form came from NHSTutoring, and was not a CSRF attack.
    For more information, check the Flask docs.

    Comments for what each particular route does are included in that route.
"""
from app import app, db
from flask import render_template, flash, redirect, url_for, session, request
from sqlalchemy.exc import IntegrityError
import time
import logging
import csv
from smtplib import SMTPAuthenticationError
import string
import random
from .forms import LoginForm, StudentRegisterForm, TutorRegisterForm, ChangePasswordForm, OfficialPasswordResetForm, \
    FreePeriodsForm, SubjectForm, TutorRequestForm, create_tutor_selection_form, AdminRegisterForm, MassEmailForm
from .models import User, Calendar, Subjects, StudentTutorPairings
from .emailing import send_email, password_change_message, confirmation_message, tutor_message, student_message
from .data import create_pairing
from config import periods, subjects as config_subjects, get_homepage_text, tutoring_head, period_names, \
    allow_password_reset, subject_names

#Logger information to print things to the log file efficiently.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
hdlr = logging.FileHandler('log.txt')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

def if_logged_out():
    flash('Please log in')

def check_login():
    """Returns True if user is not logged in.

        It has to be set up this way to remove duplicate code, slightly unintuitive, but
        I couldn't get around it easily.
    """
    if 'username' not in session:
        return redirect(url_for('login'))


@app.route('/')
@app.route('/index')
def index():
    """Render the homepage, with body text dependent upon the homepage_text.txt in the app."""
    return render_template("index.html", title='Home', bodytext=get_homepage_text())



@app.route('/login', methods=['GET', 'POST'])
def login():
    """Display the login page if the user is not already logged in.

        If the Login Form validates, add a user cookie and redirect to the profile page.
    """
    if not check_login():
        return redirect(url_for('profile'))

    form = LoginForm()

    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('There was a problem with your login.')
            return render_template("login.html", title="Sign In", form=form)
        else:
            flash('Login Successful!')
            logger.info('{user} logged in'.format(user=form.username.data))
            session['username'] = form.username.data.title()
            return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template("login.html", title="Sign In", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Displays a registration page if the user is not logged in.

        If the form validates, attempts to create a new user with formatting:
        username - lowercase
        password - case sensitive (Salted and Hashed)
        user_type - 0 (student)
        email - case sensitive

        User_ID is automatically created. For more info, see models.py

        Tries to send an email to the new user thanking them for signing up.

        Adds a line to log showing a new user was created.
    """
    if not check_login():
        return render_template(url_for('profile'))

    form = StudentRegisterForm()

    if request.method == 'POST':
        if form.validate_on_submit() is False:
            flash("registration failed.")
            return render_template("register.html", title="Register", form=form)
        else:

            try:
                newuser = User.create(form.username.data.lower(), form.password.data, 0, form.email.data)
                logger.info('new user {username} created.'.format(username=form.username.data))

            except IntegrityError:
                flash('Username taken.')
                return render_template("register.html", title="Register", form=form)

            flash('Registration Successful!')
            session['username'] = newuser.username

            try:
                send_email([newuser.email], message=confirmation_message, username=newuser.username)

            except SMTPAuthenticationError:
                flash('Sending email failed')

            return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template('register.html', title="Register", form=form)


@app.route('/tutor-registration', methods=['GET', 'POST'])
def register_tutor():
    """Turns a student (type 0) into a tutor (type 1).

        Checks if a student is logged in, and is not a tutor.
        If the form validates, and the password corresponding to the cfg file is entered,
        make the student into a tutor.

        Adds a line to log saying who became a tutor.
    """
    if check_login():
        if_logged_out()
        return check_login()

    form = TutorRegisterForm()

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template("register.html", title="Register", form=form)
        else:
            flash('Added as tutor!')
            user = User.query_from_cookie()
            logger.info('User {username} became tutor.'.format(username=user.username))
            user.update(user_type=1)
            return redirect(url_for('change_periods'))

    elif request.method == 'GET':
        return render_template('register.html', title='Register', form=form)


@app.route('/admin', methods=['GET', 'POST'])
def register_admin():
    """Turns a non admin (type 0 or 1) into an admin (type 2).
        this address is unlisted to discourage other tutors/students
        from trying to become admins...

        Adds a line to log saying who became an admin.
    """
    if check_login():
        if_logged_out()
        return check_login()

    form = AdminRegisterForm()

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template("register.html", title="Register", form=form)
        else:
            flash('Added as admin!')
            user = User.query_from_cookie()
            logger.info('User {username} became admin.'.format(username=user.username))
            user.update(user_type=2)
            return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template('register.html', title='Register', form=form)


@app.route('/free-periods', methods=['GET', 'POST'])
def change_periods():
    """Displays a grid of every period, the user ticks which periods they are available to tutor/be tutored.

        This is accomplished by iterating through the number of school days, and then, in each school day,
        by iterating through the number of periods in the day + 2 (before/after school).
        Each of these then becomes a checkbox that is displayed, and stored as a 1 or 0 in the Calendar database.
        1 => student is free
        0 => student is not free

        The form will return a list of which boxes were checked. Since the grid is essentially a list of forms,
        a list of lists is returned for a given calendar.

        Each list will contain the item number of whichever box was checked.
        To move from this format to the format above, the program iterates through the periods in a day,
        and if the period number is in the list, the database stores a 1 in that location.

        The checkboxes are also automatically ticked upon rendering based upon the student's Calendar database.
        This is done through WTForms default feature, and using a dictionary of the Calendar database.

        Additionally, if there is not a Calender that represents if a user is already doing something on a given day
        (The two will be, essentially, ANDed together to determine the true freedom of a user)
        that calendar is also created, with 1 in every position.

        For more information, see models.py, forms.py, and data.py

        Example: first day of school is monday.
        monday has 10 periods (8 periods, before school, and after school)
        iterates from i=0 to i=9, and compares each value to the data in monday.data (the monday part of the form)
        if monday.data has that value, it puts a 1 into schedule, if not, it puts a 0.

        Finally, if the user is a new tutor, redirect to the subjects page, otherwise, redirect to the profile page.
    """
    if check_login():
        if_logged_out()
        return check_login()

    user = User.query_from_cookie()
    try:
        preticked = user.get_calendar_0().get_data_dict()
    except AttributeError:
        preticked = {}
    form = FreePeriodsForm(**preticked)

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template("Tutor-calendar.html", title="Change Free Periods", form=form)
        else:
            calendar = []
            y = 0  # y will represent which day we're on.
            for day in form:
                if day.type not in ["HiddenField", "CSRFTokenField"]:
                    for i in range(periods[y] + 2):  # plus 2 because before and after school
                        counted = False
                        for point in day.data:
                            if point == i:
                                calendar.append(1)
                                counted = True
                        else:
                            if counted is False:
                                calendar.append(0)
                    y += 1

            newschedule = user.get_calendar_0()
            if not newschedule:
                newschedule = Calendar(tutor=user)
            attrs = Calendar.sort_attrs()
            for i in range(len(attrs)):
                setattr(newschedule, attrs[i], calendar[i])

            if not user.get_calendar_1():
                newagenda = Calendar(tutor=user, cal_type=1)
                for attr in attrs:
                    setattr(newagenda, attr, 1)

            db.session.commit()

            flash('Change successful!')
            logger.info('User {username} changed free periods'.format(username=user.username))

            if (user.user_type == 1) and (Subjects.query_from_field(tutor=user) is None):
                return redirect(url_for('subjects'))

            else:
                return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template("Tutor-calendar.html", title="Change Free Periods", form=form)


@app.route('/subjects', methods=['GET', 'POST'])
def subjects():
    """Change which subjects a tutor is able to tutor.

        Redirects to profile if user is not a tutor.

        Subjects, as stored in config, are a list of lists of the form:

        Subjects = [Category1, Category2, ...]
        Category1 = [Class1, Class2, ...]

        This allows the program to render a table in the same way as /free-periods

        First, the categories are split, and each category is given a form.
        Then, each category has each class within it rendered as a checkbox.

        i.e. Math = [Alg, PreCalc]; Language = [Spanish, French]
             Subjects = [Math, Language]

             This renders as:
             Math      Language
             *Alg      *Spanish
             *PreCalc  *French

        This is all generalized through iteration, like Free Periods, based on the cfg file.
        Likewise, 1 => can tutor, 0=> cannot tutor.

        Also, the subjects you can tutor are remembered and reticked, just like free-periods.

    """
    if check_login():
        if_logged_out()
        return check_login()

    user = User.query_from_cookie()
    try:
        preticked = user.get_subjects().get_data_dict()
    except AttributeError:
        preticked = {}
    form = SubjectForm(**preticked)

    if user.user_type == 0:
        flash('To change which subjects you can tutor, please log in as a tutor')
        return redirect(url_for('profile'))

    else:
        if request.method == 'POST':
            if not form.validate_on_submit():
                return render_template("subjects.html", title="Change Subjects", form=form)
            else:
                attrs = Subjects.sort_attrs()
                subject_list = []
                y = 0
                for field in form:
                    if field.type not in ["HiddenField", "CSRFTokenField"]:
                        for i in range(len(config_subjects[y])):
                            counted = False
                            for point in field.data:
                                if point == i:
                                    subject_list.append(1)
                                    counted = True
                            else:
                                if counted is False:
                                    subject_list.append(0)
                        y += 1

                newsubjects = Subjects(tutor=user)

                counter = 0
                for i in range(len(attrs)):
                    for n in range(len(attrs[i])):
                        setattr(newsubjects, attrs[i][n], subject_list[counter])
                        counter += 1
                if user.subjects is not None:
                    oldsubjects = Subjects.query.filter_by(tutor=user).first()
                    db.session.delete(oldsubjects)
                db.session.add(newsubjects)
                db.session.commit()

                flash("Change successful!")
                logger.info('user {username} changed subjects'.format(username=user.username))
                return redirect(url_for('profile'))

        elif request.method == 'GET':
            return render_template("subjects.html", title='Change Subjects', form=form)


@app.route('/profile')
def profile():
    """The profile page. Also shows the signed in user's schedule for this week.

        For more information about the schedule, see profile.html
    """
    if check_login():
        if_logged_out()
        return check_login()
    user = User.query_from_cookie()

    if user is None:
        return redirect(url_for('login'))
    else:
        return render_template('profile.html', title="My Profile", schedule=None)


@app.route('/logout')
def logout():
    """Removes the user's cookie from their computer."""
    if check_login():
        return redirect(url_for('index'))

    flash('Successfully logged out')
    logger.info('user {username} logged out'.format(username=session['username']))
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/password-reset', methods=['GET', 'POST'])
def change_password():
    """The first of a two part password reset mechanism.

        Creates a key, and stores it in a cookie alongside the user's email and a time of creation.

        Emails the key to the user.
    """
    if not allow_password_reset:
        return render_template(url_for('profile'))

    form = ChangePasswordForm()
    if not check_login():
        return render_template(url_for('profile'))

    if request.method == 'POST':
        if form.validate_on_submit() is False:
            return render_template("password-reset.html", title="Change Password", form=form)
        else:
            #make a key, email it to user, store it as a cookie
            user = User.query.filter_by(username=form.username.data.title()).first()
            user_email = user.email

            crypto = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

            send_email([user_email], message=password_change_message, code=crypto)
            flash('Password Email sent!')
            logger.info('Sent password reset email to {username} at {email}'.format(username=user.username,
                                                                                    email=user.email))

            if 'email_check' in session:
                session.pop('email_check', None)

            session['email_check'] = [user_email, time.time(), crypto, user.username]
            return redirect(url_for('reset'))

    elif request.method == 'GET':
        return render_template("password-reset.html", title="Change Password", form=form)


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    """The actual password reset page.

        The user enters their code within 5 minutes of receiving it, along with a new password.
    """
    if not allow_password_reset:
        return render_template(url_for('profile'))

    if not check_login():
        return render_template(url_for('profile'))

    if 'email_check' not in session:
        return redirect(url_for('change_password'))

    form = OfficialPasswordResetForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template("reset.html", title="Change Password", form=form)
        else:
            #compares key entered to key stored in cookie to validate
            flash('Password Changed!')
            user = User.query_from_field(username=form.username.data.title())
            user.set_password(form.password.data)
            db.session.commit()
            logger.info('Password for {username} changed'.format(username=user.username))
            session.pop('email_check', None)
            return redirect(url_for('index'))

    elif request.method == 'GET':
        return render_template("reset.html", title="Change Password", form=form)


@app.route('/tutor-request', methods=['GET', 'POST'])
def tutorrequest():
    """Shows a dropdown with every subject, then redirects to a page with tutors.

        Tutors are chosen via data.py's create_pairing() function.
    """
    if check_login():
        if_logged_out()
        return check_login()

    user = User.query_from_cookie()
    form = TutorRequestForm()

    if user.calendars.filter_by(cal_type=0).first() is None:
        flash('Please submit your schedule so we can match you with a tutor who is free when you are.')
        return redirect(url_for('change_periods'))

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template("tutor request.html", title="Request Tutor", form=form)

        else:
            session['tutor list'] = create_pairing(form.subject_request.data)
            logger.info('user {username} requested tutor in {subject}'.format(username=user.username,
                                                                              subject=form.subject_request.data))
            return redirect(url_for('tutorselection'))


    elif request.method == 'GET':
        return render_template("tutor request.html", title="Request Tutor", form=form)


@app.route('/tutor-selection', methods=['GET', 'POST'])
def tutorselection():
    """Shows a list of 3 tutors who are free at different times, that the user must pick between.

        Once the user chooses, the user and the selected tutor are both emailed, and have their second calendar
        change that period to 0, to show that they are both busy that day and period.
    """
    if check_login():
        if_logged_out()
        return check_login()

    if 'tutor list' not in session:
        flash("Please request a tutor")
        return redirect(url_for('tutorrequest'))

    form = create_tutor_selection_form()

    if not form:
        session.pop('tutor list', None)
        flash("We're sorry. There are no tutors for that subject available when you are. "
              "Please contact {0}.".format(tutoring_head))
        return redirect(url_for('profile'))

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template('tutor selection.html', title='Select Tutor', form=form)

        else:
            new_user_cal_1 = User.query_from_cookie().get_calendar_1()

            for key in form.potential_tutors.data:
                tutor = User.query_from_field(username=session['tutor list'][key][1])
                tutor_cal_1 = tutor.get_calendar_1()
                new_user_cal_1.set_0(key)
                tutor_cal_1.set_0(key)

                date_dict = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday',
                             'R': 'Thursday', 'F': 'Friday', 'S': 'Saturday', 'U': 'Sunday'}

                period_names.insert(0, 'Before School')
                period_names.append('After School')

                subject = session['tutor list'][key][2]
                date_precurser = session['tutor list'][key][3]  # MB, T3, etc.
                date_name = date_dict[date_precurser[0]]  # Monday, Wednesday, etc.
                date = tutor_cal_1.get_next_weekday(date_precurser).date()

                date_string = date_name + " " + str(date)

                if date_precurser[1] != 'B' and date_precurser[1] != 'A':
                    period = str(period_names[int(date_precurser[1])]) + " Period"  # 3rd Period
                    period_for_stp = int(date_precurser[1]) + 1
                elif date_precurser[1] == 'B':
                    period = period_names[0]  # Before School
                    period_for_stp = 0
                else:
                    period = period_names[-1]  # After School
                    period_for_stp = -1

                logger.info('{student} to be tutored by {tutor} in {subject}, {period} on {date}'.format(
                    student=User.query_from_cookie().username, tutor=tutor.username, subject=subject,
                    period=period, date=date_string))

                new_pairing = StudentTutorPairings(User.query_from_cookie().username, tutor.username, subject, date,
                                                   period_for_stp)
                db.session.add(new_pairing)

                try:
                    send_email([tutor.email], tutor_message, student=User.query_from_cookie().username,
                                                        subject=subject, date=date_string, period_number=period,
                                                        email=User.query_from_cookie().email)

                    send_email([User.query_from_cookie().email], student_message, tutor=tutor.username,
                                                        subject=subject, date=date_string, period_number=period,
                                                        email=tutor.email)
                except SMTPAuthenticationError:
                    flash('Sending email failed')
                    logger.error('Email sending failed')

            db.session.commit()

            # Removes the inserted values so that they aren't inserted every time this runs.
            period_names.remove("Before School")
            period_names.remove("After School")

            session.pop('tutor list', None)
            return redirect(url_for('profile'))
    elif request.method == 'GET':
        return render_template('tutor selection.html', title='Select Tutor', form=form)


@app.route('/schedule', methods=['GET'])
def schedule():
    """Renders a master schedule for the week. - accessible by admins only.

        Also creates a CSV file of all the student tutor pairings.
    """
    if 'username' not in session:
        flash('Please log in to continue')
        return redirect(url_for('login'))

    if User.query_from_cookie().user_type != 2:
        flash('You must be an admin to see the master schedule')
        return redirect(url_for('profile'))

    csv_array = [["student", "tutor", "subject", "date", "active"]]
    for pairing in StudentTutorPairings.query.all():
        row = [pairing.student, pairing.tutor, pairing.subject, pairing.date_str, pairing.active]
        csv_array.append(row)

    with open('StudentTutorPairings.csv', 'w') as STP:
        writer = csv.writer(STP)
        for row in csv_array:
            writer.writerow(row)

    return render_template('schedule.html', title="Master Schedule")

@app.route('/mass-email', methods=['GET', 'POST'])
def mass_email():
    """Allows to send emails to any targeted group of students/tutors

        First identifies the subjects checked in the form,
        Then sorts those ticked boxes into a dictionary of lists,
        Then compares the values in each list of that dictionary
            to the values in each corresponding list of each tutor's
            dictionary,
        Finally it makes a list of the emails of every tutor who tutors
        the subject required.
    """

    if 'username' not in session:
        flash('Please log in to continue')
        return redirect(url_for('login'))

    if User.query_from_cookie().user_type != 2:
        flash('You must be an admin to send emails')
        return redirect(url_for('profile'))

    form = MassEmailForm()

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template("mass email.html", title="Mass Email", form=form)
        else:
            subject_list = []
            y = 0
            for field in form:
                if field.type not in ["HiddenField", "CSRFTokenField", "TextAreaField"]:
                    for i in range(len(config_subjects[y])):
                        counted = False
                        for point in field.data:
                            if point == i:
                                subject_list.append(1)
                                counted = True
                        else:
                            if counted is False:
                                subject_list.append(0)
                    y += 1

            # creates a dict of lists to line up with user.subjects layout
            transition_dict = {}
            for i in range(len(config_subjects)):
                subsection = []
                for x in range(len(config_subjects[i])):
                    subsection.append(subject_list[0])
                    subject_list.pop(0)
                transition_dict[subject_names[i]] = subsection

            final_dict = {}

            for key in transition_dict:
                value = transition_dict[key]
                final_dict[key] = []
                for i in range(len(value)):
                    if value[i]:
                        final_dict[key].append(i)

            recipient_tutors = []
            possible_recipients = User.query.filter_by(user_type=1).all()
            for tutor in possible_recipients:
                tutor_subjects = tutor.get_subjects().get_data_dict()
                for key in tutor_subjects:
                    if tutor not in recipient_tutors:
                        for i in tutor_subjects[key]:
                            if i in final_dict[key]:
                                recipient_tutors.append(tutor)

            recipients = []
            for tutor in recipient_tutors:
                recipients.append(tutor.email)

            try:
                send_email(recipients, form.body.data)
                flash('email sent successfully!')
            except SMTPAuthenticationError:
                flash('Sending email failed')
                logger.error('Mass Email sending failed')

            return render_template('mass email.html', title='Mass Email', form=form)

    elif request.method == 'GET':
        return render_template('mass email.html', title='Mass Email', form=form)
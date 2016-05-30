"""All of the web forms on the site.

    Each form is stored in its own class,
    which is later instantiated in views.py

    Since FreePeriodForm and SubjectForm vary based upon
    config.py, the actual creation of the fields is handled
    outside of the class, in the segment of code immediately
    below it.
"""
from flask_wtf import Form
from flask import session
import time
from wtforms import StringField, PasswordField, SelectField, SelectMultipleField, widgets, TextAreaField
from wtforms.validators import DataRequired, email, EqualTo
from .models import User
from config import tutor_password, periods, period_names, subjects, subject_names, days_attended, admin_password


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(Form):
    """Checks if the username exists, then hashes the password and checks it against the username's password in db."""
    username = StringField('username', validators=[DataRequired("Please enter a username")])
    password = PasswordField('password', validators=[DataRequired("Please enter a password")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        """Redefine validate to take password into account."""
        if not Form.validate(self):
            return False

        user = User.query.filter_by(username=self.username.data.title()).first()
        if user is not None and user.check_password(self.password.data):
            return True
        else:
            self.username.errors.append("Invalid username or password")
            return False


class ChangePasswordForm(Form):
    """Checks if the username exists before creating the cookie in views.py."""
    username = StringField('username', validators=[DataRequired("Please enter a username")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(username=self.username.data.title()).first()
        if user is not None:
            return True
        else:
            self.username.errors.append("Please enter a valid username")
            return False


class OfficialPasswordResetForm(Form):
    """Compares the entered key-code (received via email) to the one stored on-site."""
    username = StringField('username', validators=[DataRequired("Please enter the username associated with your account")])
    code = StringField('crypto', validators=[DataRequired("Please enter the code you received via email")])
    password = PasswordField('password', validators=[DataRequired("Please enter a password")])
    password_check = PasswordField('password check', validators=[DataRequired("Please enter a password"), EqualTo('password', "Make sure your passwords match")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        """Redefine validate to take the cookie with crypto into account."""
        if not Form.validate(self):
            return False

        user = User.query.filter_by(email=session['email_check'][0]).all()

        if user is not None and (time.time() - session['email_check'][1] <= 300) and self.code.data == session['email_check'][2]:
            # checks to see if the time since the code was sent is less than 5 minutes (300s) and that the code enters matches the one sent
            return True
        else:
            self.code.errors.append("Either the code was wrong, or you waited too long.")
            return False


class StudentRegisterForm(Form):
    """Gets username, password, and email from the person registering.
        Also compares two passwords before validating.
    """
    username = StringField('username', validators=[DataRequired("Please Enter a Username"), ])
    password = PasswordField('password', validators=[DataRequired("Please enter a password")])
    password_check = PasswordField('password check', validators=[DataRequired("Please enter a password"), EqualTo('password', "Make sure your passwords match")])
    email = StringField('email', validators=[DataRequired("Please enter a valid email address"), email("Please enter a valid email address")])


class TutorRegisterForm(Form):
    """Checks if the entered code is the tutor code in config.py."""
    registration_code = StringField('registration code', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        if self.registration_code.data == tutor_password:
            return True
        else:
            self.registration_code.errors.append("Please enter the tutor code")
            return False


class AdminRegisterForm(Form):
    """Checks if the entered code is the admin code in config.py."""
    registration_code = StringField('registration code', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        if self.registration_code.data == admin_password:
            return True
        else:
            self.registration_code.errors.append("Please enter the admin code")
            return False


class FreePeriodsForm(Form):
    """Takes the day lengths from config.py and makes a table representative of the schedule.

        First, iterates through the length of each day, and makes a list of n lists, one for each day.
        Each inner list contains 2-tuples of the form (integer, period-name)

        Then, n fields of checkboxes are created, one for each day, with the number of rows corresponding to
        the number of periods in that day
    """
    total_choice_list = []
    field_list = []
    for day in periods:
        choice_list = []
        for i in range(day + 2): # +2 for before and after school
            if i == 0:
                to_append = (i, "Before School")
            elif i == day + 1:
                to_append = (i, "After School")
            else:
                to_append = (i, period_names[i-1])
            choice_list.append(to_append)
        total_choice_list.append(choice_list)

    v = 0
    for i in range(len(periods)):
        field_list.append(MultiCheckboxField(days_attended[i], coerce=int, choices=total_choice_list[v]))
        v += 1

# dynamically append days to FreePeriodsForm based upon config
for i in range(len(FreePeriodsForm.field_list)):
    setattr(FreePeriodsForm, days_attended[i], FreePeriodsForm.field_list[i])

class SubjectForm(Form):
    """Creates a table of subjects, organized by category (math, english, etc.).

        First, it iterates through the subject categories (subjects[i]), and then
        each subject in that category (subjects[i][x]).

        Second, it makes a list of lists of 2-tuples of the form (integer, subject).
        Each inner list is a category, and each tuple is a field in that category (a specific subject)

        Third, it makes a list of MultiCheckbox Fields, one for each category.

        Finally, outside the class, it appends each MultiCheckbox Field to the class using setattr.
    """
    total_choice_list = []
    field_list = []
    for i in range(len(subjects)):
        choice_list = []
        for x in range(len(subjects[i])):
            choice_list.append((x, subjects[i][x]))
        total_choice_list.append(choice_list)

    v = 0
    for i in range(len(subjects)):
        field_list.append(MultiCheckboxField(subject_names[i], coerce=int, choices=total_choice_list[v]))

        v += 1


# dynamically append subjects to SubjectForm based upon config
for i in range(len(SubjectForm.field_list)):
    setattr(SubjectForm, subject_names[i], SubjectForm.field_list[i])


class TutorRequestForm(Form):
    """Makes a dropdown of which subjects are available."""

    # make a list of subjects
    subject_list = []
    for i in range(len(subjects)):
        for x in range(len(subjects[i])):
            subject_list.append(subjects[i][x])

    # make a tuple (subject, subject) for each subject
    choice_list = [(subject, subject) for subject in subject_list]

    subject_request = SelectField(label='Select a Subject', coerce=str, choices=choice_list)



def create_tutor_selection_form():
    """Goes outside the TutorSelectionForm in order to pass a session variable to the form."""
    if 'tutor list' in session:
        if session['tutor list']:
            class TutorSelectionForm(Form):
                """Makes a table of tutors who can be selected."""

                choices = [(key, session['tutor list'][key][0]) for key in session['tutor list']]
                potential_tutors = MultiCheckboxField('Available Tutors', choices=choices)

            return TutorSelectionForm()

        else:
            return False


class MassEmailForm(Form):
    """Allows mass emailing of tutors/students/etc."""
    v = 0
    field_list = []
    for i in range(len(subjects)):
        field_list.append(MultiCheckboxField(subject_names[i], coerce=int, choices=SubjectForm.total_choice_list[v]))

        v += 1

    body = TextAreaField('body', validators=[DataRequired("Please enter some text to email")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)


# dynamically append subjects to SubjectForm based upon config
for i in range(len(SubjectForm.field_list)):
    setattr(MassEmailForm, subject_names[i], SubjectForm.field_list[i])
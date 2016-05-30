"""Database stuff."""
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from datetime import datetime, timedelta
from config import periods, subjects, labels, days_attended, subject_names, proto_labels, period_names, proto_attended

ROLE_USER = 0   
ROLE_TUTOR = 1
ROLE_ADMIN = 2

class IterMixin(object):
    """Allows iteration over variables in a class."""
    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

class QueryMixin(object):
    """Gives methods to query a database easily."""
    @classmethod
    def query_from_cookie(cls):
        if hasattr(cls, 'username'):
            return cls.query.filter_by(username=session['username']).first()
        else:
            return None

    @classmethod
    def create(cls, *args, commit=True):
        instance = cls(*args)
        return instance.save(commit=commit)

    def update(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self.save()

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    @classmethod
    def query_from_field(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()


    @classmethod
    def get_attrs(cls):
        """Return the variables names of each variable in the class."""
        return [attr for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("_")
                and not attr.endswith('_date') and attr != "id" and attr != "tutor_id" and attr != "tutor"
                and attr != "metadata" and attr != "query" and attr != "cal_type"]

    def attrs_to_list(self):
        """Return the values of each variable in the class."""
        attrs = self.get_attrs()
        attr_list = [dict(self)[attr] for attr in attrs]
        return attr_list


class User(db.Model, QueryMixin):
    """Database of users who can be students, tutors, or admins."""
    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.Date)
    username = db.Column(db.String(100), unique=True)
    user_type = db.Column(db.Integer)
    email = db.Column(db.String(120))
    pwdhash = db.Column(db.String(54))
    calendars = db.relationship('Calendar', backref='tutor', lazy='dynamic')
    subjects = db.relationship('Subjects', backref='tutor', lazy='dynamic')


    def __init__(self, username, password, user_type, email):
        self.username = username.title()
        self.user_type = user_type
        self.email = email.title()
        self.set_password(password)
        self.created = datetime.utcnow()

    def __repr__(self):
        return "<Username: {0}, Tutor: {1}>".format(self.username, self.user_type)

    def set_password(self, password):
        """Salts and hashes password."""
        self.pwdhash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the password against the database."""
        return check_password_hash(self.pwdhash, password)

    def get_calendar_0(self):
        """Returns the user's free periods calendar, if it exists."""
        return Calendar.query_from_field(tutor=self, cal_type=0)

    def get_calendar_1(self):
        """Returns the user's schedule calendar, if it exists."""
        return Calendar.query_from_field(tutor=self, cal_type=1)

    def get_subjects(self):
        """Returns the subject table associated with the user."""
        return Subjects.query_from_field(tutor=self)

    def get_business_value(self):
        """Returns a ratio of free periods and available periods.

            Used to rank the relative busy-ness of tutors.
        """
        free_cal = self.get_calendar_0() # when you're theoretically free
        available_cal = self.get_calendar_1() # when you're actually available

        attrs = Calendar.sort_attrs()
        free = 1
        available = 0
        for attr in attrs:
            free_value = getattr(free_cal, attr)
            available_value = getattr(available_cal, attr)
            if free_value:
                free += 1
            if not available_value:
                available += 1

        ratio = available/free
        return ratio


class Subjects(db.Model, IterMixin, QueryMixin):
    """Database of subjects relatively linked to their tutors.

        Some of the database construction had to be generalized, and so could not be done
        explicitly in this class. Instead, in data.py, a function defines it implicitly using
        setattr.
    """
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.uid'))


    def __init__(self, tutor):
        self.tutor = tutor


    def get_data_list(self):
        """Return a list of which subjects are tutorable."""
        categories = []
        attrs = self.sort_attrs()
        for (i, subject) in enumerate(attrs):
            category_list = []
            for (n, course) in enumerate(subject):
                if dict(self)[course]:
                    category_list.append(n)
                categories.append(category_list)

        return categories

    def get_data_dict(self):
        """Return a dict of which subjects can be tutored by the user."""
        categories = {}
        attrs = self.sort_attrs()
        for (i, subject) in enumerate(attrs):
            category_list = []
            for (n, course) in enumerate(subject):
                if dict(self)[course]:
                    category_list.append(n)
                categories[subject_names[i]] = category_list

        return categories

    @classmethod
    def sort_attrs(cls):
        """Takes a list of attributes and sorts them as in config."""
        final_list = []
        for subject in subjects:
            buffer = []
            for (i, course) in enumerate(subject):
                for attr in cls.get_attrs():
                    if attr == course.replace(" ", ""):
                        buffer.insert(i, attr)
            final_list.append(buffer)
        return final_list



class Calendar(db.Model, IterMixin, QueryMixin):
    """Database of tutor's schedules.

        Some of the database construction had to be generalized, and so could not be done
        explicitly in this class. Instead, in data.py, a function defines it implicitly using
        setattr.
    """
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.uid'))
    cal_type = db.Column(db.Integer)

    def __init__(self, tutor, cal_type=0): # 0: user defined calendar, 1: availability
        self.tutor = tutor  # Tutor can be any user (student, tutor, admin), despite the name
        self.cal_type = cal_type
        if cal_type == 0:
            for attr in self.sort_attrs():
                setattr(self, attr, 0)
        elif cal_type == 1:
            for attr in self.sort_attrs():
                self.set_1(attr)


    def __repr__(self):
        iteratable = [attr + ": " + str(getattr(self, attr)) + "| Expires: " + str(self.get_date(attr))
                      for attr in self.sort_attrs()]

        return "\n".join(iteratable)

    def get_date(self, attr):
        """Returns the date variable associated with an attribute attr."""
        return getattr(self, attr+'_date')

    def set_1(self, attr):
        """Sets the given attr to 1, and removes its expiration."""
        setattr(self, attr, 1)
        setattr(self, attr+'_date', None)

    def set_0(self, attr, weeks=1):
        """Sets a given attr to 0 with expiration date.

            by default, the expiration date is however many weeks ahead
            are specified in the config.
        """
        setattr(self, attr, 0)
        difference = self.get_next_weekday(attr)

        difference += timedelta(weeks=weeks)
        setattr(self, attr+'_date', difference.date())

    def get_next_weekday(self, attr):
        """Returns the datetime for the next time this weekday appears."""
        day = proto_labels.index(attr[0])  # gets the day value associated with the period.
        days_left = day - datetime.utcnow().weekday()
        if days_left <= 0:
            days_left += 7
        return datetime.utcnow() + timedelta(days_left)

    def check_expiration(self):
        """Checks the expiration on every attribute, and sets the attr to 1 if it's past the date."""
        attrs = [attr for attr in self.sort_attrs()]
        for attr in attrs:
            if getattr(self, attr+'_date'):
                try:
                    if datetime.utcnow().date() > self.get_date(attr):
                        self.set_1(attr)
                        db.session.commit()
                except TypeError:
                    print('type error on {0}'.format(attr))


    def check_weekday(self):
        """Checks if today is the same day that a user is busy, returns a list of tuples (user, attr)."""
        attrs = [attr for attr in self.sort_attrs()]
        final = []
        for attr in attrs:
            if getattr(self, attr+'_date'):
                if datetime.utcnow().weekday() == self.get_date(attr).weekday():
                    period = attr[1]
                    if period == 'B':
                        period = 'Before School'
                    elif period == 'A':
                        period = 'After School'
                    else:
                        try:
                            period = period_names[int(period) - 1]
                        except TypeError:
                            print('period name did not include an integer. {0}'.format(period))
                    final.append(period)
        return final



    def get_data_list(self):
        """Returns a list of lists of data."""
        categories = []
        attrs = self.sort_attrs()
        for (i, label) in enumerate(labels):
            day_list = []
            for attr in attrs:
                if attr.startswith(label):
                    if dict(self)[attr]:
                        if attr.endswith('B'):
                            day_list.append(0)
                        elif attr.endswith('A'):
                            day_list.append(periods[i]+1)
                        else:
                            day_list.append(int(attr[-1]))
            categories.append(day_list)
        return categories

    def get_data_dict(self, weeks=0):
        """Returns a dictionary of lists of the data."""
        categories = {}
        attrs = self.sort_attrs()
        for (i, label) in enumerate(labels):
            day_list = []
            for attr in attrs:
                if attr.startswith(label):
                    if dict(self)[attr]:
                        if attr.endswith('B'):
                            day_list.append(0)
                        elif attr.endswith('A'):
                            day_list.append(periods[i]+1)
                        else:
                            day_list.append(int(attr[-1]))
                    categories[days_attended[i]] = day_list

        return categories

    @classmethod
    def sort_attrs(cls):
        """Returns every available period, sorted, as one list.

        i.e. [MB, M1, M2, MA, TB, T1, T2... FA]
        """
        M = []
        T = []
        W = []
        R = []
        F = []
        S = []
        U = []

        day_dict = {'M': M, 'T': T, 'W': W, 'R': R, 'F': F, 'S': S, 'U': U}

        for attr in cls.get_attrs():
            for letter in labels:
                if str(attr).startswith(letter):
                    if str(attr).endswith('B'):
                        day_dict[letter].insert(0, attr)
                    elif str(attr).endswith('A'):
                        day_dict[letter].append(attr)
                    else:
                        index = int(str(attr)[-1])
                        day_dict[letter].insert(index, attr)

        final_list = []
        # print('--')
        for letter in labels:
            for i in day_dict[letter]:
                # print(i)
                final_list.append(i)
        # print('--')
        return final_list

    @classmethod
    def get_attrs_list(cls):
        """Returns every available period sorted into lists of lists.

        i.e. [[MB, M1, M2, MA], [TB, T1, TA]]
        """
        M = []
        T = []
        W = []
        R = []
        F = []
        S = []
        U = []

        day_dict = {'M': M, 'T': T, 'W': W, 'R': R, 'F': F, 'S': S, 'U': U}

        for attr in cls.get_attrs():
            for letter in labels:
                if str(attr).startswith(letter):
                    if str(attr).endswith('B'):
                        day_dict[letter].insert(0, attr)
                    elif str(attr).endswith('A'):
                        day_dict[letter].append(attr)
                    else:
                        index = int(str(attr)[-1])
                        day_dict[letter].insert(index, attr)

        final_list = []
        for letter in labels:
            if day_dict[letter]:
                final_list.append(day_dict[letter])
        return final_list


class StudentTutorPairings(db.Model, IterMixin):
    """Stores the list of every student - tutor - subject - date pair.


    """
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String)
    tutor = db.Column(db.String)
    subject = db.Column(db.String)
    date = db.Column(db.Date)
    active = db.Column(db.Integer)
    date_str = db.Column(db.String)
    day = db.Column(db.String)
    period = db.Column(db.Integer)

    def __init__(self, student, tutor, subject, date, period):
        self.student = student
        self.tutor = tutor
        self.subject = subject
        self.date = date
        self.date_str = str(date)
        self.active = 1
        self.day = proto_attended[date.weekday()]
        self.period = period

    def __repr__(self):
        return "<Student: {0}, Tutor: {1}, Subject: {2}, Date: {3}>".format(
            self.student, self.tutor, self.subject, self.date)

    def deactivate(self):
        if datetime.now() < self.date:
            self.active = 0
"""Configuration file for the website.

    ===========================================
    You should read this before you play around
    ===========================================
    These are the instructions
    ===========================================
    Seriously. They're short. Do it <3
    ===========================================

    Stuff that should be changed is on top,
    Stuff that can be changed in some cases is near the middle,
    Stuff that you probably shouldn't mess with is at the bottom.

    Variable names are fairly self explanatory, but I commented
    everything just in case.

    You can change the homepage text by editing homepage_text.txt
    Any html will render fine.
    i.e.
    if you want a new line, put <br> where you want it.
    if you want italics, <i> will work fine.
    links? <a> is your friend.

    You can change the banner in the top left by making a new image.
    The image goes in app/static/images
    The name must be banner.jpg, and dimensions are (728x90)

    If there isn't an image in the folder, the link will be displayed as
    NHS Tutoring

    Also, putting a favicon.ico into the app/static/images folder
    will make a favicon.

    If you ever want to totally reset the database, and therefore
    all the students, tutors, etc. who are registered,
    delete the app.db file that will be created when you first run the program.

    You will have to do this every time you make a change to the database layout:
    i.e.
    - change the number of school days or periods
    - change which classes are offered

    Warning, though! This is not reversible. Make a backup of the app.db before
    you do so.


    As a whole, if you follow the pattern that's already here,
    it should work fine. :)
"""
import os

#The passwords to become a tutor/admin
#Change these to whatever you want.
#To become and admin, navigate to YourWebsite/admin
#there is no link to this page by default to discourage
#other students from trying to guess the password
tutor_password = 'imatutor'
admin_password = 'somecomplexstring'

#A key to prevent cross site request forgery. Make it something decently complex that isn't this,
#becuase this one is on github, etc.
#If you're too lazy to come up with something yourself, I suggest:
#random.org/strings
#Just say to use 20 characters, all the character types, and paste it in.
#Whatever you do, though, make sure something is here THAT ISN'T THIS.
SECRET_KEY = 'WE2SZqXxV4QzWaj49ha4Dja3sNZurvej99RBDYWsMGr26tjh2thF7aCNhLzdprvmKet3ryr8'


#This is the name that is printed as a contact
#if there aren't any available tutors for 
#a particular subject and period. I suggest
#making it the head of your NHS chapter.
tutoring_head = 'Ms. Williams'

#This is the email of whoever you want to receive
#an email every time a new tutoring assignment
#is created.
#To have multiple recipients, add another member
#to the list.
#If the list is empty, nobody will receive
#these emails, however the information
#will still be stored in the log file.
tutoring_head_email = ['Willims@someemail.com']


#Display the tutor's name in the tutor selection screen.
#0 = no, 1 = yes
display_tutor_name = 1


#Allows the password reset form I created.
#I'm allowing this as a setting because it's mildly insecure, and doesn't work in all situations.
#I'm fine with this, because NHS should be a pretty low security risk thing,
#but if you're really worried about people doing cookie manipulation to break the site,
#then definitely set this to 0 :)
allow_password_reset = 1


#Number of periods in each day.
#0 will make that day not appear on the website
monday_periods = 8
tuesday_periods = 8
wednesday_periods = 4
thursday_periods = 4
friday_periods = 8
saturday_periods = 0
sunday_periods = 0

#subjects in each category
#make sure each name is alphanumeric (spaces are ok)

#IMPORTANT:
#Adding or removing classes from an existing
#category is easy.
#I.E.
#If your school doesn't offer Calculus,
#just delete "Calculus" from the list.
#If your school offers German,
#Go ahead and put German into the languages category.

#HOWEVER:
#If you want to add or remove a category,
#I.E.
#If your school wants to add an engineering category,
#In addition to adding a list for engineering_subjects,
#You need to add the tuple 
#("engineering", engineering_subects) 
#to subject_names provided below.
#If you don't, things WILL break.

math_subjects = [
    "Algebra 1",
    "Geometry",
    "Algebra 2",
    "PreCalculus",
    "Calculus",
    "Statistics",
    "Computer Science",
]

english_subjects = [
    "English 9",
    "English 10",
    "English 11",
    "English 12",
    "Essay Review"
]

language_subjects = [
    "Spanish",
    "French",
    "Chinese",
    "Latin",
]

social_subjects = [
    "World Civ 1",
    "World Civ 2",
    "US History",
    "Government",
    "Civics",
    "Law"
]

science_subjects = [
    "IPS",
    "Biology",
    "Chemistry",
    "Physics",
    "Psychology",
    "Sociology"
]

#included categories.
#if you add a category above, you must include it here.
#the format is ("category name", category_list)
included_subjects = [
    ("math", math_subjects),
    ("english", english_subjects),
    ("language", language_subjects),
    ("social studies", social_subjects),
    ("science", science_subjects)
]


#confirmation email messages
#the things in {} will be changed with a .format later, so don't change/remove/add any of those
#unless you modify the parts of views.py that send emails accordingly. :)
#Everything else is fair game to write as you see fit.
confirmation = "Thank you, {username}, for signing up for Simsbury Tutoring"

#Note WEBSITE must be changed to your actual website. The program will not do that for you.
password_change = "Please navigate to WEBSITE/reset and enter the following code: \n {code}" \
                  "\n If you did not request a password reset, please ignore this message."

sent_to_tutor = "You have been chosen to tutor {student} (email: {email}) in {subject} on {date}, {period_number}."

sent_to_student = "You have chosen to be tutored by {tutor} (email: {email}) in {subject} on {date}, {period_number}."

reminder = "This is a reminder that you are to meet in the library {period} today for tutoring."


#If you're using gmail as your email service,
#you can use the below settings.
#If not, a quick google search for smtplib
#will put you on the right path :)

MY_EMAIL = "your-email-here@gmail.com"  # The gmail account you're using
EMAIL_SERVER = "smtp.gmail.com:587"  # You probably shouldn't touch this
EMAIL_USERNAME = "your-email-username"  # The username for your gmail account
EMAIL_PASSWORD = "your-email-password"  # The password for your gmail account


#The name of your tutoring service. 
#This is what will show up as the subject of emails
tutoring_service_name = "Simsbury Tutoring"



#period names. add more if you end up with more than 12 periods in a day
period_names = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"]

#===============================#
#The land of please-do-not-touch#
#===============================#

#proto lists include a value for every weekday.
#Then periods, labels, and days_attended update if the cfg values for the number of periods is non 0.
proto_periods = [monday_periods, tuesday_periods, wednesday_periods,
                 thursday_periods, friday_periods, saturday_periods, sunday_periods]
proto_labels = ['M', 'T', 'W', 'R', 'F', 'S', 'U']
proto_attended = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

periods = [proto_periods[i] for i in range(7) if proto_periods[i]]
labels = [proto_labels[i] for i in range(7) if proto_periods[i]]
days_attended = [proto_attended[i] for i in range(7) if proto_periods[i]]

#Separates the user-friendly list of tuples into two related lists for easy coding.
subject_names = []
subjects = []
for name, value in included_subjects:
    subject_names.append(name)
    subjects.append(value)

#Dynamically sets the base directory so the website will correctly establish a database location.
basedir = os.path.abspath(os.path.dirname(__file__))

#JSON path location so that the StudentTutorPairings can correctly establish a location
JSON_location = os.path.join(basedir, 'app', 'static', 'JSON_STP.json')

def get_homepage_text():
    """Returns the text in homepage_text.txt"""
    homepage_document = open("homepage_text.txt", 'r')
    raw_text = homepage_document.read()
    homepage_document.close()

    return raw_text

#The description won't fit in the margin... google these.

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

CSRF_ENABLED = True
SQLALCHEMY_ECHO = False

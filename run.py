"""Updates the database, then runs the server."""
from app import app, db
from app.data import update_environment_variables, update_subjects, update_calendar, _jinja2_datetime_filter

update_environment_variables(app)
update_subjects()
update_calendar()
db.create_all()
app.jinja_env.filters['date'] = _jinja2_datetime_filter
app.run(host="0.0.0.0")

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length

class TipForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10)])
    odds = StringField("Odds", validators=[DataRequired()])
    sport = SelectField("Sport", choices=[('football', 'Football'), ('basketball', 'Basketball'), ('tennis', 'Tennis')])
    #match_date = DateTimeField("Match Date & Time", format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField("Post Tip")

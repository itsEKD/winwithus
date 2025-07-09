from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length

class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5, max=100)])
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=20)])
    
    # Add image field using FileField
    image = FileField("Image", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed.')
    ])

    submit = SubmitField("Publish Post")

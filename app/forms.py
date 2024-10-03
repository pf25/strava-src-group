from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class EditGroupForm(FlaskForm):
    group = SelectField('Group', choices=[('North Austin', 'North Austin'), 
                                          ('South Austin', 'South Austin'), 
                                          ('Others', 'Others')], 
                        validators=[DataRequired()])
    submit = SubmitField('Save')

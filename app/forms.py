
from flask.ext.wtf import Form
from wtforms.fields import TextField, HiddenField, FileField, RadioField, SelectField, TextAreaField, StringField, PasswordField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, ValidationError
from models import db
from sqlalchemy.sql import text

def phoneCheck(form, field):
	phone = ""
	for each in field.data:
		if each != "(" and each != ")" and each != "-":
			phone += each
	for each in phone:
			if each.isdigit() == False:
				raise ValidationError('Please input a valid phone number.')
	if len(phone) != 10:
		raise ValidationError("Please make sure to include only ten digits.")

def uniqueCheck(form, field):
	input = field.data
	counter = 0

	connection = db.engine.connect()
	result = connection.execute(text('SELECT phone FROM Users WHERE phone = :input'), input = input)

	for each in result:
		counter = counter + 1	
		print each
	if counter == 0:
		print "Looks good! :D"
	else:
		raise ValidationError("Looks like that phone number is in use. Try another one?")


def sanitize(form, field):
	unusableChars = ['<', '>', '=', '*', '+',"""'"""]
	for each in field.data:
		if each in unusableChars:
			raise ValidationError("Please remove all instances of " + each + ".")
			
class JoinForm(Form):
	fname = StringField('fname', validators=[DataRequired(), sanitize])
	lname = TextField('lname', validators=[DataRequired(), sanitize])

	year = SelectField('year', validators=[DataRequired(), sanitize], choices=[(' ', ' '),('Freshman', 'Freshman'), ('Sophomore', 'Sophomore'), ('Junior', 'Junior'), ('Senior', 'Senior'), ('Fifth Year', 'Fifth Year'), ('Sixth Year', 'Sixth Year')])
	major = TextField('major', validators=[DataRequired(), sanitize])
	focus = TextField('focus', validators=[DataRequired(), sanitize])

	phone = TextField('phone', validators=[DataRequired(), sanitize, phoneCheck, uniqueCheck])
	email = TextField('email', validators=[DataRequired(), Email(), sanitize])
	cantext = RadioField('cantext', validators=[DataRequired(), sanitize], choices=[('Yes', 'Yes'), ('No', 'No')], default='Yes')

	about = TextAreaField('about', validators=[DataRequired(), sanitize])

   	password = PasswordField('password', validators=[DataRequired(), sanitize])

class ValidateForm(Form):
	validationCode = StringField('validationCode', validators=[DataRequired(), sanitize])

class SprocketForm(Form):
	phoneInput = StringField('phoneInput', validators=[DataRequired(), sanitize, phoneCheck])
	password = PasswordField('password', validators=[DataRequired(), sanitize])

class CreateEvent(Form):
	title = StringField('title', validators=[DataRequired(), sanitize])
	date = DateField('date', validators=[DataRequired()])
	time = StringField('time', validators=[DataRequired(), sanitize])
	shortDescription = StringField('shortDescription', validators=[DataRequired(), sanitize])
	description = TextAreaField('description', validators=[DataRequired(), sanitize])
	eventPicture = FileField('eventPicture', validators=[DataRequired()])
	address = StringField('address', validators=[DataRequired(), sanitize])
	featured = RadioField('featured', validators=[DataRequired(), sanitize], choices=[('1', 'Yes'), ('0', 'No')])
	buzzword = StringField('buzzword', validators=[DataRequired(), sanitize])

class Notify(Form):
	members = BooleanField('members')
        marketing = BooleanField('marketing')
        manual = BooleanField('manual')
	manualNumbers = TextField("messageList", validators=[sanitize])
	message = TextAreaField('message', validators=[DataRequired(), sanitize])
	emailMessage = BooleanField('emailMessage')
	textMessage = BooleanField('textMessage')

class MarketingList(Form):
	addrm = RadioField('addrm', validators=[DataRequired(), sanitize], choices=[('Add', 'Add'), ('Remove', 'Remove')], default='Add')
	fname = StringField('fname', validators=[DataRequired(), sanitize])
	lname = StringField('lname', validators=[DataRequired(), sanitize])
	phone = StringField('phone', validators=[DataRequired(), sanitize, phoneCheck])
	email = StringField('email', validators=[DataRequired(), Email(), sanitize])

import os
from app import app
from flask import redirect, session, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash, secure_filename
from random import randint
from sqlalchemy.sql import text

db = SQLAlchemy()

UPLOAD_FOLDER = '/static/events'
ALLOWED_EXTENSIONS = set(['doc', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def setPassword(password):
	return generate_password_hash(password)

def checkPassword(password):
	return check_password_hash(password)

def generateShortID():
	hash = randint(10000, 99999)
	return hash

def generateLongID():
	hash = randint(10000000, 99999999)
	return hash

def sanitary(input):
        unusableChars = ['<', '>', '=', '*', '+',"""'"""]
	
	if input == None:
		return True        
	input = str(input)
	for each in input:
                if each in unusableChars:
                        return False
	return True

def getSQLList(rows):
	result = []
        for row in rows:
                for each in row:
                        result.append(each)
	return result

def getSQLDict(row):
	l = []
	for each in row:
		row_as_dict = dict(each)
		l.append(row_as_dict)
	return l

def loginCheck():
	sql = "SELECT loginid FROM Users WHERE loginid = :input"
	connection = db.engine.connect()
	try:
		if session['id'] and sanitary(session['id']):
                	input = session['id']
        	else:
             		session['id'] = None
			return False
		result = getSQLList(connection.execute(text(sql), input = input))
	
		if input in result:
			return True
		else:
			return False
	except KeyError:
		session['id'] = None
		return False

def adminLoginCheck():
	
        sql = "SELECT loginid FROM Users WHERE loginid = :input AND level = 1"
        connection = db.engine.connect()
        try:
                if session['id'] and sanitary(session['id']):
                        input = session['id']
                else:
                        session['id'] = None
                        return False
                result = getSQLList(connection.execute(text(sql), input = input))

                if input in result:
                        return True
                else:
                        return False
        except KeyError:
                session['id'] = None
                return False

def allowed_file(filename):
    		return '.' in filename and \
			filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def uploadFile(inputFile):
	if inputFile and allowed_file(inputFile.filename):
		filename = secure_filename(inputFile.filename)
		inputFile.save(os.path.join("/var/www/Sprocket/app/static/events", filename))
		return filename
	else:
		return None

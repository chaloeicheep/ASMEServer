import os
from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename
from flask_mail import Mail

UPLOAD_FOLDER = '/var/www/Sprocket/app/static/events'
ALLOWED_EXTENSIONS = set(['doc', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

app.config.from_object('config')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:YaleKing@localhost/maindb'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'asme.sjsu@gmail.com'
app.config['MAIL_PASSWORD'] = 'Snps!2345'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['DEBUG'] = True

from models import db
db.init_app(app)

mail = Mail(app)

from app import views

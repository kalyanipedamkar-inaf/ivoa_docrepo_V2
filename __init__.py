import os
import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



app = Flask(__name__)

# The UPLOAD_DIR folder contains all the .zip and .tar files that are uploaded by the app. 
# The uploaded .zip or .tar files are first saved in this folder. It can also be used as a backup of the uploaded documents
UPLOAD_DIR = '/var/www/html/docrepo/uploads'

# The 'documents' folder has the extracted files from the 'uploads'. 
# This is the main repository where the documents will be saved.
documents = '/var/www/html/docrepo/documents'

app.config['SECRET_KEY'] = 'SECRET_KEY'
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.zip','.tar']
app.config['UPLOAD_DIR'] = UPLOAD_DIR

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' +os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Migrate(app,db)

from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
#from app import views, models
#from flask_bootstrap import Bootstrap
import os
from flask_bcrypt import Bcrypt

webapp = Flask(__name__)


bcrypt = Bcrypt(webapp)

webapp.config['UPLOAD_FOLDER'] = os.getcwd()+'/app/static/images_uploaded'
webapp.config['SECRET_KEY'] = 'this is a secret string'

#Bootstrap(webapp)

from app import views
from app import userforms
from app import userpage
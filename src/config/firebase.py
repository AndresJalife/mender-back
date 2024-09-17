from firebase_admin import credentials
from pyrebase import pyrebase
import json
import firebase_admin
import os
######################################### Initialize Firebase

cred = credentials.Certificate(os.environ.get('GOOGLE_CREDS'))
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open(os.environ.get('FIREBASE_CONFIG'))))

########################################
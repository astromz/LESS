from flask import Flask
app = Flask(__name__)  # creates the application object
from app import views  # views are the handlers that respond to requests from web browsers

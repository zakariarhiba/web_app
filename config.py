import os

DB_USER = 'root'
DB_PASS = '@Passw0rd123'
DB_NAME = 'healthconnectdb'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://{DB_USER}:{DB_PASS}@localhost/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
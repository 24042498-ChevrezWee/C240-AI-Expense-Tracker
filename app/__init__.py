import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS

# Initialize the SQLAlchemy extension
db = SQLAlchemy()

def create_app():
    # Load environment variables from a .env file
    load_dotenv()
    
    app = Flask(__name__)

    CORS(app)
    
    # Configure the database connection using PyMySQL
    # Make sure to create a .env file with your DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'mysql+pymysql://user:password@localhost/dbname'
    )
    # Disable tracking modifications to save memory
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize plugins
    db.init_app(app)
    
    # Register Blueprints
    with app.app_context():
        from app.routes import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        
    return app
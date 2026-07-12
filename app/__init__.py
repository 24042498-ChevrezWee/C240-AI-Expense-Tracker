import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS
from sqlalchemy import inspect, text

# Initialize the SQLAlchemy extension
db = SQLAlchemy()


def create_app(test_config=None):
    # Load environment variables from a .env file
    load_dotenv()

    app = Flask(__name__)

    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        test_config.get('SQLALCHEMY_DATABASE_URI')
        if test_config else os.environ.get(
            'DATABASE_URL',
            'mysql+pymysql://user:password@localhost/dbname'
        )
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = test_config.get('TESTING', False) if test_config else False

    # Initialize plugins
    db.init_app(app)

    # Register Blueprints
    with app.app_context():
        from app.routes import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        db.create_all()

        inspector = inspect(db.engine)
        if 'receipts' in inspector.get_table_names():
            receipt_columns = {column['name'] for column in inspector.get_columns('receipts')}
            if 'amount_in_sgd' not in receipt_columns:
                db.session.execute(text('ALTER TABLE receipts ADD COLUMN amount_in_sgd NUMERIC(10, 2)'))
                db.session.commit()

        from app.models import User
        from werkzeug.security import generate_password_hash

        existing_user = User.query.filter_by(email='demo@example.com').first()
        if not existing_user:
            demo_user = User(
                email='demo@example.com',
                password_hash=generate_password_hash('password123'),
                first_name='Demo',
                last_name='User',
            )
            db.session.add(demo_user)
            db.session.commit()

    return app
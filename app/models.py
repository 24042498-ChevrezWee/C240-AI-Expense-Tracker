from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    receipts = db.relationship('Receipt', backref='user', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    receipts = db.relationship('Receipt', backref='category', lazy=True)

class Currency(db.Model):
    __tablename__ = 'currencies'

    currency_code = db.Column(db.String(3), primary_key=True)
    currency_name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    receipts = db.relationship('Receipt', backref='currency', lazy=True)

class Receipt(db.Model):
    __tablename__ = 'receipts'

    receipt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    merchant_name = db.Column(db.String(255))
    receipt_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(10, 2))
    amount_in_sgd = db.Column(db.Numeric(10, 2))
    currency_code = db.Column(db.String(3), db.ForeignKey('currencies.currency_code'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    receipt_image_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
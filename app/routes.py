import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Category, Currency, Receipt
from app.services import extract_receipt_data
from app.currency_service import convert_amount_to_sgd, normalize_currency_code


def _serialize_receipt(receipt):
    original_amount = float(receipt.total_amount or 0)
    normalized_currency = normalize_currency_code(receipt.currency_code)

    if receipt.amount_in_sgd is not None:
        amount_in_sgd = float(receipt.amount_in_sgd)
    else:
        converted_amount = convert_amount_to_sgd(original_amount, normalized_currency)
        if converted_amount is not None:
            amount_in_sgd = float(converted_amount)
        else:
            # Preserve stability when rates are unavailable; avoid inflating SGD totals with foreign raw values.
            amount_in_sgd = original_amount if normalized_currency == "SGD" else 0.0

    return {
        "id": receipt.receipt_id,
        "merchant": receipt.merchant_name or "Not available",
        "category": receipt.category.category_name if receipt.category else "Uncategorized",
        "amount": original_amount,
        "amountInSgd": amount_in_sgd,
        "currency": normalized_currency,
        "date": receipt.receipt_date.strftime("%Y-%m-%d") if receipt.receipt_date else "",
    }


def _build_dashboard_payload(user_id):
    receipts = (
        Receipt.query.filter_by(user_id=user_id)
        .order_by(Receipt.created_at.desc())
        .all()
    )

    if not receipts:
        return {
            "totalExpenses": 0,
            "receiptCount": 0,
            "monthlySpending": 0,
            "topCategory": "-",
            "largestExpense": "-",
            "averageExpense": 0,
            "categories": [],
            "recentReceipts": [],
        }

    serialized_receipts = [_serialize_receipt(receipt) for receipt in receipts]
    totals_by_category = {}
    total_expenses = 0
    monthly_spending = 0
    largest_expense = None

    today = datetime.utcnow()
    for receipt in serialized_receipts:
        amount_in_sgd = receipt["amountInSgd"]
        total_expenses += amount_in_sgd
        if receipt["date"]:
            receipt_date = datetime.strptime(receipt["date"], "%Y-%m-%d")
            if receipt_date.year == today.year and receipt_date.month == today.month:
                monthly_spending += amount_in_sgd

        category_name = receipt["category"] or "Uncategorized"
        category_entry = totals_by_category.setdefault(category_name, {"name": category_name, "total": 0, "count": 0})
        category_entry["total"] += amount_in_sgd
        category_entry["count"] += 1

        if largest_expense is None or amount_in_sgd > largest_expense["amountInSgd"]:
            largest_expense = receipt

    categories = sorted(totals_by_category.values(), key=lambda item: item["total"], reverse=True)

    return {
        "totalExpenses": round(total_expenses, 2),
        "receiptCount": len(serialized_receipts),
        "monthlySpending": round(monthly_spending, 2),
        "topCategory": categories[0]["name"] if categories else "-",
        "largestExpense": f"SGD {largest_expense['amountInSgd']:.2f}" if largest_expense else "-",
        "averageExpense": round(total_expenses / len(serialized_receipts), 2) if serialized_receipts else 0,
        "categories": categories,
        "recentReceipts": serialized_receipts[:5],
    }


def _friendly_error(message, status_code=500):
    return jsonify({"error": message}), status_code


def _clear_receipt_related_data():
    deleted_receipts = Receipt.query.delete()

    unused_categories = (
        Category.query.outerjoin(Receipt, Category.category_id == Receipt.category_id)
        .filter(Receipt.receipt_id.is_(None))
        .all()
    )
    deleted_categories = len(unused_categories)
    for category in unused_categories:
        db.session.delete(category)

    unused_currencies = (
        Currency.query.outerjoin(Receipt, Currency.currency_code == Receipt.currency_code)
        .filter(Receipt.receipt_id.is_(None))
        .all()
    )
    deleted_currencies = len(unused_currencies)
    for currency in unused_currencies:
        db.session.delete(currency)

    return {
        "deletedReceipts": deleted_receipts,
        "deletedCategories": deleted_categories,
        "deletedCurrencies": deleted_currencies,
    }

api_bp = Blueprint('api', __name__)

# Configure Upload Folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Creates the folder if it doesn't exist

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/status', methods=['GET'])
def health_check():
    return jsonify({
        "status": "success",
        "message": "AI Receipt & Expense Tracker API is running perfectly."
    }), 200


@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return _friendly_error("Please enter your email and password.", 400)

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return _friendly_error("Invalid email or password", 401)

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }), 200


@api_bp.route('/dashboard', methods=['GET'])
def dashboard_summary():
    user_id = request.args.get('user_id')
    if not user_id:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    user = db.session.get(User, int(user_id))
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    return jsonify(_build_dashboard_payload(user.user_id)), 200


@api_bp.route('/receipts', methods=['GET'])
def list_receipts():
    user_id = request.args.get('user_id')
    if not user_id:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    user = db.session.get(User, int(user_id))
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    receipts = (
        Receipt.query.filter_by(user_id=user.user_id)
        .order_by(Receipt.created_at.desc())
        .all()
    )
    return jsonify([_serialize_receipt(receipt) for receipt in receipts]), 200


@api_bp.route('/clear-data', methods=['POST'])
def clear_data():
    try:
        result = _clear_receipt_related_data()
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "All receipt data has been cleared.",
            "data": result,
        }), 200
    except Exception:
        db.session.rollback()
        return _friendly_error("We couldn’t clear receipt data right now. Please try again shortly.", 500)


@api_bp.route('/upload', methods=['POST'])
def upload_receipt():
    # 1. Validate the Request
    if 'file' not in request.files:
        return _friendly_error("No receipt file was provided. Please choose a file and try again.", 400)
    
    file = request.files['file']
    user_id = request.form.get('user_id')

    if file.filename == '':
        return _friendly_error("No receipt file was selected. Please choose a file and try again.", 400)
        
    if not user_id:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    # Ensure user exists before processing
    user = db.session.get(User, user_id)
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    # 2. Save the File Locally
    if file and allowed_file(file.filename):
        # Create a unique filename to prevent overwriting
        filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file.filename}")
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 3. Call the AI Extraction Service
        try:
            extracted_data = extract_receipt_data(file_path)
        except Exception:
            return _friendly_error("We couldn’t read the receipt. Please try a clearer image or upload again.", 500)
            
        # Safely extract data from the AI response
        merchant_name = extracted_data.get('merchant_name') if isinstance(extracted_data, dict) else None
        receipt_date_str = extracted_data.get('receipt_date') if isinstance(extracted_data, dict) else None
        total_amount = extracted_data.get('total_amount') if isinstance(extracted_data, dict) else None
        raw_currency_code = (extracted_data.get('currency_code') or 'USD') if isinstance(extracted_data, dict) else 'USD'
        currency_code = normalize_currency_code(raw_currency_code)
        category_name = (extracted_data.get('category_name') or 'Uncategorized') if isinstance(extracted_data, dict) else 'Uncategorized'
        amount_in_sgd = convert_amount_to_sgd(total_amount, currency_code)
        
        # Parse date string to Python Date object
        try:
            receipt_date = datetime.strptime(receipt_date_str, '%Y-%m-%d').date() if receipt_date_str else None
        except ValueError:
            receipt_date = None

        # 4. Database Operations
        try:
            # Check if Currency exists, otherwise create it
            currency = db.session.get(Currency, currency_code)
            if not currency:
                currency = Currency(
                    currency_code=currency_code,
                    currency_name=f"{currency_code} Currency"
                )
                db.session.add(currency)
            
            # Check if Category exists, otherwise create it
            category = Category.query.filter(Category.category_name.ilike(category_name)).first()
            if not category:
                category = Category(
                    category_name=category_name,
                    description="Auto-generated by AI"
                )
                db.session.add(category)
                db.session.flush()
            
            new_receipt = Receipt(
                user_id=user.user_id,
                merchant_name=merchant_name,
                receipt_date=receipt_date,
                total_amount=total_amount,
                amount_in_sgd=amount_in_sgd,
                currency_code=currency.currency_code,
                category_id=category.category_id,
                receipt_image_path=file_path
            )
            
            db.session.add(new_receipt)
            db.session.commit()
            
            # 5. Return Success Response
            return jsonify({
                "status": "success",
                "message": "Receipt processed and saved successfully.",
                "data": {
                    "receipt_id": new_receipt.receipt_id,
                    "merchant_name": merchant_name,
                    "receipt_date": receipt_date_str,
                    "total_amount": total_amount,
                    "currency": currency_code,
                    "amount_in_sgd": amount_in_sgd,
                    "category": category_name
                }
            }), 201

        except Exception:
            db.session.rollback()
            return _friendly_error("We couldn’t save the receipt right now. Please try again shortly.", 500)

    return _friendly_error("Please upload a JPG, PNG, or PDF receipt.", 400)
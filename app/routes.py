import os
import re
from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
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


def _is_valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def _split_name(full_name):
    cleaned = (full_name or "").strip()
    if not cleaned:
        return "", ""

    parts = cleaned.split()
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first_name, last_name


def _parse_user_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_upload_path(file_path):
    if not file_path:
        return False

    absolute_upload_folder = os.path.abspath(UPLOAD_FOLDER)
    absolute_file_path = os.path.abspath(file_path)
    return absolute_file_path.startswith(absolute_upload_folder)


def _remove_file_if_exists(file_path):
    if not file_path or not _is_upload_path(file_path):
        return

    if os.path.exists(file_path):
        os.remove(file_path)


def _parse_receipt_date(receipt_date_str):
    try:
        return datetime.strptime(receipt_date_str, '%Y-%m-%d').date() if receipt_date_str else None
    except ValueError:
        return None


def _get_or_create_currency(currency_code):
    currency = db.session.get(Currency, currency_code)
    if currency:
        return currency

    currency = Currency(
        currency_code=currency_code,
        currency_name=f"{currency_code} Currency"
    )
    db.session.add(currency)
    return currency


def _get_or_create_category(category_name):
    category = Category.query.filter(Category.category_name.ilike(category_name)).first()
    if category:
        return category

    category = Category(
        category_name=category_name,
        description="Auto-generated by AI"
    )
    db.session.add(category)
    db.session.flush()
    return category


def _create_receipt_record(user, merchant_name, receipt_date_str, total_amount, currency_code, category_name, file_path):
    normalized_currency_code = normalize_currency_code(currency_code)
    amount_in_sgd = convert_amount_to_sgd(total_amount, normalized_currency_code)
    receipt_date = _parse_receipt_date(receipt_date_str)

    currency = _get_or_create_currency(normalized_currency_code)
    category = _get_or_create_category(category_name)

    receipt = Receipt(
        user_id=user.user_id,
        merchant_name=merchant_name,
        receipt_date=receipt_date,
        total_amount=total_amount,
        amount_in_sgd=amount_in_sgd,
        currency_code=currency.currency_code,
        category_id=category.category_id,
        receipt_image_path=file_path
    )
    db.session.add(receipt)
    return receipt, normalized_currency_code, amount_in_sgd


def _extract_response_payload(extracted_data):
    merchant_name = extracted_data.get('merchant_name') if isinstance(extracted_data, dict) else None
    receipt_date_str = extracted_data.get('receipt_date') if isinstance(extracted_data, dict) else None
    total_amount = extracted_data.get('total_amount') if isinstance(extracted_data, dict) else None
    raw_currency_code = (extracted_data.get('currency_code') or 'USD') if isinstance(extracted_data, dict) else 'USD'
    category_name = (extracted_data.get('category_name') or 'Uncategorized') if isinstance(extracted_data, dict) else 'Uncategorized'

    return {
        "merchant_name": merchant_name,
        "receipt_date": receipt_date_str,
        "total_amount": total_amount,
        "currency": normalize_currency_code(raw_currency_code),
        "category": category_name,
    }


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


@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not name or not email or not password:
        return _friendly_error("Please complete all required fields.", 400)

    if not _is_valid_email(email):
        return _friendly_error("Please enter a valid email address.", 400)

    if len(password) < 8:
        return _friendly_error("Password must be at least 8 characters long.", 400)

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return _friendly_error("An account with this email already exists.", 409)

    try:
        first_name, last_name = _split_name(name)
        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Registration successful. Please log in.",
            "user": {
                "user_id": new_user.user_id,
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
            },
        }), 201
    except Exception:
        db.session.rollback()
        return _friendly_error("We couldn’t create your account right now. Please try again shortly.", 500)


@api_bp.route('/dashboard', methods=['GET'])
def dashboard_summary():
    raw_user_id = request.args.get('user_id')
    user_id = _parse_user_id(raw_user_id)
    if user_id is None:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    user = db.session.get(User, user_id)
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    return jsonify(_build_dashboard_payload(user.user_id)), 200


@api_bp.route('/receipts', methods=['GET'])
def list_receipts():
    raw_user_id = request.args.get('user_id')
    user_id = _parse_user_id(raw_user_id)
    if user_id is None:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    user = db.session.get(User, user_id)
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    receipts = (
        Receipt.query.filter_by(user_id=user.user_id)
        .order_by(Receipt.created_at.desc())
        .all()
    )
    return jsonify([_serialize_receipt(receipt) for receipt in receipts]), 200


@api_bp.route('/receipts/preview', methods=['POST'])
def preview_receipt_upload():
    if 'file' not in request.files:
        return _friendly_error("No receipt file was provided. Please choose a file and try again.", 400)

    file = request.files['file']
    raw_user_id = request.form.get('user_id')
    user_id = _parse_user_id(raw_user_id)

    if file.filename == '':
        return _friendly_error("No receipt file was selected. Please choose a file and try again.", 400)

    if user_id is None:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    user = db.session.get(User, user_id)
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    if not (file and allowed_file(file.filename)):
        return _friendly_error("Please upload a JPG, PNG, or WebP receipt.", 400)

    filename = secure_filename(f"tmp_{int(datetime.utcnow().timestamp())}_{file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        extracted_data = extract_receipt_data(file_path)
        payload = _extract_response_payload(extracted_data)

        return jsonify({
            "status": "success",
            "message": "Receipt extracted successfully. Please verify the details before uploading.",
            "data": {
                **payload,
                "temp_file_path": file_path,
            }
        }), 200
    except Exception:
        _remove_file_if_exists(file_path)
        return _friendly_error("We couldn’t read the receipt. Please try a clearer image or upload again.", 500)


@api_bp.route('/receipts/confirm', methods=['POST'])
def confirm_receipt_upload():
    data = request.get_json(silent=True) or {}
    user_id = _parse_user_id(data.get('user_id'))

    if user_id is None:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    user = db.session.get(User, user_id)
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    temp_file_path = (data.get('temp_file_path') or '').strip()
    merchant_name = data.get('merchant_name')
    receipt_date_str = data.get('receipt_date')
    total_amount = data.get('total_amount')
    currency_code = data.get('currency') or 'USD'
    category_name = data.get('category') or 'Uncategorized'

    if not temp_file_path or not _is_upload_path(temp_file_path) or not os.path.exists(temp_file_path):
        return _friendly_error("Receipt preview is no longer available. Please upload again.", 400)

    try:
        numeric_total = float(total_amount)
    except (TypeError, ValueError):
        return _friendly_error("Please provide a valid receipt total amount.", 400)

    final_file_path = temp_file_path
    temp_file_name = os.path.basename(temp_file_path)
    if temp_file_name.startswith('tmp_'):
        final_file_name = temp_file_name.replace('tmp_', '', 1)
        candidate_path = os.path.join(UPLOAD_FOLDER, final_file_name)
        if not os.path.exists(candidate_path):
            os.replace(temp_file_path, candidate_path)
            final_file_path = candidate_path

    try:
        new_receipt, normalized_currency, amount_in_sgd = _create_receipt_record(
            user=user,
            merchant_name=merchant_name,
            receipt_date_str=receipt_date_str,
            total_amount=numeric_total,
            currency_code=currency_code,
            category_name=category_name,
            file_path=final_file_path,
        )
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Receipt processed and saved successfully.",
            "data": {
                "receipt_id": new_receipt.receipt_id,
                "merchant_name": merchant_name,
                "receipt_date": receipt_date_str,
                "total_amount": numeric_total,
                "currency": normalized_currency,
                "amount_in_sgd": amount_in_sgd,
                "category": category_name,
            }
        }), 201
    except Exception:
        db.session.rollback()
        return _friendly_error("We couldn’t save the receipt right now. Please try again shortly.", 500)


@api_bp.route('/receipts/cancel-preview', methods=['POST'])
def cancel_receipt_preview():
    data = request.get_json(silent=True) or {}
    temp_file_path = (data.get('temp_file_path') or '').strip()

    if temp_file_path:
        try:
            _remove_file_if_exists(temp_file_path)
        except OSError:
            return _friendly_error("We couldn’t cancel the receipt preview right now. Please try again.", 500)

    return jsonify({
        "status": "success",
        "message": "Receipt preview cancelled.",
    }), 200


@api_bp.route('/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    raw_user_id = request.args.get('user_id')
    user_id = _parse_user_id(raw_user_id)
    if user_id is None:
        return _friendly_error("Your session is missing. Please sign in again and try again.", 400)

    user = db.session.get(User, user_id)
    if not user:
        return _friendly_error("We couldn’t identify your account. Please sign in again and try again.", 404)

    receipt = Receipt.query.filter_by(receipt_id=receipt_id, user_id=user.user_id).first()
    if not receipt:
        return _friendly_error("Receipt not found.", 404)

    file_path = receipt.receipt_image_path
    category_id = receipt.category_id
    currency_code = receipt.currency_code

    try:
        db.session.delete(receipt)
        db.session.flush()

        if category_id and not Receipt.query.filter_by(category_id=category_id).first():
            category = db.session.get(Category, category_id)
            if category:
                db.session.delete(category)

        if currency_code and not Receipt.query.filter_by(currency_code=currency_code).first():
            currency = db.session.get(Currency, currency_code)
            if currency:
                db.session.delete(currency)

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _friendly_error("We couldn’t delete the receipt right now. Please try again shortly.", 500)

    try:
        _remove_file_if_exists(file_path)
    except OSError:
        return jsonify({
            "status": "success",
            "message": "Receipt deleted, but we couldn’t remove the local image file.",
        }), 200

    return jsonify({
        "status": "success",
        "message": "Receipt deleted successfully.",
    }), 200


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
    raw_user_id = request.form.get('user_id')
    user_id = _parse_user_id(raw_user_id)

    if file.filename == '':
        return _friendly_error("No receipt file was selected. Please choose a file and try again.", 400)
        
    if user_id is None:
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
            _remove_file_if_exists(file_path)
            return _friendly_error("We couldn’t read the receipt. Please try a clearer image or upload again.", 500)

        payload = _extract_response_payload(extracted_data)

        # 4. Database Operations
        try:
            new_receipt, normalized_currency, amount_in_sgd = _create_receipt_record(
                user=user,
                merchant_name=payload['merchant_name'],
                receipt_date_str=payload['receipt_date'],
                total_amount=payload['total_amount'],
                currency_code=payload['currency'],
                category_name=payload['category'],
                file_path=file_path,
            )

            db.session.commit()
            
            # 5. Return Success Response
            return jsonify({
                "status": "success",
                "message": "Receipt processed and saved successfully.",
                "data": {
                    "receipt_id": new_receipt.receipt_id,
                    "merchant_name": payload['merchant_name'],
                    "receipt_date": payload['receipt_date'],
                    "total_amount": payload['total_amount'],
                    "currency": normalized_currency,
                    "amount_in_sgd": amount_in_sgd,
                    "category": payload['category']
                }
            }), 201

        except Exception:
            db.session.rollback()
            return _friendly_error("We couldn’t save the receipt right now. Please try again shortly.", 500)

    return _friendly_error("Please upload a JPG, PNG, or WebP receipt.", 400)
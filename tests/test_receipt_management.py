import io
import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app import create_app, db
from app.models import Category, Currency, Receipt, User


class ReceiptManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch("app.routes.extract_receipt_data", return_value={
        "merchant_name": "Coffee House",
        "receipt_date": "2026-07-10",
        "total_amount": 12.5,
        "currency_code": "MYR",
        "category_name": "Food",
    })
    def test_preview_confirm_and_cancel_flow(self, _mock_extract):
        user = User.query.filter_by(email="demo@example.com").first()
        self.assertIsNotNone(user)

        preview_response = self.client.post(
            "/api/receipts/preview",
            data={
                "file": (io.BytesIO(b"fake-image-data"), "receipt.png"),
                "user_id": str(user.user_id),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(preview_response.status_code, 200)

        preview_payload = preview_response.get_json()["data"]
        temp_file_path = preview_payload["temp_file_path"]
        self.assertTrue(os.path.exists(temp_file_path))

        confirm_response = self.client.post(
            "/api/receipts/confirm",
            json={
                "user_id": user.user_id,
                "temp_file_path": temp_file_path,
                "merchant_name": "Coffee House Edited",
                "receipt_date": "2026-07-11",
                "total_amount": 20.0,
                "currency": "MYR",
                "category": "Food",
            },
        )
        self.assertEqual(confirm_response.status_code, 201)

        receipt = Receipt.query.filter_by(user_id=user.user_id).first()
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.merchant_name, "Coffee House Edited")
        self.assertEqual(receipt.currency_code, "MYR")

        second_preview_response = self.client.post(
            "/api/receipts/preview",
            data={
                "file": (io.BytesIO(b"fake-image-data-2"), "receipt2.png"),
                "user_id": str(user.user_id),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(second_preview_response.status_code, 200)
        second_temp_path = second_preview_response.get_json()["data"]["temp_file_path"]
        self.assertTrue(os.path.exists(second_temp_path))

        cancel_response = self.client.post(
            "/api/receipts/cancel-preview",
            json={"temp_file_path": second_temp_path},
        )
        self.assertEqual(cancel_response.status_code, 200)
        self.assertFalse(os.path.exists(second_temp_path))
        self.assertEqual(Receipt.query.filter_by(user_id=user.user_id).count(), 1)

    def test_delete_single_receipt_removes_file_only_for_target_record(self):
        user = User.query.filter_by(email="demo@example.com").first()
        self.assertIsNotNone(user)

        category = Category(category_name="Food", description="Test")
        currency = Currency(currency_code="SGD", currency_name="Singapore Dollar")
        db.session.add(category)
        db.session.add(currency)
        db.session.flush()

        uploads_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        first_path = os.path.join(uploads_dir, "delete-test-1.png")
        second_path = os.path.join(uploads_dir, "delete-test-2.png")
        with open(first_path, "wb") as file_handle:
            file_handle.write(b"one")
        with open(second_path, "wb") as file_handle:
            file_handle.write(b"two")

        first_receipt = Receipt(
            user_id=user.user_id,
            merchant_name="First",
            receipt_date=date.today(),
            total_amount=Decimal("10.00"),
            amount_in_sgd=Decimal("10.00"),
            currency_code="SGD",
            category_id=category.category_id,
            receipt_image_path=first_path,
        )
        second_receipt = Receipt(
            user_id=user.user_id,
            merchant_name="Second",
            receipt_date=date.today(),
            total_amount=Decimal("20.00"),
            amount_in_sgd=Decimal("20.00"),
            currency_code="SGD",
            category_id=category.category_id,
            receipt_image_path=second_path,
        )
        db.session.add(first_receipt)
        db.session.add(second_receipt)
        db.session.commit()

        response = self.client.delete(f"/api/receipts/{first_receipt.receipt_id}?user_id={user.user_id}")
        self.assertEqual(response.status_code, 200)

        self.assertIsNone(db.session.get(Receipt, first_receipt.receipt_id))
        self.assertIsNotNone(db.session.get(Receipt, second_receipt.receipt_id))
        self.assertFalse(os.path.exists(first_path))
        self.assertTrue(os.path.exists(second_path))

        if os.path.exists(second_path):
            os.remove(second_path)


if __name__ == "__main__":
    unittest.main()

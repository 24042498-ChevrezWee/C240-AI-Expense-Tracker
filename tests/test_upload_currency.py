import io
import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import User


class UploadCurrencyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch("app.routes.convert_amount_to_sgd", return_value=12.5)
    @patch("app.routes.extract_receipt_data", return_value={
        "merchant_name": "Coffee House",
        "receipt_date": "2024-07-01",
        "total_amount": 50.0,
        "currency_code": "MYR",
        "category_name": "Food",
    })
    def test_upload_returns_converted_sgd_amount(self, mock_extract, mock_convert):
        user = User.query.filter_by(email="demo@example.com").first()
        self.assertIsNotNone(user)

        response = self.client.post(
            "/api/upload",
            data={
                "file": (io.BytesIO(b"fake-image-data"), "receipt.png"),
                "user_id": user.user_id,
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["data"]["amount_in_sgd"], 12.5)
        mock_convert.assert_called_once_with(50.0, "MYR")


if __name__ == "__main__":
    unittest.main()

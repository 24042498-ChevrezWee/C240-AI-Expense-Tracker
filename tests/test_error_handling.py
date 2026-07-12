import unittest
from io import BytesIO
from unittest.mock import patch

from app import create_app, db


class ErrorHandlingTestCase(unittest.TestCase):
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

    def test_upload_with_invalid_file_type_returns_generic_message(self):
        response = self.client.post(
            "/api/upload",
            data={
                "file": (BytesIO(b"not-a-receipt"), "receipt.txt"),
                "user_id": "1",
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Please upload a JPG, PNG, or WebP receipt.")

    def test_upload_with_ai_processing_failure_returns_generic_message(self):
        with patch("app.routes.extract_receipt_data", side_effect=Exception("Gemini exploded")):
            response = self.client.post(
                "/api/upload",
                data={
                    "file": (BytesIO(b"fake-image"), "receipt.png"),
                    "user_id": "1",
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data["error"], "We couldn’t read the receipt. Please try a clearer image or upload again.")


if __name__ == "__main__":
    unittest.main()

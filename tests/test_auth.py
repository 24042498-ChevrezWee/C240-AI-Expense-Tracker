import unittest

from app import create_app
from app import db


class AuthRoutesTestCase(unittest.TestCase):
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

    def test_login_with_seeded_user(self):
        response = self.client.post(
            "/api/login",
            json={"email": "demo@example.com", "password": "password123"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["status"] == "success")
        self.assertEqual(data["user"]["email"], "demo@example.com")

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            "/api/login",
            json={"email": "demo@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid email or password")


if __name__ == "__main__":
    unittest.main()

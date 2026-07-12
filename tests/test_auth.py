import unittest
from werkzeug.security import check_password_hash

from app import create_app
from app import db
from app.models import User


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

    def test_register_success_creates_hashed_user_and_can_login(self):
        register_response = self.client.post(
            "/api/register",
            json={
                "name": "Alice Tan",
                "email": "alice@example.com",
                "password": "strongpass123",
            },
        )

        self.assertEqual(register_response.status_code, 201)
        register_payload = register_response.get_json()
        self.assertEqual(register_payload["status"], "success")

        user = User.query.filter_by(email="alice@example.com").first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, "strongpass123")
        self.assertTrue(check_password_hash(user.password_hash, "strongpass123"))

        login_response = self.client.post(
            "/api/login",
            json={"email": "alice@example.com", "password": "strongpass123"},
        )
        self.assertEqual(login_response.status_code, 200)

    def test_register_rejects_duplicate_email(self):
        first_response = self.client.post(
            "/api/register",
            json={
                "name": "Bob Lee",
                "email": "bob@example.com",
                "password": "strongpass123",
            },
        )
        self.assertEqual(first_response.status_code, 201)

        duplicate_response = self.client.post(
            "/api/register",
            json={
                "name": "Bob Lee",
                "email": "bob@example.com",
                "password": "strongpass123",
            },
        )

        self.assertEqual(duplicate_response.status_code, 409)
        payload = duplicate_response.get_json()
        self.assertEqual(payload["error"], "An account with this email already exists.")

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            "/api/register",
            json={
                "name": "Chris Wong",
                "email": "chris@example.com",
                "password": "short",
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"], "Password must be at least 8 characters long.")


if __name__ == "__main__":
    unittest.main()

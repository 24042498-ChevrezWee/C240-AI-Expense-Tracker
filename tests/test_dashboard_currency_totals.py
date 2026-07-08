import unittest
from datetime import date
from decimal import Decimal

from app import create_app, db
from app.models import Category, Currency, Receipt, User


class DashboardCurrencyTotalsTestCase(unittest.TestCase):
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

    def test_dashboard_uses_sgd_converted_totals_with_mixed_currencies(self):
        user = User.query.filter_by(email="demo@example.com").first()
        self.assertIsNotNone(user)

        category = Category(category_name="Food", description="Test category")
        db.session.add(category)
        db.session.add(Currency(currency_code="SGD", currency_name="Singapore Dollar"))
        db.session.add(Currency(currency_code="MYR", currency_name="Malaysian Ringgit"))
        db.session.add(Currency(currency_code="USD", currency_name="US Dollar"))
        db.session.flush()

        db.session.add(
            Receipt(
                user_id=user.user_id,
                merchant_name="Shop SG",
                receipt_date=date.today(),
                total_amount=Decimal("100.00"),
                amount_in_sgd=Decimal("100.00"),
                currency_code="SGD",
                category_id=category.category_id,
                receipt_image_path="uploads/sgd.png",
            )
        )
        db.session.add(
            Receipt(
                user_id=user.user_id,
                merchant_name="Shop MY",
                receipt_date=date.today(),
                total_amount=Decimal("500.00"),
                amount_in_sgd=Decimal("142.86"),
                currency_code="MYR",
                category_id=category.category_id,
                receipt_image_path="uploads/myr.png",
            )
        )
        db.session.add(
            Receipt(
                user_id=user.user_id,
                merchant_name="Shop US",
                receipt_date=date.today(),
                total_amount=Decimal("20.00"),
                amount_in_sgd=Decimal("27.03"),
                currency_code="USD",
                category_id=category.category_id,
                receipt_image_path="uploads/usd.png",
            )
        )
        db.session.commit()

        response = self.client.get(f"/api/dashboard?user_id={user.user_id}")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertAlmostEqual(payload["totalExpenses"], 269.89, places=2)
        self.assertAlmostEqual(payload["monthlySpending"], 269.89, places=2)
        self.assertEqual(payload["largestExpense"], "SGD 142.86")
        self.assertAlmostEqual(payload["averageExpense"], 89.96, places=2)


if __name__ == "__main__":
    unittest.main()

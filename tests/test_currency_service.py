import unittest
from unittest.mock import patch

from app.currency_service import _EXCHANGE_RATE_CACHE, convert_amount_to_sgd, normalize_currency_code


class CurrencyServiceTestCase(unittest.TestCase):
    def setUp(self):
        _EXCHANGE_RATE_CACHE.clear()

    def test_normalizes_common_symbol_variants(self):
        self.assertEqual(normalize_currency_code("RM"), "MYR")
        self.assertEqual(normalize_currency_code("S$"), "SGD")
        self.assertEqual(normalize_currency_code("sgd"), "SGD")
        self.assertEqual(normalize_currency_code("myr"), "MYR")
        self.assertEqual(normalize_currency_code("USD"), "USD")

    @patch("app.currency_service.requests.get")
    def test_converts_to_sgd_with_live_rate_response(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "rates": {
                "SGD": 1.0,
                "MYR": 3.5,
                "USD": 0.74,
            }
        }

        myr_in_sgd = convert_amount_to_sgd(500, "MYR")
        usd_in_sgd = convert_amount_to_sgd(20, "USD")

        self.assertIsNotNone(myr_in_sgd)
        self.assertIsNotNone(usd_in_sgd)
        self.assertAlmostEqual(myr_in_sgd, 500 / 3.5, places=4)
        self.assertAlmostEqual(usd_in_sgd, 20 / 0.74, places=4)

    @patch("app.currency_service.requests.get", side_effect=Exception("service unavailable"))
    def test_handles_rate_api_failure_gracefully(self, _mock_get):
        self.assertIsNone(convert_amount_to_sgd(500, "MYR"))


if __name__ == "__main__":
    unittest.main()

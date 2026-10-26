import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline import validate


class PipelineTests(unittest.TestCase):
    def test_duplicate_and_invalid_email_are_rejected(self):
        customers = [
            {"customer_id": "C1", "full_name": "Ada", "email": "ada@example.com", "country": "DK"},
            {"customer_id": "C1", "full_name": "Ada", "email": "bad", "country": "DK"},
        ]
        data, report = validate(customers, [{"sku": "P1", "description": "Brick", "unit_price": 1, "active": True}], [])
        self.assertEqual(len(data["customers"]), 1)
        self.assertEqual(report["rejected_counts"]["customers"], 1)
        self.assertEqual(report["errors"]["customers"]["duplicate_customer_id"], 1)
        self.assertEqual(report["errors"]["customers"]["invalid_email"], 1)

    def test_unknown_customer_is_rejected(self):
        customers = [{"customer_id": "C1", "full_name": "Ada", "email": "ada@example.com", "country": "DK"}]
        orders = [{"order_id": "O1", "customer_id": "C9", "sku": "P1", "ordered_on": "2026-01-01", "quantity": 1}]
        data, report = validate(customers, [{"sku": "P1", "description": "Brick", "unit_price": 1, "active": True}], orders)
        self.assertEqual(data["orders"], [])
        self.assertEqual(report["errors"]["orders"]["unknown_customer"], 1)


if __name__ == "__main__":
    unittest.main()

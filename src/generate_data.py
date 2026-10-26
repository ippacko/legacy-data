"""Generate deterministic, intentionally messy legacy source data."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)

    customers = [
        {"legacy_customer_id": "C001", "full_name": "Ada Lovelace", "email_address": "ada@example.com", "country": "DK"},
        {"legacy_customer_id": "C002", "full_name": "Grace Hopper", "email_address": "grace@example.com", "country": "US"},
        {"legacy_customer_id": "C002", "full_name": "Grace Hopper", "email_address": "grace@example.com", "country": "US"},
        {"legacy_customer_id": "C003", "full_name": "Katherine Johnson", "email_address": "katherine@example.com", "country": ""},
        {"legacy_customer_id": "C004", "full_name": "Alan Turing", "email_address": "not-an-email", "country": "GB"},
    ]
    with (RAW / "customers_legacy.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=customers[0].keys())
        writer.writeheader()
        writer.writerows(customers)

    products = [
        {"sku": "P-100", "description": "Classic Brick", "unit_price": 12.5, "active": True},
        {"sku": "P-200", "description": "Creative Wheel Set", "unit_price": 18.0, "active": True},
        {"sku": "P-300", "description": "Display Base", "unit_price": 9.5, "active": True},
    ]
    (RAW / "products_legacy.json").write_text(json.dumps(products, indent=2), encoding="utf-8")

    orders = []
    for index in range(1, 11):
        customer_id = f"C{rng.randint(1, 3):03d}"
        sku = rng.choice(["P-100", "P-200", "P-300"])
        quantity = rng.randint(1, 5)
        orders.append(
            {
                "order_no": f"O-{index:04d}",
                "customer_ref": customer_id,
                "sku": sku,
                "ordered_on": f"2026-01-{index:02d}",
                "quantity": quantity,
            }
        )
    orders.append({"order_no": "O-9999", "customer_ref": "C999", "sku": "P-100", "ordered_on": "2026-01-20", "quantity": 2})
    with (RAW / "orders_legacy.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=orders[0].keys())
        writer.writeheader()
        writer.writerows(orders)


if __name__ == "__main__":
    main()

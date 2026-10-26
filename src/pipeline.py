"""Normalize, validate, and load legacy data into a small warehouse."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "warehouse.db"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def read_csv(name: str) -> list[dict[str, str]]:
    with (RAW / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def normalize_customers(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "customer_id": row["legacy_customer_id"].strip().upper(),
            "full_name": " ".join(row["full_name"].split()),
            "email": row["email_address"].strip().lower(),
            "country": row["country"].strip().upper() or None,
        }
        for row in rows
    ]


def normalize_orders(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "order_id": row["order_no"].strip().upper(),
            "customer_id": row["customer_ref"].strip().upper(),
            "sku": row["sku"].strip().upper(),
            "ordered_on": row["ordered_on"].strip(),
            "quantity": int(row["quantity"]),
        }
        for row in rows
    ]


def validate(customers: list[dict[str, Any]], products: list[dict[str, Any]], orders: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    customer_ids = {row["customer_id"] for row in customers}
    product_skus = {row["sku"] for row in products}
    seen_customers: set[str] = set()
    valid_customers: list[dict[str, Any]] = []
    invalid_customers: list[dict[str, Any]] = []
    customer_errors: Counter[str] = Counter()
    for row in customers:
        errors = []
        if row["customer_id"] in seen_customers:
            errors.append("duplicate_customer_id")
        if not row["customer_id"] or not row["full_name"]:
            errors.append("missing_required_field")
        if not EMAIL_RE.match(row["email"]):
            errors.append("invalid_email")
        seen_customers.add(row["customer_id"])
        (valid_customers if not errors else invalid_customers).append(row | {"errors": errors} if errors else row)
        customer_errors.update(errors)

    valid_orders: list[dict[str, Any]] = []
    invalid_orders: list[dict[str, Any]] = []
    order_errors: Counter[str] = Counter()
    for row in orders:
        errors = []
        if row["customer_id"] not in customer_ids:
            errors.append("unknown_customer")
        if row["sku"] not in product_skus:
            errors.append("unknown_product")
        if row["quantity"] <= 0:
            errors.append("non_positive_quantity")
        (valid_orders if not errors else invalid_orders).append(row | {"errors": errors} if errors else row)
        order_errors.update(errors)

    result = {"customers": valid_customers, "products": products, "orders": valid_orders}
    report = {
        "source_counts": {"customers": len(customers), "products": len(products), "orders": len(orders)},
        "accepted_counts": {key: len(value) for key, value in result.items()},
        "rejected_counts": {"customers": len(invalid_customers), "orders": len(invalid_orders)},
        "errors": {"customers": dict(customer_errors), "orders": dict(order_errors)},
        "rejected_records": {"customers": invalid_customers, "orders": invalid_orders},
    }
    return result, report


def load_warehouse(data: dict[str, list[dict[str, Any]]]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS customers;
            DROP TABLE IF EXISTS products;
            CREATE TABLE customers (customer_id TEXT PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL, country TEXT);
            CREATE TABLE products (sku TEXT PRIMARY KEY, description TEXT NOT NULL, unit_price REAL NOT NULL, active INTEGER NOT NULL);
            CREATE TABLE orders (order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(customer_id), sku TEXT NOT NULL REFERENCES products(sku), ordered_on TEXT NOT NULL, quantity INTEGER NOT NULL);
            """
        )
        connection.executemany("INSERT INTO customers VALUES (:customer_id, :full_name, :email, :country)", data["customers"])
        connection.executemany("INSERT INTO products VALUES (:sku, :description, :unit_price, :active)", data["products"])
        connection.executemany("INSERT INTO orders VALUES (:order_id, :customer_id, :sku, :ordered_on, :quantity)", data["orders"])


def main() -> dict[str, Any]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    customers = normalize_customers(read_csv("customers_legacy.csv"))
    products = json.loads((RAW / "products_legacy.json").read_text(encoding="utf-8"))
    orders = normalize_orders(read_csv("orders_legacy.csv"))
    data, report = validate(customers, products, orders)
    load_warehouse(data)
    (PROCESSED / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for name, rows in data.items():
        with (PROCESSED / f"{name}.json").open("w", encoding="utf-8") as handle:
            json.dump(rows, handle, indent=2)
    return report


if __name__ == "__main__":
    summary = main()
    print(json.dumps({key: summary[key] for key in ("source_counts", "accepted_counts", "rejected_counts")}, indent=2))

# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES.
#
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0

"""Duplicate-column tests for the SQLite connector (issue #408)."""

import sqlite3
import tempfile
from pathlib import Path

from auto_ontology.connectors.sqlite import SQLiteDatabase


def _seed_shop(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE customers (id INT, name TEXT);
        CREATE TABLE orders (id INT, customer_id INT, name TEXT);
        INSERT INTO customers VALUES (1, 'Ada');
        INSERT INTO orders VALUES (100, 1, 'first order');
        """
    )
    conn.close()


def test_execute_preserves_duplicate_column_values() -> None:
    """SELECT c.id, o.id, ... must return both ids, not the first twice."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "shop.db"
        _seed_shop(path)
        database = SQLiteDatabase(f"sqlite:///{path}")
        try:
            result = database.execute(
                "SELECT c.id, o.id, c.name, o.name "
                "FROM customers c JOIN orders o ON o.customer_id = c.id"
            )
        finally:
            database.close()
        assert list(result.columns) == ["id", "id", "name", "name"]
        assert result.values.tolist() == [[1, 100, "Ada", "first order"]]


def test_execute_empty_result_keeps_columns() -> None:
    """A zero-row result must still report its column names."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "shop.db"
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE empty_t (id INT, v TEXT)")
        conn.close()
        database = SQLiteDatabase(f"sqlite:///{path}")
        try:
            result = database.execute("SELECT id, v FROM empty_t")
        finally:
            database.close()
        assert list(result.columns) == ["id", "v"]
        assert result.empty

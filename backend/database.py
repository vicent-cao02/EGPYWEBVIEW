from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "negocio.db"


class Database:
    """
    Capa de acceso a SQLite.
    Todas las consultas del sistema deben pasar por aquí.
    """

    def __init__(self):
        self.db_path = DB_PATH

    def connect(self):

        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            detect_types=0
        )

        conn.row_factory = sqlite3.Row
        conn.text_factory = str

        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        return conn

    @contextmanager
    def transaction(self):

        conn = self.connect()

        try:

            yield conn

            conn.commit()

        except Exception:

            conn.rollback()

            raise

        finally:

            conn.close()

    def fetchall(
        self,
        query: str,
        params: Iterable = ()
    ) -> List[Dict]:

        with self.transaction() as conn:

            cur = conn.execute(query, params)

            return [dict(r) for r in cur.fetchall()]

    def fetchone(
        self,
        query: str,
        params: Iterable = ()
    ) -> Optional[Dict]:

        with self.transaction() as conn:

            cur = conn.execute(query, params)

            row = cur.fetchone()

            if row is None:
                return None

            return dict(row)

    def execute(
        self,
        query: str,
        params: Iterable = ()
    ) -> int:

        with self.transaction() as conn:

            cur = conn.execute(query, params)

            return cur.lastrowid

    def executemany(
        self,
        query: str,
        values: Iterable
    ):

        with self.transaction() as conn:

            conn.executemany(query, values)


db = Database()


def get_connection():
    return db.connect()
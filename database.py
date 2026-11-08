"""
SetuSentry Database Management Module
Handles SQLite schema creation, connection pooling, and CRUD operations
for bridges and inspection records.
Ensures connections are properly closed to avoid file-locking on Windows.
"""

from __future__ import annotations
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

DEFAULT_DB_FILENAME = "setusentry.db"


def get_default_db_path() -> str:
    """Return the absolute path to the default SQLite database file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DEFAULT_DB_FILENAME)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a SQLite database connection with row factory enabled."""
    target_path = db_path or get_default_db_path()
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables with the required schema."""
    target_path = db_path or get_default_db_path()
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    conn = get_connection(target_path)
    try:
        with conn:
            cursor = conn.cursor()

            # Bridges table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bridges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bridge_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    state TEXT NOT NULL,
                    bridge_type TEXT NOT NULL,
                    construction_year INTEGER,
                    span_length REAL,
                    design_load REAL,
                    last_inspection_date TEXT,
                    risk_flood_zone INTEGER DEFAULT 0,
                    risk_high_traffic INTEGER DEFAULT 0,
                    risk_age_over30 INTEGER DEFAULT 0,
                    risk_previous_scour INTEGER DEFAULT 0,
                    risk_previous_cracks INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Inspections table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bridge_id TEXT NOT NULL,
                    inspection_date TEXT NOT NULL,
                    inspector_name TEXT NOT NULL,
                    inspection_type TEXT NOT NULL,
                    observations TEXT,
                    severity_rating INTEGER,
                    action_status TEXT DEFAULT 'Pending',
                    ai_crack_detected INTEGER,
                    ai_confidence REAL,
                    ai_severity TEXT,
                    image_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bridge_id) REFERENCES bridges(bridge_id) ON DELETE CASCADE
                )
                """
            )

            # Create indexes for fast filtering
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bridges_id ON bridges(bridge_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inspections_bridge ON inspections(bridge_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inspections_date ON inspections(inspection_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inspections_status ON inspections(action_status);")
    finally:
        conn.close()


# ---------------------------------------------------------
# BRIDGE CRUD OPERATIONS
# ---------------------------------------------------------

def add_bridge(bridge_dict: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Insert a new bridge record into the database."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO bridges (
                    bridge_id, name, location, state, bridge_type,
                    construction_year, span_length, design_load,
                    last_inspection_date, risk_flood_zone, risk_high_traffic,
                    risk_age_over30, risk_previous_scour, risk_previous_cracks,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bridge_dict.get("bridge_id"),
                    bridge_dict.get("name"),
                    bridge_dict.get("location"),
                    bridge_dict.get("state"),
                    bridge_dict.get("bridge_type"),
                    bridge_dict.get("construction_year"),
                    bridge_dict.get("span_length"),
                    bridge_dict.get("design_load"),
                    bridge_dict.get("last_inspection_date"),
                    int(bool(bridge_dict.get("risk_flood_zone", 0))),
                    int(bool(bridge_dict.get("risk_high_traffic", 0))),
                    int(bool(bridge_dict.get("risk_age_over30", 0))),
                    int(bool(bridge_dict.get("risk_previous_scour", 0))),
                    int(bool(bridge_dict.get("risk_previous_cracks", 0))),
                    bridge_dict.get("notes", ""),
                ),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def update_bridge(bridge_id: str, update_dict: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Update fields of an existing bridge."""
    target_path = db_path or get_default_db_path()
    fields = []
    values = []
    allowed_fields = {
        "name", "location", "state", "bridge_type", "construction_year",
        "span_length", "design_load", "last_inspection_date",
        "risk_flood_zone", "risk_high_traffic", "risk_age_over30",
        "risk_previous_scour", "risk_previous_cracks", "notes"
    }

    for key, val in update_dict.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            if key.startswith("risk_"):
                values.append(int(bool(val)))
            else:
                values.append(val)

    if not fields:
        return False

    values.append(bridge_id)
    conn = get_connection(target_path)
    try:
        with conn:
            cursor = conn.cursor()
            query = f"UPDATE bridges SET {', '.join(fields)} WHERE bridge_id = ?"
            cursor.execute(query, tuple(values))
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_bridge(bridge_id: str, db_path: Optional[str] = None) -> bool:
    """Delete a bridge and cascade delete inspections."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inspections WHERE bridge_id = ?", (bridge_id,))
            cursor.execute("DELETE FROM bridges WHERE bridge_id = ?", (bridge_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_bridge(bridge_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single bridge record by its unique bridge_id."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bridges WHERE bridge_id = ?", (bridge_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_bridges(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all bridges sorted by bridge_id."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bridges ORDER BY bridge_id ASC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_bridges_df(db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve all bridges as a pandas DataFrame."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        return pd.read_sql_query("SELECT * FROM bridges ORDER BY bridge_id ASC", conn)
    finally:
        conn.close()


def update_bridge_last_inspection(bridge_id: str, inspection_date: str, db_path: Optional[str] = None) -> None:
    """Update last_inspection_date of a bridge if new date is more recent."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_inspection_date FROM bridges WHERE bridge_id = ?", (bridge_id,))
            row = cursor.fetchone()
            if row:
                current_date = row["last_inspection_date"]
                if not current_date or inspection_date > current_date:
                    cursor.execute(
                        "UPDATE bridges SET last_inspection_date = ? WHERE bridge_id = ?",
                        (inspection_date, bridge_id),
                    )
    finally:
        conn.close()


# ---------------------------------------------------------
# INSPECTION CRUD OPERATIONS
# ---------------------------------------------------------

def add_inspection(inspection_dict: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Insert a new inspection record and update bridge last_inspection_date."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO inspections (
                    bridge_id, inspection_date, inspector_name,
                    inspection_type, observations, severity_rating,
                    action_status, ai_crack_detected, ai_confidence,
                    ai_severity, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_dict.get("bridge_id"),
                    inspection_dict.get("inspection_date"),
                    inspection_dict.get("inspector_name"),
                    inspection_dict.get("inspection_type", "Visual"),
                    inspection_dict.get("observations", ""),
                    int(inspection_dict.get("severity_rating", 1)),
                    inspection_dict.get("action_status", "Pending"),
                    1 if inspection_dict.get("ai_crack_detected") else 0,
                    float(inspection_dict.get("ai_confidence", 0.0)),
                    inspection_dict.get("ai_severity", "None"),
                    inspection_dict.get("image_path", ""),
                ),
            )
            last_id = cursor.lastrowid
    finally:
        conn.close()

    # Update last_inspection_date on the bridge
    if inspection_dict.get("bridge_id") and inspection_dict.get("inspection_date"):
        update_bridge_last_inspection(
            inspection_dict["bridge_id"],
            inspection_dict["inspection_date"],
            db_path=target_path
        )

    return last_id


def get_inspections_for_bridge(bridge_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all inspections for a specific bridge ordered by date descending."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM inspections WHERE bridge_id = ? ORDER BY inspection_date DESC, id DESC",
            (bridge_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_inspections(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all inspection records across all bridges."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT i.*, b.name as bridge_name, b.state, b.location
            FROM inspections i
            JOIN bridges b ON i.bridge_id = b.bridge_id
            ORDER BY i.inspection_date DESC, i.id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_inspections_df(db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve all inspections as a pandas DataFrame."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        return pd.read_sql_query(
            """
            SELECT i.*, b.name as bridge_name, b.state, b.location
            FROM inspections i
            JOIN bridges b ON i.bridge_id = b.bridge_id
            ORDER BY i.inspection_date DESC, i.id DESC
            """,
            conn,
        )
    finally:
        conn.close()


def get_unresolved_inspections(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve inspections with Pending or Escalated action status."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT i.*, b.name as bridge_name, b.location, b.state
            FROM inspections i
            JOIN bridges b ON i.bridge_id = b.bridge_id
            WHERE i.action_status IN ('Pending', 'Escalated')
            ORDER BY
                CASE i.action_status WHEN 'Escalated' THEN 1 ELSE 2 END,
                i.severity_rating DESC,
                i.inspection_date DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_inspection_status(inspection_id: int, new_status: str, db_path: Optional[str] = None) -> bool:
    """Update the action_status of an inspection record."""
    target_path = db_path or get_default_db_path()
    conn = get_connection(target_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE inspections SET action_status = ? WHERE id = ?",
                (new_status, inspection_id),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_overdue_bridges(days_threshold: int = 365, reference_date: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve bridges whose last inspection is overdue (> days_threshold)."""
    target_path = db_path or get_default_db_path()
    ref_dt = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()

    bridges = get_all_bridges(target_path)
    overdue = []

    for b in bridges:
        last_date_str = b.get("last_inspection_date")
        if not last_date_str:
            b_copy = dict(b)
            b_copy["days_overdue"] = 9999
            b_copy["status_note"] = "Never inspected"
            overdue.append(b_copy)
            continue

        try:
            last_dt = datetime.strptime(last_date_str, "%Y-%m-%d")
            diff_days = (ref_dt - last_dt).days
            if diff_days > days_threshold:
                b_copy = dict(b)
                b_copy["days_overdue"] = diff_days
                b_copy["status_note"] = f"{diff_days} days since last inspection"
                overdue.append(b_copy)
        except ValueError:
            b_copy = dict(b)
            b_copy["days_overdue"] = 9999
            b_copy["status_note"] = "Invalid date format"
            overdue.append(b_copy)

    # Sort descending by days overdue
    overdue.sort(key=lambda x: x["days_overdue"], reverse=True)
    return overdue

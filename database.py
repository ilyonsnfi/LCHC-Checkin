import sqlite3
from datetime import datetime
from typing import List, Optional
from models import User, Checkin, CheckinRecord

DATABASE = "checkin.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            table_number INTEGER NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES users (employee_id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_user_by_employee_id(employee_id: str) -> Optional[User]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE employee_id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return User(
            id=row["id"],
            employee_id=row["employee_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            table_number=row["table_number"]
        )
    return None

def create_checkin(employee_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO checkins (employee_id) VALUES (?)", (employee_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False

def get_checkin_history() -> List[CheckinRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.first_name, u.last_name, u.employee_id, u.table_number, c.checkin_time
        FROM checkins c
        JOIN users u ON c.employee_id = u.employee_id
        ORDER BY c.checkin_time DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        CheckinRecord(
            first_name=row["first_name"],
            last_name=row["last_name"],
            employee_id=row["employee_id"],
            table_number=row["table_number"],
            checkin_time=row["checkin_time"]
        )
        for row in rows
    ]

def create_user(user: User) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO users (first_name, last_name, employee_id, table_number) VALUES (?, ?, ?, ?)",
            (user.first_name, user.last_name, user.employee_id, user.table_number)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False

def create_users_batch(users: List[User]) -> tuple[int, List[str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    imported = 0
    errors = []
    
    for i, user in enumerate(users):
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO users (first_name, last_name, employee_id, table_number) VALUES (?, ?, ?, ?)",
                (user.first_name, user.last_name, user.employee_id, user.table_number)
            )
            imported += 1
        except sqlite3.Error as e:
            errors.append(f"User {i+1}: {str(e)}")
    
    conn.commit()
    conn.close()
    return imported, errors

def get_all_users() -> List[User]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY first_name, last_name")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        User(
            id=row["id"],
            employee_id=row["employee_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            table_number=row["table_number"]
        )
        for row in rows
    ]

def delete_all_users() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        # Delete all users
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        return count
    except sqlite3.Error:
        conn.close()
        return 0
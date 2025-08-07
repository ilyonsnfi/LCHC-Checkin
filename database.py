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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Initialize default settings if they don't exist
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("welcome_banner", "RFID Checkin Station"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("secondary_banner", "Scan your badge to check in"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("background_color", "#f5f5f5"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("highlight_color", "#007bff"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("background_image", ""))
    
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

def get_checkin_history(search: str = "") -> List[CheckinRecord]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search.strip():
        search_pattern = f"%{search}%"
        cursor.execute("""
            SELECT u.first_name, u.last_name, u.employee_id, u.table_number, c.checkin_time
            FROM checkins c
            JOIN users u ON c.employee_id = u.employee_id
            WHERE u.first_name LIKE ? COLLATE NOCASE
            OR u.last_name LIKE ? COLLATE NOCASE
            OR u.employee_id LIKE ? COLLATE NOCASE
            OR CAST(u.table_number AS TEXT) LIKE ?
            OR c.checkin_time LIKE ?
            ORDER BY c.checkin_time DESC
        """, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
    else:
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

def create_single_user(user: User) -> tuple[bool, str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if employee_id already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE employee_id = ?", (user.employee_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, "Employee ID already exists"
        
        cursor.execute(
            "INSERT INTO users (first_name, last_name, employee_id, table_number) VALUES (?, ?, ?, ?)",
            (user.first_name, user.last_name, user.employee_id, user.table_number)
        )
        conn.commit()
        conn.close()
        return True, "User created successfully"
    except sqlite3.Error as e:
        conn.close()
        return False, str(e)

def search_users(query: str) -> List[User]:
    if not query.strip():
        return get_all_users()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search across all fields
    search_pattern = f"%{query}%"
    cursor.execute("""
        SELECT * FROM users 
        WHERE first_name LIKE ? COLLATE NOCASE
        OR last_name LIKE ? COLLATE NOCASE
        OR employee_id LIKE ? COLLATE NOCASE
        OR CAST(table_number AS TEXT) LIKE ?
        ORDER BY first_name, last_name
    """, (search_pattern, search_pattern, search_pattern, search_pattern))
    
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

def get_tables_with_users(search: str = "") -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search.strip():
        search_pattern = f"%{search}%"
        cursor.execute("""
            SELECT table_number, 
                   GROUP_CONCAT(first_name || ' ' || last_name, ', ') as users,
                   COUNT(*) as user_count
            FROM users 
            WHERE first_name LIKE ? COLLATE NOCASE
            OR last_name LIKE ? COLLATE NOCASE
            OR employee_id LIKE ? COLLATE NOCASE
            OR CAST(table_number AS TEXT) LIKE ?
            GROUP BY table_number 
            ORDER BY table_number
        """, (search_pattern, search_pattern, search_pattern, search_pattern))
    else:
        cursor.execute("""
            SELECT table_number, 
                   GROUP_CONCAT(first_name || ' ' || last_name, ', ') as users,
                   COUNT(*) as user_count
            FROM users 
            GROUP BY table_number 
            ORDER BY table_number
        """)
    
    tables = cursor.fetchall()
    conn.close()
    
    return [
        {
            "table_number": table["table_number"],
            "users": table["users"].split(', ') if table["users"] else [],
            "user_count": table["user_count"]
        }
        for table in tables
    ]

def get_export_data() -> dict:
    """Get comprehensive data for export including users with and without checkins"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get users with checkins
    cursor.execute("""
        SELECT u.first_name, u.last_name, u.employee_id, u.table_number, c.checkin_time
        FROM checkins c
        JOIN users u ON c.employee_id = u.employee_id
        ORDER BY c.checkin_time DESC
    """)
    users_with_checkins = cursor.fetchall()
    
    # Get users without checkins
    cursor.execute("""
        SELECT u.first_name, u.last_name, u.employee_id, u.table_number
        FROM users u
        LEFT JOIN checkins c ON u.employee_id = c.employee_id
        WHERE c.employee_id IS NULL
        ORDER BY u.first_name, u.last_name
    """)
    users_without_checkins = cursor.fetchall()
    
    conn.close()
    
    return {
        'with_checkins': [
            CheckinRecord(
                first_name=row["first_name"],
                last_name=row["last_name"],
                employee_id=row["employee_id"],
                table_number=row["table_number"],
                checkin_time=row["checkin_time"]
            )
            for row in users_with_checkins
        ],
        'without_checkins': [
            User(
                first_name=row["first_name"],
                last_name=row["last_name"],
                employee_id=row["employee_id"],
                table_number=row["table_number"]
            )
            for row in users_without_checkins
        ]
    }

def get_settings() -> dict:
    """Get all settings as a dictionary"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    
    return {row["key"]: row["value"] for row in rows}

def update_settings(settings: dict) -> bool:
    """Update multiple settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for key, value in settings.items():
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False
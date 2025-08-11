import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from models import User, Checkin, CheckinRecord
import secrets
import hashlib
import bcrypt

import os
DATABASE = os.getenv("DATABASE_PATH", "checkin.db")

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
    
    # Authentication tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (username) REFERENCES auth_users (username)
        )
    """)
    
    # Initialize default settings if they don't exist
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("welcome_banner", "RFID Checkin Station"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("secondary_banner", "Scan your badge to check in"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("text_color", "#333333"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("foreground_color", "#ffffff"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("background_color", "#f5f5f5"))
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
    cursor.execute("""
        SELECT u.*, 
               MAX(c.checkin_time) as last_checkin,
               CASE WHEN MAX(c.checkin_time) IS NOT NULL THEN 1 ELSE 0 END as is_checked_in
        FROM users u
        LEFT JOIN checkins c ON u.employee_id = c.employee_id
        GROUP BY u.id, u.employee_id, u.first_name, u.last_name, u.table_number
        ORDER BY u.first_name, u.last_name
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        User(
            id=row["id"],
            employee_id=row["employee_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            table_number=row["table_number"],
            last_checkin=row["last_checkin"],
            is_checked_in=bool(row["is_checked_in"])
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
        SELECT u.*, 
               MAX(c.checkin_time) as last_checkin,
               CASE WHEN MAX(c.checkin_time) IS NOT NULL THEN 1 ELSE 0 END as is_checked_in
        FROM users u
        LEFT JOIN checkins c ON u.employee_id = c.employee_id
        WHERE u.first_name LIKE ? COLLATE NOCASE
        OR u.last_name LIKE ? COLLATE NOCASE
        OR u.employee_id LIKE ? COLLATE NOCASE
        OR CAST(u.table_number AS TEXT) LIKE ?
        GROUP BY u.id, u.employee_id, u.first_name, u.last_name, u.table_number
        ORDER BY u.first_name, u.last_name
    """, (search_pattern, search_pattern, search_pattern, search_pattern))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        User(
            id=row["id"],
            employee_id=row["employee_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            table_number=row["table_number"],
            last_checkin=row["last_checkin"],
            is_checked_in=bool(row["is_checked_in"])
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

def clear_checkin_history() -> int:
    """Delete all checkin records, returns count of deleted records"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM checkins")
        count = cursor.fetchone()[0]
        
        # Delete all checkin records
        cursor.execute("DELETE FROM checkins")
        conn.commit()
        conn.close()
        return count
    except sqlite3.Error:
        conn.close()
        return 0

def checkout_user(employee_id: str) -> bool:
    """Remove the most recent checkin record for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete the most recent checkin for this user
        cursor.execute("""
            DELETE FROM checkins 
            WHERE employee_id = ? 
            AND checkin_time = (
                SELECT MAX(checkin_time) 
                FROM checkins 
                WHERE employee_id = ?
            )
        """, (employee_id, employee_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0
    except sqlite3.Error:
        conn.close()
        return False

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

# Authentication functions

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def has_admin_user() -> bool:
    """Check if any admin user exists"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM auth_users WHERE is_admin = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def create_initial_admin_if_needed():
    """Create initial admin from environment variables if no admin exists"""
    if has_admin_user():
        return False
    
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    return create_auth_user(admin_username, admin_password, is_admin=True)

def create_auth_user(username: str, password: str, is_admin: bool = False) -> bool:
    """Create a new auth user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO auth_users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username.lower(), password_hash, is_admin)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False
    except sqlite3.Error:
        conn.close()
        return False

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user and return user info if successful"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auth_users WHERE username = ?", (username.lower(),))
    row = cursor.fetchone()
    conn.close()
    
    if row and verify_password(password, row["password_hash"]):
        # Update last login
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE auth_users SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
            (username.lower(),)
        )
        conn.commit()
        conn.close()
        
        return {
            "id": row["id"],
            "username": row["username"],
            "is_admin": bool(row["is_admin"]),
            "created_at": row["created_at"],
            "last_login": datetime.now().isoformat()
        }
    return None

def get_auth_user(username: str) -> Optional[dict]:
    """Get auth user by username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auth_users WHERE username = ?", (username.lower(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "is_admin": bool(row["is_admin"]),
            "created_at": row["created_at"],
            "last_login": row["last_login"]
        }
    return None

def get_all_auth_users() -> List[dict]:
    """Get all auth users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, is_admin, created_at, last_login FROM auth_users ORDER BY username")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row["id"],
            "username": row["username"],
            "is_admin": bool(row["is_admin"]),
            "created_at": row["created_at"],
            "last_login": row["last_login"]
        }
        for row in rows
    ]

def delete_auth_user(username: str) -> bool:
    """Delete an auth user (except if it's the last admin)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if this is an admin
        cursor.execute("SELECT is_admin FROM auth_users WHERE username = ?", (username.lower(),))
        user = cursor.fetchone()
        
        if user and user["is_admin"]:
            # Count total admins
            cursor.execute("SELECT COUNT(*) FROM auth_users WHERE is_admin = 1")
            admin_count = cursor.fetchone()[0]
            
            if admin_count <= 1:
                conn.close()
                return False  # Can't delete the last admin
        
        cursor.execute("DELETE FROM auth_users WHERE username = ?", (username.lower(),))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    except sqlite3.Error:
        conn.close()
        return False

def create_session(username: str) -> str:
    """Create a new session for the user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate session ID
    session_id = secrets.token_urlsafe(32)
    
    # Set expiration to 30 days from now
    expires_at = datetime.now() + timedelta(days=30)
    
    cursor.execute(
        "INSERT INTO sessions (id, username, expires_at) VALUES (?, ?, ?)",
        (session_id, username.lower(), expires_at)
    )
    conn.commit()
    conn.close()
    
    return session_id

def get_session_user(session_id: str) -> Optional[dict]:
    """Get user info from session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT au.* FROM sessions s
        JOIN auth_users au ON s.username = au.username
        WHERE s.id = ? AND s.expires_at > CURRENT_TIMESTAMP
    """, (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "is_admin": bool(row["is_admin"]),
            "created_at": row["created_at"],
            "last_login": row["last_login"]
        }
    return None

def delete_session(session_id: str) -> bool:
    """Delete a session (logout)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete expired sessions
    cursor.execute("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")
    
    conn.commit()
    conn.close()
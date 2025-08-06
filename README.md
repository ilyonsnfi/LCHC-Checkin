# RFID Checkin Station

A simple web application for RFID badge checkin with admin dashboard.

## Features

- **Main Checkin Interface**: Scan RFID badges to check in users
- **Admin Dashboard**: View checkin history, export to CSV, import users
- **SQLite Database**: Stores user information and checkin logs
- **CSV Import/Export**: Manage users and export checkin data

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

3. Access the application:
- Main checkin: http://localhost:8000
- Admin dashboard: http://localhost:8000/admin

## Usage

### RFID Checkin
- The main page automatically focuses on the input field
- RFID scanners that type text and press enter will work automatically
- Shows user name and table number on successful checkin
- Displays error for unrecognized badges

### Admin Dashboard
- View all checkin history in a table
- Export checkin data to CSV
- Import users from CSV with format: First Name, Last Name, Employee ID, Table Number

## CSV Format for User Import

```csv
First Name,Last Name,Employee ID,Table Number
John,Doe,12345,1
Jane,Smith,67890,2
```
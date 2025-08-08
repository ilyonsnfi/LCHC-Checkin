# RFID Checkin Station

A modern web application for RFID badge checkin with comprehensive admin dashboard, featuring manual check-in/check-out capabilities, real-time preview, and customizable theming.

## Features

### Checkin Interface
- **Responsive Design**: 70% viewport coverage, scales to any screen size
- **RFID Integration**: Automatic badge scanning with audio feedback
- **Manual Operations**: Admin can manually check users in/out
- **Real-time Status**: Shows current checkin status and last checkin time
- **Custom Theming**: Configurable colors and background images

### Admin Dashboard
- **User Management**: View all users with checkin status and manual check-in/out
- **Checkin History**: Comprehensive logging with search functionality
- **Excel Import/Export**: Manage users and export comprehensive checkin data
- **Settings Panel**: Live preview with auto-apply functionality
- **Data Management**: Clear history, delete users with confirmations

## Quick Start with Docker

1. **Clone and run**:
```bash
git clone <repository>
cd checkin
docker-compose up -d
```

2. **Access the application**:
- Main checkin: http://localhost:8000
- Admin dashboard: http://localhost:8000/admin

## Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Usage

### RFID Checkin
- **Kiosk Mode**: Full-screen interface designed for dedicated displays
- **Auto-Detection**: RFID scanners that send text + enter work automatically
- **Success Display**: Shows welcome message and table assignment
- **Audio Feedback**: Success/error sounds for user confirmation

### Manual Check-in/out (Admin)
- **Check In**: Green button for users not currently checked in
- **Check Out**: Red button for checked-in users (removes latest checkin record)
- **Status Display**: Real-time status and last checkin timestamp
- **Silent Operation**: No confirmation popups, immediate visual feedback

### Admin Features
- **Live Settings**: Real-time preview with auto-apply changes
- **Data Export**: Comprehensive Excel export including users without checkins
- **Bulk Import**: Excel format: First Name, Last Name, Employee ID, Table Number
- **History Management**: Search, clear history, delete all users

## Docker Details

### Volumes
- `checkin_data`: Persistent database storage
- `checkin_uploads`: Background image uploads
- Database automatically mounted from host

### Environment Variables
- `DATABASE_PATH`: Database location (default: /app/data/checkin.db)
- `PYTHONPATH`: Application path
- `PYTHONUNBUFFERED`: Python output buffering

### Health Checks
- Automatic health monitoring with 30s intervals
- Container restart on failure
- 40s startup grace period

## XLSX Import Format

```csv
First Name,Last Name,Employee ID,Table Number
John,Doe,12345,1
Jane,Smith,67890,2
```
# RFID Checkin Station

A secure web application for RFID badge checkin with authentication, comprehensive admin dashboard, featuring manual check-in/check-out capabilities, real-time preview, and customizable theming.

## Features

### Authentication & Security
- **User Authentication**: Secure login system with session management
- **Role-based Access**: Separate admin and regular user accounts
- **Admin Protection**: All admin endpoints require admin privileges
- **Session Cookies**: 30-day secure HTTP-only session cookies

### Checkin Interface
- **Responsive Design**: 70% viewport coverage, scales to any screen size
- **RFID Integration**: Automatic badge scanning with audio feedback
- **Manual Operations**: Admin can manually check users in/out
- **Real-time Status**: Shows current checkin status and last checkin time
- **Custom Theming**: Configurable colors and background images

### Admin Dashboard
- **Login User Management**: Create/delete login accounts with admin privileges
- **RFID User Management**: Manage badge users separate from login users
- **Checkin History**: Comprehensive logging with search functionality
- **Excel Import/Export**: Manage users and export comprehensive checkin data
- **Settings Panel**: Live preview with auto-apply functionality
- **Data Management**: Clear history, delete users with confirmations

## Quick Start with Docker

1. **Clone the repository**:
```bash
git clone <repository>
cd checkin
```

2. **Configure authentication** (IMPORTANT):
```bash
# Edit docker-compose.yml and set secure credentials
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **Run the application**:
```bash
docker-compose up -d
```

4. **First login**:
- Navigate to: http://localhost:8000
- You'll be redirected to login page
- Use the admin credentials from docker-compose.yml
- After login, you'll see the checkin interface
- Admin users will see an "Admin" link to access the dashboard

## Manual Setup

1. **Setup environment**:
```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure authentication**:
```bash
# Copy environment template
cp .env.example .env

# Edit .env file and set secure credentials
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
```

3. **Run the application**:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Usage

### Authentication
- **First Time Setup**: Admin account is created automatically from environment variables
- **Login Required**: All users must authenticate to access the system
- **Admin vs Regular**: Only admin users can access the admin dashboard
- **Session Management**: 30-day login sessions with secure cookies

### RFID Checkin
- **Kiosk Mode**: Full-screen interface designed for dedicated displays
- **Auto-Detection**: RFID scanners that send text + enter work automatically
- **Success Display**: Shows welcome message and table assignment
- **Audio Feedback**: Success/error sounds for user confirmation

### User Management (Admin Only)
- **Login Users**: Create/manage accounts for system access (Admin panel → Login Users tab)
- **RFID Users**: Manage badge users for checkin (Admin panel → Guests tab)
- **Role Assignment**: Set admin privileges when creating login users
- **Bulk Import**: Excel format: First Name, Last Name, Employee ID, Table Number

### Manual Check-in/out (Admin)
- **Check In**: Green button for users not currently checked in
- **Check Out**: Red button for checked-in users (removes latest checkin record)
- **Status Display**: Real-time status and last checkin timestamp
- **Silent Operation**: No confirmation popups, immediate visual feedback

### Admin Features
- **Live Settings**: Real-time preview with auto-apply changes
- **Data Export**: Comprehensive Excel export including users without checkins
- **History Management**: Search, clear history, delete all users
- **Background Images**: Upload/remove custom background images

## Docker Details

### Volumes
- `checkin_data`: Persistent database storage
- `checkin_uploads`: Background image uploads
- Database automatically mounted from host

### Environment Variables
- `ADMIN_USERNAME`: Initial admin account username (required)
- `ADMIN_PASSWORD`: Initial admin account password (required)
- `SECRET_KEY`: Secret key for session security (recommended)
- `DATABASE_PATH`: Database location (default: /app/data/checkin.db)

### Health Checks
- Automatic health monitoring with 30s intervals
- Container restart on failure
- 40s startup grace period

## Security Notes

### Authentication
- **Change Default Credentials**: Always set secure `ADMIN_USERNAME` and `ADMIN_PASSWORD`
- **Session Security**: Sessions use HTTP-only cookies with 30-day expiration
- **Password Hashing**: All passwords are hashed with bcrypt
- **Admin Protection**: All admin endpoints require proper authorization

### Production Deployment
- Session cookies use `secure=True` by default (requires HTTPS in production)
- Use environment variables, never hardcode credentials
- Regularly review login users and remove unused accounts
- Consider implementing password complexity requirements
- Generate a secure `SECRET_KEY` for enhanced session security

## XLSX Import Format

```csv
First Name,Last Name,Employee ID,Table Number
John,Doe,12345,1
Jane,Smith,67890,2
```

**Note**: This imports RFID badge users, not login users. Login users must be created through the admin panel.

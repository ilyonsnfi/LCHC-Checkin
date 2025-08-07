from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import io
from datetime import datetime
from openpyxl import load_workbook
from models import CheckinResponse, ImportResponse, User, DeleteResponse, CreateUserResponse, Settings, SettingsUpdate, SettingsResponse
from database import init_db, get_user_by_employee_id, create_checkin, get_checkin_history, create_users_batch, get_all_users, delete_all_users, create_single_user, search_users, get_tables_with_users, get_export_data, clear_checkin_history, checkout_user, get_settings, update_settings

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

app = FastAPI(title="RFID Checkin Station", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def checkin_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("checkin.html", {"request": request, "settings": settings})

@app.get("/preview", response_class=HTMLResponse)
async def checkin_preview(request: Request):
    settings = get_settings()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return templates.TemplateResponse("checkin.html", {"request": request, "settings": settings, "current_time": current_time, "preview_mode": True, "show_admin_link": False})

@app.post("/checkin", response_model=CheckinResponse)
async def checkin(badge_id: str = Form(...)):
    user = get_user_by_employee_id(badge_id)
    
    if user:
        success = create_checkin(badge_id)
        if success:
            return CheckinResponse(
                success=True,
                name=f"{user.first_name} {user.last_name}",
                table_number=user.table_number,
                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            return CheckinResponse(success=False, message="Checkin failed")
    else:
        return CheckinResponse(success=False, message="Badge not found. Please see check-in attendant.")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/history")
async def get_history(search: str = ""):
    return get_checkin_history(search)

@app.get("/admin/users")
async def get_users(search: str = ""):
    if search:
        return search_users(search)
    return get_all_users()

@app.get("/admin/tables")
async def get_tables(search: str = ""):
    return get_tables_with_users(search)

@app.get("/admin/export")
async def export_xlsx():
    from openpyxl import Workbook
    
    export_data = get_export_data()
    
    # Create a new workbook and worksheet
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Checkin Data"
    
    current_row = 1
    
    # Section 1: Users with checkins
    if export_data['with_checkins']:
        # Add section header
        worksheet.cell(row=current_row, column=1, value="USERS WITH CHECKINS")
        worksheet.cell(row=current_row, column=1).font = worksheet.cell(row=current_row, column=1).font.copy(bold=True)
        current_row += 1
        
        # Add headers for checkins section
        headers = ["First Name", "Last Name", "Employee ID", "Table Number", "Checkin Time"]
        for col, header in enumerate(headers, 1):
            worksheet.cell(row=current_row, column=col, value=header)
            worksheet.cell(row=current_row, column=col).font = worksheet.cell(row=current_row, column=col).font.copy(bold=True)
        current_row += 1
        
        # Add checkin data
        for record in export_data['with_checkins']:
            worksheet.cell(row=current_row, column=1, value=record.first_name)
            worksheet.cell(row=current_row, column=2, value=record.last_name)
            worksheet.cell(row=current_row, column=3, value=record.employee_id)
            worksheet.cell(row=current_row, column=4, value=record.table_number)
            worksheet.cell(row=current_row, column=5, value=record.checkin_time)
            current_row += 1
    
    # Section 2: Users without checkins
    if export_data['without_checkins']:
        # Add spacing between sections
        current_row += 1
        
        # Add section header
        worksheet.cell(row=current_row, column=1, value="USERS WITHOUT CHECKINS")
        worksheet.cell(row=current_row, column=1).font = worksheet.cell(row=current_row, column=1).font.copy(bold=True)
        current_row += 1
        
        # Add headers for no-checkins section
        headers = ["First Name", "Last Name", "Employee ID", "Table Number", "Status"]
        for col, header in enumerate(headers, 1):
            worksheet.cell(row=current_row, column=col, value=header)
            worksheet.cell(row=current_row, column=col).font = worksheet.cell(row=current_row, column=col).font.copy(bold=True)
        current_row += 1
        
        # Add users without checkins
        for user in export_data['without_checkins']:
            worksheet.cell(row=current_row, column=1, value=user.first_name)
            worksheet.cell(row=current_row, column=2, value=user.last_name)
            worksheet.cell(row=current_row, column=3, value=user.employee_id)
            worksheet.cell(row=current_row, column=4, value=user.table_number)
            worksheet.cell(row=current_row, column=5, value="No Checkin")
            current_row += 1
    
    # Save to BytesIO
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    
    def iter_xlsx():
        yield output.read()
    
    return StreamingResponse(
        iter_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=checkin_data.xlsx"}
    )

@app.post("/admin/import", response_model=ImportResponse)
async def import_users(file: UploadFile = File(...)):
    if not file.filename:
        return ImportResponse(success=False, message="Please upload a file")
    
    # Check file extension
    filename = file.filename.lower()
    if not filename.endswith('.xlsx'):
        return ImportResponse(success=False, message="Please upload an Excel (.xlsx) file")
    
    content = await file.read()
    users = []
    errors = []
    
    try:
        # Load Excel file
        workbook = load_workbook(io.BytesIO(content))
        worksheet = workbook.active
        
        # Read header row to map column positions
        header_row = next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True))
        if not header_row:
            return ImportResponse(success=False, message="Excel file appears to be empty")
        
        # Create header mapping (case-insensitive)
        header_map = {}
        for col_idx, header in enumerate(header_row):
            if header:
                header_lower = str(header).lower().strip()
                header_map[header_lower] = col_idx
        
        # Required headers (flexible matching)
        required_fields = {
            'first_name': ['first name', 'firstname', 'first', 'fname'],
            'last_name': ['last name', 'lastname', 'last', 'lname', 'surname'],
            'employee_id': ['employee id', 'employeeid', 'employee', 'id', 'badge', 'badge id', 'employe id', 'employeid', 'emp id', 'emp_id'],
            'table_number': ['table number', 'tablenumber', 'table', 'table_number', 'table num']
        }
        
        # Find column indices for each required field
        column_indices = {}
        for field, possible_headers in required_fields.items():
            found = False
            for possible_header in possible_headers:
                if possible_header in header_map:
                    column_indices[field] = header_map[possible_header]
                    found = True
                    break
            if not found:
                missing_headers = ', '.join(possible_headers[:3])  # Show first 3 options
                return ImportResponse(
                    success=False, 
                    message=f"Missing required column for {field}. Expected one of: {missing_headers}"
                )
        
        # Process data rows
        for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                continue
            
            try:
                # Extract values using column mapping
                first_name_val = row[column_indices['first_name']] if column_indices['first_name'] < len(row) else None
                last_name_val = row[column_indices['last_name']] if column_indices['last_name'] < len(row) else None
                employee_id_val = row[column_indices['employee_id']] if column_indices['employee_id'] < len(row) else None
                table_number_val = row[column_indices['table_number']] if column_indices['table_number'] < len(row) else None
                
                # Validate required fields are not empty
                if not first_name_val or str(first_name_val).strip() == '':
                    errors.append(f"Row {row_num}: Missing first name")
                    continue
                if not last_name_val or str(last_name_val).strip() == '':
                    errors.append(f"Row {row_num}: Missing last name")
                    continue
                if not employee_id_val or str(employee_id_val).strip() == '':
                    errors.append(f"Row {row_num}: Missing employee ID")
                    continue
                if not table_number_val:
                    errors.append(f"Row {row_num}: Missing table number")
                    continue
                
                # Create user object
                user = User(
                    first_name=str(first_name_val).strip(),
                    last_name=str(last_name_val).strip(),
                    employee_id=str(employee_id_val).strip(),
                    table_number=int(table_number_val)
                )
                users.append(user)
                
            except (ValueError, TypeError) as e:
                errors.append(f"Row {row_num}: {str(e)}")
            except Exception as e:
                errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
    
    except Exception as e:
        return ImportResponse(success=False, message=f"Error reading Excel file: {str(e)}")
    
    if users:
        imported, db_errors = create_users_batch(users)
        errors.extend(db_errors)
        return ImportResponse(success=True, imported=imported, errors=errors)
    else:
        return ImportResponse(success=False, message="No valid users found", errors=errors)

@app.delete("/admin/users", response_model=DeleteResponse)
async def delete_all_users_endpoint():
    try:
        deleted_count = delete_all_users()
        return DeleteResponse(
            success=True,
            deleted=deleted_count,
            message=f"Successfully deleted {deleted_count} users"
        )
    except Exception as e:
        return DeleteResponse(
            success=False,
            message=f"Error deleting users: {str(e)}"
        )

@app.post("/admin/users", response_model=CreateUserResponse)
async def create_user_endpoint(user: User):
    try:
        success, message = create_single_user(user)
        if success:
            return CreateUserResponse(
                success=True,
                message=message,
                user=user
            )
        else:
            return CreateUserResponse(
                success=False,
                message=message
            )
    except Exception as e:
        return CreateUserResponse(
            success=False,
            message=f"Error creating user: {str(e)}"
        )

@app.get("/admin/settings", response_model=Settings)
async def get_settings_endpoint():
    settings_dict = get_settings()
    return Settings(**settings_dict)

@app.put("/admin/settings", response_model=SettingsResponse)
async def update_settings_endpoint(settings_update: SettingsUpdate):
    try:
        # Convert to dict, excluding None values
        update_dict = {k: v for k, v in settings_update.dict().items() if v is not None}
        
        if not update_dict:
            return SettingsResponse(
                success=False,
                message="No settings provided to update"
            )
        
        success = update_settings(update_dict)
        
        if success:
            updated_settings = get_settings()
            return SettingsResponse(
                success=True,
                message="Settings updated successfully",
                settings=Settings(**updated_settings)
            )
        else:
            return SettingsResponse(
                success=False,
                message="Failed to update settings"
            )
    except Exception as e:
        return SettingsResponse(
            success=False,
            message=f"Error updating settings: {str(e)}"
        )

@app.post("/admin/upload-background")
async def upload_background(file: UploadFile = File(...)):
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            return {"success": False, "message": "Please upload an image file"}
        
        # Create uploads directory if it doesn't exist
        import os
        uploads_dir = "static/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file with unique name
        import uuid
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"background_{uuid.uuid4().hex}.{file_extension}"
        file_path = f"{uploads_dir}/{filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update settings with new background image path
        web_path = f"/static/uploads/{filename}"
        update_settings({"background_image": web_path})
        
        return {"success": True, "message": "Background image uploaded successfully", "path": web_path}
    
    except Exception as e:
        return {"success": False, "message": f"Error uploading image: {str(e)}"}

@app.delete("/admin/remove-background")
async def remove_background():
    try:
        # Get current background image path
        settings = get_settings()
        current_bg = settings.get('background_image', '')
        
        # Remove from settings first
        success = update_settings({"background_image": ""})
        
        if not success:
            return {"success": False, "message": "Failed to update settings"}
        
        # Delete the physical file if it exists and is in uploads folder
        if current_bg and current_bg.startswith('/static/uploads/'):
            import os
            # Convert web path to file path
            file_path = current_bg.replace('/static/', 'static/')
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    # File deletion failed but settings were updated
                    return {"success": True, "message": "Background removed but file deletion failed", "warning": str(e)}
        
        return {"success": True, "message": "Background image removed successfully"}
    
    except Exception as e:
        return {"success": False, "message": f"Error removing background: {str(e)}"}

@app.delete("/admin/clear-history")
async def clear_checkin_history_endpoint():
    try:
        deleted_count = clear_checkin_history()
        return {
            "success": True,
            "deleted": deleted_count,
            "message": f"Successfully cleared {deleted_count} checkin records"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error clearing checkin history: {str(e)}"
        }

@app.post("/admin/checkin/{employee_id}")
async def manual_checkin(employee_id: str):
    try:
        user = get_user_by_employee_id(employee_id)
        
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        success = create_checkin(employee_id)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully checked in {user.first_name} {user.last_name}",
                "user": {
                    "name": f"{user.first_name} {user.last_name}",
                    "employee_id": employee_id,
                    "table_number": user.table_number
                }
            }
        else:
            return {
                "success": False,
                "message": "Checkin failed"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during manual checkin: {str(e)}"
        }

@app.delete("/admin/checkout/{employee_id}")
async def manual_checkout(employee_id: str):
    try:
        user = get_user_by_employee_id(employee_id)
        
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        success = checkout_user(employee_id)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully checked out {user.first_name} {user.last_name}",
                "user": {
                    "name": f"{user.first_name} {user.last_name}",
                    "employee_id": employee_id,
                    "table_number": user.table_number
                }
            }
        else:
            return {
                "success": False,
                "message": "No checkin record found to remove"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during checkout: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
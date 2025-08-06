from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import io
from datetime import datetime
from openpyxl import load_workbook
from models import CheckinResponse, ImportResponse, User, DeleteResponse
from database import init_db, get_user_by_employee_id, create_checkin, get_checkin_history, create_users_batch, get_all_users, delete_all_users

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
    return templates.TemplateResponse("checkin.html", {"request": request})

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
async def get_history():
    return get_checkin_history()

@app.get("/admin/users")
async def get_users():
    return get_all_users()

@app.get("/admin/export")
async def export_xlsx():
    from openpyxl import Workbook
    
    history = get_checkin_history()
    
    # Create a new workbook and worksheet
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Checkin History"
    
    # Add headers
    headers = ["First Name", "Last Name", "Employee ID", "Table Number", "Checkin Time"]
    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col, value=header)
    
    # Add data
    for row_idx, record in enumerate(history, 2):
        worksheet.cell(row=row_idx, column=1, value=record.first_name)
        worksheet.cell(row=row_idx, column=2, value=record.last_name)
        worksheet.cell(row=row_idx, column=3, value=record.employee_id)
        worksheet.cell(row=row_idx, column=4, value=record.table_number)
        worksheet.cell(row=row_idx, column=5, value=record.checkin_time)
    
    # Save to BytesIO
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    
    def iter_xlsx():
        yield output.read()
    
    return StreamingResponse(
        iter_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=checkin_history.xlsx"}
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
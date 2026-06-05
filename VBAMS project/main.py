import os
import mysql.connector
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware 
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import google.genai as genai
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Make sure to replace this secret key with a random string when taking your project live!
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your_super_secret_session_key"))

templates = Jinja2Templates(directory="templates")

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GOOGLE_GEMINI_API_KEY_HERE")
if GEMINI_API_KEY != "YOUR_GOOGLE_GEMINI_API_KEY_HERE":
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    print("⚠️ WARNING: GEMINI_API_KEY not set. AI features will be disabled.")

def database():
    return mysql.connector.connect(
       DB_HOST=sql12.freesqldatabase.com
       DB_USER=sql12829421
       DB_PASSWORD=dyjfhuhwwg
       DB_NAME=sql12829421
       DB_PORT=3306
    )

# Pydantic models for request bodies
class ChatRequest(BaseModel):
    message: str
    username: str = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )

@app.get("/reguser", response_class=HTMLResponse)
async def regpage(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request}
    )

@app.post("/reguser", response_class=HTMLResponse)
def createuser(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)):
    
    db = database()
    cursor = db.cursor(dictionary=True)
    
    # Check if email already exists
    cursor.execute("SELECT COUNT(*) as count FROM user WHERE email = %s", (email,))
    result = cursor.fetchone()
    
    if result['count'] > 0:
        cursor.close()
        db.close()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "request": request,
                "error": "Email already exists. Please use a different email.",
                "username": username,
                "email": email
            }
        )
    
    # Insert new user if email doesn't exist
    sql = "INSERT INTO user(username,email,password) VALUES(%s,%s,%s)"
    val = (username, email, password)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request}
    )

@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)):
    
    db = database()
    cursor = db.cursor(dictionary=True)
    
    sql_query = "SELECT * FROM user WHERE email = %s AND password = %s"
    cursor.execute(sql_query, (email, password))
    user = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if user:
        request.session["username"] = user["username"]
        return RedirectResponse(url="/frontpage", status_code=303)
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
@app.get("/frontpage", response_class=HTMLResponse)
async def front_page(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login") 

    user_context = {"username": username}
    return templates.TemplateResponse(
        request=request,
        name="front.html",
        context={"request": request, "user": user_context} 
    )

@app.post("/complaint")
def regcomplaint(
    request: Request,
    location: str = Form(...),
    issue: str = Form(...),
    other: str = Form(...),
    phone: str = Form(...),
    latitude: str = Form(default=""),
    longitude: str = Form(default="")):
    
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Please log in first")
    
    db = database()
    cursor = db.cursor(dictionary=True)
    
    # Convert coordinates to float if provided
    lat = float(latitude) if latitude else None
    lng = float(longitude) if longitude else None
    
    sql = "INSERT INTO complaint(username, location, issue, other, phone, latitude, longitude) VALUES(%s, %s, %s, %s, %s, %s, %s)"
    val = (username, location, issue, other, phone, lat, lng)
    
    cursor.execute(sql, val)
    db.commit()
    
    cursor.close()
    db.close()
    
    return RedirectResponse(url="/frontpage", status_code=303)

@app.get("/user_dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login") 
        
    db = database()
    cursor = db.cursor(dictionary=True)

    sql = "SELECT * FROM complaint WHERE username = %s "
    cursor.execute(sql, (username,))
    history = cursor.fetchall()
    total_count = len(history)

    cursor.close()
    db.close()    

    return templates.TemplateResponse(
        request=request,
        name="user_dashboard.html",
        context={
            "request": request, 
            "username": username, 
            "history": history, 
            "total_count": total_count
        } 
    )

# --- MECHANIC MODULE ROUTES ---

@app.get("/mechanic_login", response_class=HTMLResponse)
async def mechanic_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="mechanic_login.html",
        context={"request": request}
    )

@app.post("/mechanic_login", response_class=HTMLResponse)
def login_mechanic(request: Request, email: str = Form(...), password: str = Form(...)):
    db = database()
    cursor = db.cursor(dictionary=True)
    
    sql_query = "SELECT mechanicname, email FROM mechanic WHERE email = %s AND password = %s"
    cursor.execute(sql_query, (email, password))
    mechanic = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if mechanic:
        request.session["mechanicname"] = mechanic["mechanicname"]
        return RedirectResponse(url="/mechanic_dashboard", status_code=303)
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")

@app.get("/mechanic_dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request):
    mechanicname = request.session.get("mechanicname")
    if not mechanicname:
        return RedirectResponse(url="/mechanic_login")

    db = database()
    cursor = db.cursor(dictionary=True)
    
    sql_active = """
        SELECT * FROM complaint 
        WHERE status = 'Pending' 
        OR (status = 'In Progress' AND mechanicassigned = %s)
    """
    cursor.execute(sql_active, (mechanicname,))
    active_jobs = cursor.fetchall()
    
    cursor.execute("SELECT * FROM complaint WHERE status = 'Resolved'")
    completed_jobs = cursor.fetchall()
    
    cursor.close()
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="mechanic_dashboard.html",
        context={
            "request": request,
            "mechanicname": mechanicname,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs
        }
    )

@app.post("/update_status/{complaint_id}")
async def update_job_status(request: Request, complaint_id: int, status: str = Form(...)):
    mechanicname = request.session.get("mechanicname") 
    if not mechanicname:
         return RedirectResponse(url="/mechanic_login")

    db = database()
    cursor = db.cursor(dictionary=True)

    if status == "In Progress":
        cursor.execute("SELECT mechanicname, mechanicphoneno FROM mechanic WHERE mechanicname = %s", (mechanicname,))
        mech_info = cursor.fetchone()

        sql = """
            UPDATE complaint 
            SET status = %s, mechanicassigned = %s, mechanicphoneno = %s 
            WHERE complaint_id = %s
        """
        cursor.execute(sql, (status, mech_info['mechanicname'], mech_info['mechanicphoneno'], complaint_id))
    
    elif status == "Pending":
        sql = """
            UPDATE complaint 
            SET status = %s, mechanicassigned = NULL, mechanicphoneno = NULL 
            WHERE complaint_id = %s
        """
        cursor.execute(sql, (status, complaint_id))
        
    else:
        cursor.execute("UPDATE complaint SET status = %s WHERE complaint_id = %s", (status, complaint_id))

    db.commit()
    cursor.close()
    db.close()
    return RedirectResponse(url="/mechanic_dashboard", status_code=303)

# --- MECHANIC LOCATION TRACKING ---

@app.post("/update_mechanic_location")
async def update_mechanic_location(
    request: Request,
    complaint_id: int = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...)):
    
    mechanicname = request.session.get("mechanicname")
    if not mechanicname:
        raise HTTPException(status_code=401, detail="Please log in first")
    
    db = database()
    cursor = db.cursor()
    
    # Update mechanic location in complaint record
    sql = "UPDATE complaint SET mechanic_latitude = %s, mechanic_longitude = %s WHERE complaint_id = %s"
    cursor.execute(sql, (latitude, longitude, complaint_id))
    db.commit()
    cursor.close()
    db.close()
    
    return {"status": "Location updated"}

@app.get("/track_mechanic/{complaint_id}", response_class=HTMLResponse)
async def track_mechanic(request: Request, complaint_id: int):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login")
    
    db = database()
    cursor = db.cursor(dictionary=True)
    
    # Get complaint and mechanic details
    cursor.execute("""
        SELECT complaint_id, location, mechanicassigned, latitude, longitude, mechanic_latitude, mechanic_longitude, mechanicphoneno 
        FROM complaint 
        WHERE complaint_id = %s AND username = %s
    """, (complaint_id, username))
    complaint = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if not complaint:
        return RedirectResponse(url="/user_dashboard")
    
    return templates.TemplateResponse(
        request=request,
        name="track_mechanic.html",
        context={
            "request": request,
            "complaint": complaint
        }
    )

@app.get("/get_mechanic_location/{complaint_id}")
async def get_mechanic_location(request: Request, complaint_id: int):
    db = database()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT mechanic_latitude, mechanic_longitude, mechanicassigned, mechanicphoneno 
        FROM complaint 
        WHERE complaint_id = %s
    """, (complaint_id,))
    complaint = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if complaint and complaint['mechanic_latitude'] and complaint['mechanic_longitude']:
        return {
            "latitude": complaint['mechanic_latitude'],
            "longitude": complaint['mechanic_longitude'],
            "mechanic_name": complaint['mechanicassigned'],
            "mechanic_phone": complaint['mechanicphoneno']
        }
    
    return {"error": "Location not available"}

@app.post("/ai_chat")
async def ai_chat(request: Request, chat_request: ChatRequest):
    """Handle AI chat requests with retry logic"""
    if not client:
        return JSONResponse(
            status_code=400,
            content={"error": "AI service not configured. Please set GEMINI_API_KEY environment variable."}
        )
    
    try:
        # System prompt for the AI assistant
        system_prompt = """You are a helpful customer support assistant for BreakdownAssist, a 24/7 roadside vehicle assistance service. 
        You help users with:
        - General questions about our service
        - Troubleshooting common vehicle issues
        - Explaining how to use the app
        - Providing tips for vehicle maintenance
        - Answering questions about breakdown coverage
        
        Be friendly, professional, and concise. Keep responses brief and helpful."""
        
        # Create the full prompt
        full_prompt = f"{system_prompt}\n\nUser: {chat_request.message}"
        
        # Retry logic for handling temporary unavailability
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Generate response using Gemini with retry fallback
                models_to_try = [
                    'models/gemini-2.0-flash-lite',
                    'models/gemini-2.0-flash',
                    'models/gemini-2.5-flash'
                ]
                
                response = None
                for model_name in models_to_try:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=full_prompt
                        )
                        break  # Success, exit the loop
                    except Exception as model_error:
                        if attempt < max_retries - 1:
                            continue  # Try next model
                        raise model_error
                
                if response:
                    return {
                        "response": response.text,
                        "status": "success"
                    }
            except Exception as e:
                error_str = str(e)
                # If it's a 503 (unavailable), retry
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    if attempt < max_retries - 1:
                        print(f"Model unavailable, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                # For other errors, raise immediately
                raise e
        
        return JSONResponse(
            status_code=503,
            content={"error": "AI models are temporarily unavailable. Please try again in a moment."}
        )
        
    except Exception as e:
        print(f"AI Chat Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing your request: {str(e)}"}
        )

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

# ******************************** ADMIN MODULE ***************************

@app.get("/admin_login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"request": request}
    )

@app.post("/admin_login", response_class=HTMLResponse)
def login_admin(request: Request, username: str = Form(...), password: str = Form(...)):
    db = database()
    cursor = db.cursor(dictionary=True)
    
    sql_query = "SELECT username, password FROM admin WHERE username = %s AND password = %s"
    cursor.execute(sql_query, (username, password))
    admin = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if admin:
        request.session["username"] = admin["username"]
        return RedirectResponse(url="/admin_dashboard", status_code=303)
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
@app.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin_user = request.session.get("username") 
    if not admin_user:
        return RedirectResponse(url="/admin_login")

    db = database()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM mechanic")
    total_mechanics = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM complaint")
    total_complaints = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM feedback")
    total_feedbacks_count = cursor.fetchone()['count']

    cursor.execute("SELECT * FROM complaint ORDER BY complaint_id")
    all_jobs = cursor.fetchall()

    cursor.execute("SELECT mechanicname, mechanicphoneno, address, email FROM mechanic")
    mechanic_list = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={ 
            "request": request,
            "adminname": admin_user,
            "total_mechs": total_mechanics,
            "total_jobs": total_complaints,
            "all_jobs": all_jobs,
            "feedback_count": total_feedbacks_count,
            "mechanics": mechanic_list
        }
    )

@app.get("/select_mechanic")
async def select_mechanic(request: Request):
    if not request.session.get("username"):
        return RedirectResponse(url="/admin_login")
        
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT mechanicname, mechanicphoneno, address, email FROM mechanic ORDER BY mechanicname ASC")
    mechanic_list = cursor.fetchall()
    cursor.close()
    db.close()
    
    return templates.TemplateResponse(
        request=request,
        name="total_mechanic.html",
        context={ 
            "request": request,
            "mechanic": mechanic_list
        }
    )

@app.get("/delete_complaint/{complaint_id}")
async def delete_complaint(request: Request, complaint_id: int):
    if not request.session.get("username"):
        return RedirectResponse(url="/admin_login")
        
    db = database()
    cursor = db.cursor()
    cursor.execute("DELETE FROM complaint WHERE complaint_id = %s", (complaint_id,))
    db.commit()
    cursor.close()
    db.close()
    return RedirectResponse(url="/admin_dashboard")

# ***************************** ADD MECHANIC *************************

@app.get("/add_mechanic", response_class=HTMLResponse)
async def add_mechanic_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add_mechanic.html",
        context={"request": request}
    )

@app.post("/add_mechanic")
async def submit_mechanic(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Please log in first")
        
    db = database()
    cursor = db.cursor()
    sql = "INSERT INTO mechanic(mechanicname, mechanicphoneno, address, email, password) VALUES(%s,%s,%s,%s,%s)"
    val = (name, phone, address, email, password)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    
    return RedirectResponse(url="/admin_dashboard", status_code=303)

@app.get("/delete_mechanic/{mechanicname}")
async def delete_mechanic(request: Request, mechanicname: str):
    if not request.session.get("username"):
        return RedirectResponse(url="/admin_login")
        
    db = database()
    cursor = db.cursor()
    cursor.execute("DELETE FROM mechanic WHERE mechanicname = %s", (mechanicname,))
    db.commit()
    cursor.close()
    db.close()
    return RedirectResponse(url="/admin_dashboard")

#****************************** FEEDBACK ******************************

@app.post("/submit-inquiry")
async def submit_inquiry(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    content: str = Form(...)
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Please log in first")
        
    db = database()
    cursor = db.cursor()
    sql = "INSERT INTO feedback(name, email, content) VALUES(%s,%s,%s)"
    val = (name, email, content)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    
    return RedirectResponse(url="/frontpage", status_code=303)

@app.get("/select_feedback")
async def select_feedback(request: Request):
    if not request.session.get("username"):
        return RedirectResponse(url="/admin_login")
        
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM feedback ORDER BY name ASC")
    feedback = cursor.fetchall()
    cursor.close()
    db.close()
    
    return templates.TemplateResponse(
        request=request,
        name="total_feedback.html",
        context={ 
            "request": request,
            "feedback_": feedback # Match variable name inside total_feedback.html
        }
    )

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

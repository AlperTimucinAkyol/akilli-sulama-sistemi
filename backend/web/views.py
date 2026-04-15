from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "title": "Hoş Geldiniz"
    })

@router.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {
        "request": request, 
        "title": "Sistemi Tanı"
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request): 
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "title": "Giriş Yap - AgroLog", 
        "hide_nav": True
    })

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request, 
        "title": "Kayıt Ol - AgroLog", 
        "hide_nav": True
    })

@router.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "title": "Dashboard - AgroLog"
    })

@router.get("/profile", response_class=HTMLResponse, name="profile")
async def dashboard(request: Request):
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "title": "Profile - AgroLog"
    })

@router.get("/field-detail/{field_id}", response_class=HTMLResponse)
async def field_detail_page(request: Request, field_id: int):
    return templates.TemplateResponse("field_detail.html", {
        "request": request,
        "field_id": field_id,
        "title": "Tarla Detayları - AgroLog"
    })
    
@router.get("/fields", response_class=HTMLResponse)
async def fields_page(request: Request):
    return templates.TemplateResponse("fields.html", {
        "request": request, 
        "title": "Tarlalarım - AgroLog"
    })

@router.get("/irrigation/logs", response_class=HTMLResponse)
async def irrigation_logs_page(request: Request):
    return templates.TemplateResponse("irrigation_logs.html", {
        "request": request,
        "title": "Sulama Kayıtları - AgroLog"
    })
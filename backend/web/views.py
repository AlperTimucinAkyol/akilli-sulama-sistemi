from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Hoş Geldiniz"})

@router.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "title": "Sistemi Tanı"})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request): 
    referer = request.headers.get("referer")
    return templates.TemplateResponse("login.html", { "request": request, "title": "Giriş Yap - AgroLog", "hide_nav": True, "back_url": referer})

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    referer = request.headers.get("referer")
    return templates.TemplateResponse("register.html", {"request": request, "title": "Kayıt Ol - AgroLog", "hide_nav": True, "back_url": referer})

@router.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request):
    # İleride buraya DB'den son sensör verileri dönecek
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": "Dashboard"})
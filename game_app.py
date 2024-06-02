from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

game_app = FastAPI()

# 挂载静态文件目录
game_app.mount("/static", StaticFiles(directory="static"), name="static")

# 使用Jinja2模板
templates = Jinja2Templates(directory="templates")

@game_app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

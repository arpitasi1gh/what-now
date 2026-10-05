# src/what_now/main.py
"""FastAPI app: routes for tasks, check-in, and action feedback."""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import agent, db

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="What Now?")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    tasks = db.list_active_tasks()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"tasks": tasks},
    )


@app.post("/tasks", response_class=HTMLResponse)
def create_task(
    request: Request,
    title: str = Form(...),
    deadline: str = Form(""),
    estimated_minutes: int = Form(...),
    energy_cost: str = Form(...),
    importance: int = Form(...),
):
    db.add_task(title, deadline or None, estimated_minutes, energy_cost, importance)
    tasks = db.list_active_tasks()
    return templates.TemplateResponse(
        request,
        "_task_list.html",
        {"tasks": tasks},
    )


@app.post("/tasks/{task_id}/complete", response_class=HTMLResponse)
def complete_task_route(task_id: int, request: Request):
    db.complete_task(task_id)
    tasks = db.list_active_tasks()
    return templates.TemplateResponse(
        request,
        "_task_list.html",
        {"tasks": tasks},
    )


@app.post("/checkin", response_class=HTMLResponse)
async def checkin(
    request: Request,
    energy: int = Form(...),
    available_minutes: int = Form(...),
):
    tasks = db.list_active_tasks()
    context = {
        "time": datetime.now().strftime("%H:%M"),
        "energy": energy,
        "available_minutes": available_minutes,
        "tasks": [
            {k: t[k] for k in ("title", "deadline", "estimated_minutes", "energy_cost", "importance")}
            for t in tasks
        ],
    }

    try:
        action = await agent.get_next_action(context)
    except agent.AgentError as exc:
        return HTMLResponse(f'<div class="error">Could not get a suggestion: {exc}</div>')

    # Best-effort link: if a task title appears in the action text, log against it.
    task_id = None
    for t in tasks:
        if t["title"].lower() in action["action"].lower():
            task_id = t["id"]
            break

    action_id = db.log_action(task_id, action)
    return templates.TemplateResponse(
        request,
        "_action_card.html",
        {"action": action, "action_id": action_id},
    )


@app.post("/feedback/{action_id}", response_class=HTMLResponse)
def feedback(action_id: int, outcome: str = Form(...)):
    db.record_outcome(action_id, outcome)
    return HTMLResponse(
        '<div class="thanks">Logged. Check in again when you want the next move.</div>'
    )
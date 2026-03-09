from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import time
import os
import json

from app.preprocessing import clean_text
from app.categorization import analyze_ticket
from app.kb_retrieval import kb
from app.reply_generation import generate_draft_reply

app = FastAPI(
    title="Customer Support Ticket Triage System",
    description="AI-powered triage with customer chat assistant and admin dashboard.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ─── In-memory ticket store ──────────────────────────────────────────
tickets_store = {}  # ticket_id -> ticket dict

# Confidence threshold: below this percentage (0-100), the AI defers to admin
KB_CONFIDENCE_THRESHOLD = 60  # percent

# Admin response time in hours (configurable)
ADMIN_RESPONSE_HOURS = 2


# ─── Models ──────────────────────────────────────────────────────────
class TicketRequest(BaseModel):
    subject: str
    body: str
    channel: Optional[str] = "chat"
    customer_id: Optional[str] = None

class AdminReplyRequest(BaseModel):
    ticket_id: str
    admin_reply: str

class AdminSettingsRequest(BaseModel):
    response_hours: Optional[int] = None
    confidence_threshold: Optional[float] = None

class AdminLoginRequest(BaseModel):
    username: str
    password: str


# ─── Health ──────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "3.0.0"}


# ─── Customer Chat: Submit a ticket ─────────────────────────────────
@app.post("/api/triage", tags=["Customer"])
def triage_ticket(ticket: TicketRequest):
    cleaned_subject = clean_text(ticket.subject)
    cleaned_body = clean_text(ticket.body)

    queue, ticket_type, priority = analyze_ticket(cleaned_subject, cleaned_body)

    combined_query = f"{cleaned_subject} {cleaned_body}"
    retrieved_docs = kb.search(combined_query, top_k=3)

    raw_score = retrieved_docs[0]["score"] if retrieved_docs else 0.0
    # Normalize to 0-100 percentage (cap at 100)
    confidence_pct = min(round(raw_score * 500, 1), 100.0)  # scale TF-IDF scores

    # Decide: AI answers or defers to admin
    if confidence_pct >= KB_CONFIDENCE_THRESHOLD and retrieved_docs:
        draft = generate_draft_reply(queue, ticket_type, priority, retrieved_docs, ticket.subject)
        status = "answered_by_ai"
    else:
        draft = (
            f"Hello,\n\nThank you for reaching out regarding '{ticket.subject}'.\n\n"
            f"We don't have enough information in our knowledge base to answer this right now. "
            f"Our support team will reach out to you in about **{ADMIN_RESPONSE_HOURS} hour(s)**.\n\n"
            f"Best regards,\nCustomer Support Team"
        )
        status = "pending_admin"

    ticket_id = str(uuid.uuid4())[:8]
    ticket_data = {
        "ticket_id": ticket_id,
        "subject": ticket.subject,
        "body": ticket.body,
        "channel": ticket.channel,
        "customer_id": ticket.customer_id,
        "queue": queue,
        "ticket_type": ticket_type,
        "priority": priority,
        "status": status,
        "ai_reply": draft,
        "admin_reply": None,
        "kb_sources": [
            {"title": d["title"], "source": d["source"], "snippet": d["snippet"][:300], "score": round(d["score"], 4)}
            for d in retrieved_docs
        ],
        "confidence_score": confidence_pct,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "resolved_at": None
    }
    tickets_store[ticket_id] = ticket_data

    return {
        "ticket_id": ticket_id,
        "status": status,
        "reply": draft,
        "queue": queue,
        "ticket_type": ticket_type,
        "priority": priority,
        "confidence_score": confidence_pct,
        "kb_sources": [d["title"] for d in retrieved_docs],
        "response_hours": ADMIN_RESPONSE_HOURS if status == "pending_admin" else None
    }


# ─── Customer: Check ticket status ──────────────────────────────────
@app.get("/api/ticket/{ticket_id}", tags=["Customer"])
def get_ticket(ticket_id: str):
    if ticket_id not in tickets_store:
        return {"error": "Ticket not found"}
    t = tickets_store[ticket_id]
    reply = t["admin_reply"] if t["admin_reply"] else t["ai_reply"]
    return {
        "ticket_id": t["ticket_id"],
        "subject": t["subject"],
        "status": t["status"],
        "reply": reply,
        "queue": t["queue"],
        "priority": t["priority"]
    }


# ─── Admin: Login ───────────────────────────────────────────────────
@app.post("/api/admin/login", tags=["Admin"])
def admin_login(req: AdminLoginRequest):
    if req.username == "admin124" and req.password == "admin":
        return {"success": True, "token": "mock-jwt-token-7x92v"}
    return {"success": False, "error": "Invalid credentials"}


# ─── Admin: Get all tickets ─────────────────────────────────────────
@app.get("/api/admin/tickets", tags=["Admin"])
def admin_get_tickets():
    all_tickets = sorted(tickets_store.values(), key=lambda t: t["created_at"], reverse=True)
    return {"tickets": all_tickets, "total": len(all_tickets)}


# ─── Admin: Get only pending tickets ─────────────────────────────────
@app.get("/api/admin/pending", tags=["Admin"])
def admin_get_pending():
    pending = [t for t in tickets_store.values() if t["status"] == "pending_admin"]
    pending.sort(key=lambda t: t["created_at"], reverse=True)
    return {"tickets": pending, "total": len(pending)}


# ─── Admin: Respond to a ticket (adds answer to KB) ─────────────────
@app.post("/api/admin/reply", tags=["Admin"])
def admin_reply(req: AdminReplyRequest):
    if req.ticket_id not in tickets_store:
        return {"error": "Ticket not found"}

    t = tickets_store[req.ticket_id]
    t["admin_reply"] = req.admin_reply
    t["status"] = "answered_by_admin"
    t["resolved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Add admin reply to the KB for future queries
    kb_title = f"Admin KB: {t['subject']}"
    kb_content = f"Q: {t['subject']}\n{t['body']}\n\nA: {req.admin_reply}"
    kb._add_doc(kb_title, kb_content, f"admin_reply:{req.ticket_id}")
    print(f"KB updated: added article '{kb_title}' (total: {len(kb.documents)})")

    return {
        "success": True,
        "ticket_id": req.ticket_id,
        "kb_articles_total": len(kb.documents)
    }


# ─── Admin: Update settings ─────────────────────────────────────────
@app.post("/api/admin/settings", tags=["Admin"])
def admin_settings(req: AdminSettingsRequest):
    global ADMIN_RESPONSE_HOURS, KB_CONFIDENCE_THRESHOLD
    if req.response_hours is not None:
        ADMIN_RESPONSE_HOURS = req.response_hours
    if req.confidence_threshold is not None:
        KB_CONFIDENCE_THRESHOLD = req.confidence_threshold
    return {
        "response_hours": ADMIN_RESPONSE_HOURS,
        "confidence_threshold": KB_CONFIDENCE_THRESHOLD
    }


# ─── Admin: Get dashboard stats ─────────────────────────────────────
@app.get("/api/admin/stats", tags=["Admin"])
def admin_stats():
    total = len(tickets_store)
    ai_answered = sum(1 for t in tickets_store.values() if t["status"] == "answered_by_ai")
    pending = sum(1 for t in tickets_store.values() if t["status"] == "pending_admin")
    admin_answered = sum(1 for t in tickets_store.values() if t["status"] == "answered_by_admin")
    from collections import Counter
    queues = Counter(t["queue"] for t in tickets_store.values())
    priorities = Counter(t["priority"] for t in tickets_store.values())
    return {
        "total_tickets": total,
        "ai_answered": ai_answered,
        "pending_admin": pending,
        "admin_answered": admin_answered,
        "queues": dict(queues),
        "priorities": dict(priorities),
        "kb_articles": len(kb.documents),
        "response_hours": ADMIN_RESPONSE_HOURS,
        "confidence_threshold": KB_CONFIDENCE_THRESHOLD
    }


# ─── Serve Frontend ─────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/", tags=["Frontend"])
def serve_home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/login", tags=["Frontend"])
def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/admin", tags=["Frontend"])
def serve_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))

# Serve static files (CSS, JS)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = os.environ.get("DB_PATH", "huorengan.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            invite_code TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


class RegisterPayload(BaseModel):
    email: str
    inviteCode: str = ""


@app.get("/")
def root():
    return {"ok": True, "service": "活人感 注册后台"}


@app.post("/register")
def register(payload: RegisterPayload):
    if not payload.email or "@" not in payload.email:
        raise HTTPException(400, "invalid email")
    conn = get_db()
    now = datetime.datetime.utcnow().isoformat() + "Z"
    conn.execute(
        "INSERT INTO registrations (email, invite_code, created_at) VALUES (?, ?, ?)",
        (payload.email.strip(), payload.inviteCode.strip(), now),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/registrations")
def list_registrations():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, email, invite_code, created_at FROM registrations ORDER BY id DESC LIMIT 200"
    ).fetchall()
    conn.close()
    return {
        "count": len(rows),
        "registrations": [
            {
                "id": r["id"],
                "email": r["email"],
                "inviteCode": r["invite_code"],
                "createdAt": r["created_at"],
            }
            for r in rows
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))

import time
import uuid

from app.config import settings

# session_id -> {"history": list[dict], "created_at": float, "last_accessed_at": float}
_sessions: dict[str, dict] = {}


def create_session() -> str:
    """Create a new session and return its ID."""
    session_id = uuid.uuid4().hex[:12]
    now = time.time()
    _sessions[session_id] = {
        "history": [],
        "created_at": now,
        "last_accessed_at": now,
    }
    _cleanup_expired()
    return session_id


def get_history(session_id: str) -> list[dict]:
    """Get conversation history for a session. Returns empty list if session not found."""
    _cleanup_expired()
    session = _sessions.get(session_id)
    if not session:
        return []
    session["last_accessed_at"] = time.time()
    return session["history"]


def add_message(session_id: str, role: str, content: str) -> None:
    """Add a message to the session history. Creates session if not exists."""
    now = time.time()
    if session_id not in _sessions:
        _sessions[session_id] = {
            "history": [],
            "created_at": now,
            "last_accessed_at": now,
        }

    session = _sessions[session_id]
    session["last_accessed_at"] = now
    session["history"].append({"role": role, "content": content})

    # Trim to last 20 messages to manage context window
    if len(session["history"]) > 20:
        session["history"] = session["history"][-20:]


def get_session(session_id: str) -> dict | None:
    """Get full session data including history. Returns None if not found or expired."""
    _cleanup_expired()
    session = _sessions.get(session_id)
    if not session:
        return None
    session["last_accessed_at"] = time.time()
    return {
        "id": session_id,
        "history": session["history"],
        "created_at": session["created_at"],
        "msg_count": len(session["history"]),
    }


def list_sessions() -> list[dict]:
    """Return metadata for all active sessions with at least one message."""
    _cleanup_expired()
    result = []
    for sid, s in _sessions.items():
        history = s["history"]
        if not history:
            continue
        # Use first user message as title
        title = "新对话"
        for msg in history:
            if msg.get("role") == "user":
                title = msg["content"][:30]
                break
        result.append({
            "id": sid,
            "title": title,
            "created_at": s["created_at"],
            "msg_count": len(history),
        })
    # Sort newest first
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return result


def delete_session(session_id: str) -> bool:
    """Delete a session by ID. Returns True if deleted, False if not found."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def _cleanup_expired() -> None:
    """Remove sessions where last_accessed_at exceeds TTL."""
    now = time.time()
    expired = [
        sid
        for sid, s in _sessions.items()
        if now - s["last_accessed_at"] > settings.session_ttl_seconds
    ]
    for sid in expired:
        del _sessions[sid]

import time
import uuid

from app.config import settings

# session_id -> {"history": list[dict], "created_at": float}
_sessions: dict[str, dict] = {}


def create_session() -> str:
    """Create a new session and return its ID."""
    session_id = uuid.uuid4().hex[:12]
    _sessions[session_id] = {
        "history": [],
        "created_at": time.time(),
    }
    _cleanup_expired()
    return session_id


def get_history(session_id: str) -> list[dict]:
    """Get conversation history for a session. Returns empty list if session not found."""
    _cleanup_expired()
    session = _sessions.get(session_id)
    if not session:
        return []
    return session["history"]


def add_message(session_id: str, role: str, content: str) -> None:
    """Add a message to the session history. Creates session if not exists."""
    if session_id not in _sessions:
        _sessions[session_id] = {
            "history": [],
            "created_at": time.time(),
        }

    history = _sessions[session_id]["history"]
    history.append({"role": role, "content": content})

    # Trim to last 20 messages to manage context window
    if len(history) > 20:
        _sessions[session_id]["history"] = history[-20:]


def _cleanup_expired() -> None:
    """Remove expired sessions."""
    now = time.time()
    expired = [
        sid
        for sid, s in _sessions.items()
        if now - s["created_at"] > settings.session_ttl_seconds
    ]
    for sid in expired:
        del _sessions[sid]

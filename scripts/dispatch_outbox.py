"""Drain durable audit intents without running the HTTP server."""
import json
from app.db.session import init_db
from app.core.outbox import dispatch_pending
if __name__ == "__main__":
    init_db()
    print(json.dumps(dispatch_pending()))

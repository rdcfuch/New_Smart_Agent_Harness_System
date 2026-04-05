import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app import db, socketio
from app.models import Event


class EventBusService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.events_path = Path("/Users/jackyfox/New_Smart_Agent_Harness_System/.worktrees/events.jsonl")
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.events_path.exists():
            self.events_path.write_text("")

    def emit(
        self,
        event_type: str,
        sender_id: str = None,
        receiver_id: str = None,
        payload: dict = None,
        error: str = None,
        trace_id: str = None,
        priority: int = 5,
    ) -> Event:
        if not trace_id:
            trace_id = str(uuid.uuid4())

        event = Event(
            id=str(uuid.uuid4()),
            trace_id=trace_id,
            event_type=event_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            priority=priority,
            payload=payload or {},
            error=error,
            timestamp=datetime.utcnow(),
        )

        db.session.add(event)
        db.session.commit()

        self._write_to_file(event)

        self._broadcast(event)

        return event

    def _write_to_file(self, event: Event):
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def _broadcast(self, event: Event):
        try:
            socketio.emit(
                "event",
                event.to_dict(),
                namespace="/ws/events",
            )
        except Exception:
            pass

    def list_recent(self, limit: int = 50, event_type: str = None) -> list[dict]:
        query = Event.query
        if event_type:
            query = query.filter(Event.event_type == event_type)
        events = (
            query.order_by(Event.timestamp.desc())
            .limit(min(limit, 200))
            .all()
        )
        return [e.to_dict() for e in reversed(events)]

    def get_by_trace(self, trace_id: str) -> list[Event]:
        return Event.query.filter(Event.trace_id == trace_id).order_by(Event.timestamp.asc()).all()

    def emit_task_created(self, task_id: str, subject: str, sender_id: str = None):
        return self.emit(
            event_type="task.created",
            sender_id=sender_id,
            payload={"task_id": task_id, "subject": subject},
        )

    def emit_task_completed(self, task_id: str, sender_id: str = None):
        return self.emit(
            event_type="task.completed",
            sender_id=sender_id,
            payload={"task_id": task_id},
        )

    def emit_worktree_created(self, name: str, path: str, task_id: str = None):
        return self.emit(
            event_type="worktree.created",
            payload={"name": name, "path": path, "task_id": task_id},
        )

    def emit_worktree_removed(self, name: str):
        return self.emit(
            event_type="worktree.removed",
            payload={"name": name},
        )

    def emit_agent_registered(self, agent_id: str, agent_type: str, name: str):
        return self.emit(
            event_type="agent.registered",
            payload={"agent_id": agent_id, "agent_type": agent_type, "name": name},
        )
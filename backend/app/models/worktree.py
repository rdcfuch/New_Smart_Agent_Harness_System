import uuid
from datetime import datetime
from enum import Enum
from app import db


class WorktreeStatus(str, Enum):
    ACTIVE = "active"
    KEPT = "kept"
    REMOVED = "removed"
    FAILED = "failed"


class Worktree(db.Model):
    __tablename__ = "worktrees"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)

    path = db.Column(db.String(500), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    base_ref = db.Column(db.String(100), default="HEAD")

    status = db.Column(db.String(20), default=WorktreeStatus.ACTIVE.value)

    task_id = db.Column(db.String(36), db.ForeignKey("tasks.id"), nullable=True)
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    removed_at = db.Column(db.DateTime, nullable=True)
    kept_at = db.Column(db.DateTime, nullable=True)

    task = db.relationship("Task", backref="worktrees", lazy=True)
    agent = db.relationship("Agent", backref="worktrees", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "branch": self.branch,
            "base_ref": self.base_ref,
            "status": self.status,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "removed_at": self.removed_at.isoformat() if self.removed_at else None,
            "kept_at": self.kept_at.isoformat() if self.kept_at else None,
        }
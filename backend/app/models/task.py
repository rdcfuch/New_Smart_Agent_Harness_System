import uuid
from datetime import datetime
from enum import Enum
from app import db


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_number = db.Column(db.Integer, unique=True, nullable=False)

    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), default=TaskStatus.PENDING.value)
    priority = db.Column(db.Integer, default=TaskPriority.NORMAL.value)

    owner = db.Column(db.String(100), nullable=True)
    blocked_by = db.Column(db.JSON, default=list)

    worktree_name = db.Column(db.String(100), nullable=True)
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=True)

    result = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    agent = db.relationship("Agent", back_populates="tasks")
    project = db.relationship("Project", back_populates="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "task_number": self.task_number,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "owner": self.owner,
            "blocked_by": self.blocked_by,
            "worktree_name": self.worktree_name,
            "agent_id": self.agent_id,
            "project_id": self.project_id,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
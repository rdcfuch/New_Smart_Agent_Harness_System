import uuid
from datetime import datetime
from enum import Enum
from app import db


class AgentType(str, Enum):
    ORCHESTRATOR = "ORCHESTRATOR"
    PERSONAL_TWIN = "PERSONAL_TWIN"
    DOMAIN_EXPERT = "DOMAIN_EXPERT"
    TASK_EXECUTOR = "TASK_EXECUTOR"
    EVALUATOR = "EVALUATOR"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class Agent(db.Model):
    __tablename__ = "agents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    agent_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default=AgentStatus.IDLE.value)
    version = db.Column(db.String(20), default="1.0.0")

    description = db.Column(db.Text, nullable=True)
    system_prompt = db.Column(db.Text, nullable=True)

    resource_access = db.Column(db.JSON, default=list)
    permission_level = db.Column(db.String(20), default="RESTRICTED")
    memory_focus = db.Column(db.String(50), nullable=True)
    special_attributes = db.Column(db.JSON, default=dict)

    parent_id = db.Column(db.String(36), nullable=True)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, nullable=True)

    tasks = db.relationship("Task", back_populates="agent", lazy="dynamic")
    project = db.relationship("Project", back_populates="agents")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status,
            "version": self.version,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "resource_access": self.resource_access,
            "permission_level": self.permission_level,
            "memory_focus": self.memory_focus,
            "special_attributes": self.special_attributes,
            "parent_id": self.parent_id,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }
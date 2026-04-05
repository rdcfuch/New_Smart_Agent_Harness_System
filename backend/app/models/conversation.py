import uuid
from datetime import datetime
from app import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False)
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=False)

    messages = db.Column(db.JSON, default=list)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship("Project", backref="conversations")
    agent = db.relationship("Agent", backref="conversations")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "messages": self.messages or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
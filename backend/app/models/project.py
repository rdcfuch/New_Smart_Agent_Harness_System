import uuid
from datetime import datetime
from app import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    sandbox_path = db.Column(db.String(500), nullable=True)
    context = db.Column(db.Text, nullable=True)
    memory_path = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agents = db.relationship("Agent", back_populates="project")
    tasks = db.relationship("Task", back_populates="project")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sandbox_path": self.sandbox_path,
            "context": self.context,
            "memory_path": self.memory_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
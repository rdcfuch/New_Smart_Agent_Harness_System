import uuid
from datetime import datetime
from app import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = db.Column(db.String(36), nullable=False)

    event_type = db.Column(db.String(50), nullable=False)
    sender_id = db.Column(db.String(36), nullable=True)
    receiver_id = db.Column(db.String(36), nullable=True)

    priority = db.Column(db.Integer, default=5)

    payload = db.Column(db.JSON, default=dict)
    error = db.Column(db.Text, nullable=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "event_type": self.event_type,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "priority": self.priority,
            "payload": self.payload,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
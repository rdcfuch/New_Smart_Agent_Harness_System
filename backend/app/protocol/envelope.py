import uuid
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Intent(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    DELEGATE = "DELEGATE"
    RESUME = "RESUME"
    HALT = "HALT"
    CALL_MCP_TOOL = "CALL_MCP_TOOL"
    MAINTENANCE_AUDIT = "MAINTENANCE_AUDIT"


@dataclass
class EnvelopeHeader:
    trace_id: str
    sender_id: str
    receiver_id: str
    priority: int = 5
    timestamp: float = field(default_factory=lambda: __import__("time").time())


@dataclass
class CognitiveContext:
    risk_level: float = 0.0
    persona_vibe: str = ""
    decision_weights: dict = field(default_factory=dict)


@dataclass
class ContinuityMeta:
    checkpoint_token: Optional[str] = None
    is_resumed: bool = False
    retry_count: int = 0


@dataclass
class MCPMeta:
    method: str = ""
    params: dict = field(default_factory=dict)


@dataclass
class AgentEnvelope:
    header: EnvelopeHeader
    payload: dict
    signature: str = ""

    def to_dict(self):
        return {
            "header": {
                "trace_id": self.header.trace_id,
                "sender_id": self.header.sender_id,
                "receiver_id": self.header.receiver_id,
                "priority": self.header.priority,
                "timestamp": self.header.timestamp,
            },
            "payload": self.payload,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict):
        header = EnvelopeHeader(
            trace_id=data["header"]["trace_id"],
            sender_id=data["header"]["sender_id"],
            receiver_id=data["header"]["receiver_id"],
            priority=data["header"].get("priority", 5),
            timestamp=data["header"].get("timestamp", 0),
        )
        return cls(
            header=header,
            payload=data["payload"],
            signature=data.get("signature", ""),
        )

    @classmethod
    def create(
        cls,
        sender_id: str,
        receiver_id: str,
        intent: Intent,
        content: any = None,
        cognitive_context: CognitiveContext = None,
        continuity_meta: ContinuityMeta = None,
        mcp_meta: MCPMeta = None,
        priority: int = 5,
    ):
        header = EnvelopeHeader(
            trace_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            priority=priority,
        )
        payload = {
            "intent": intent.value,
            "content": content,
        }
        if cognitive_context:
            payload["cognitive_context"] = {
                "risk_level": cognitive_context.risk_level,
                "persona_vibe": cognitive_context.persona_vibe,
                "decision_weights": cognitive_context.decision_weights,
            }
        if continuity_meta:
            payload["continuity_meta"] = {
                "checkpoint_token": continuity_meta.checkpoint_token,
                "is_resumed": continuity_meta.is_resumed,
                "retry_count": continuity_meta.retry_count,
            }
        if mcp_meta:
            payload["mcp_meta"] = {
                "method": mcp_meta.method,
                "params": mcp_meta.params,
            }
        return cls(header=header, payload=payload)


def sign_envelope(envelope: AgentEnvelope, secret: str = "") -> AgentEnvelope:
    import hashlib
    content = str(envelope.to_dict())
    envelope.signature = hashlib.sha256(
        (content + secret).encode()
    ).hexdigest()[:16]
    return envelope
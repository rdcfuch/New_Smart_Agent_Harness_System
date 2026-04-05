import uuid
from datetime import datetime
from typing import Optional
from app import db
from app.models import Agent, AgentType, AgentStatus


class AgentRegistry:
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

    def create(
        self,
        name: str,
        agent_type: str,
        description: str = "",
        system_prompt: str = "",
        resource_access: list = None,
        permission_level: str = "RESTRICTED",
        memory_focus: str = "",
        special_attributes: dict = None,
        parent_id: str = None,
        project_id: str = None,
    ) -> Agent:
        agent = Agent(
            id=str(uuid.uuid4()),
            name=name,
            agent_type=agent_type,
            description=description,
            system_prompt=system_prompt,
            resource_access=resource_access or [],
            permission_level=permission_level,
            memory_focus=memory_focus,
            special_attributes=special_attributes or {},
            parent_id=parent_id,
            project_id=project_id,
            status=AgentStatus.IDLE.value,
        )
        db.session.add(agent)
        db.session.commit()
        return agent

    def get(self, agent_id: str) -> Optional[Agent]:
        return db.session.get(Agent, agent_id)

    def list_all(self, agent_type: str = None, status: str = None) -> list[Agent]:
        query = Agent.query
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        if status:
            query = query.filter(Agent.status == status)
        return query.all()

    def list_active(self) -> list[Agent]:
        return Agent.query.filter(Agent.status == AgentStatus.ACTIVE.value).all()

    def update_status(self, agent_id: str, status: str) -> Optional[Agent]:
        agent = self.get(agent_id)
        if agent:
            agent.status = status
            agent.last_active_at = datetime.utcnow()
            db.session.commit()
        return agent

    def update(self, agent_id: str, **kwargs) -> Optional[Agent]:
        agent = self.get(agent_id)
        if not agent:
            return None
        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        agent.updated_at = datetime.utcnow()
        db.session.commit()
        return agent

    def terminate(self, agent_id: str) -> bool:
        agent = self.get(agent_id)
        if not agent:
            return False
        agent.status = AgentStatus.TERMINATED.value
        db.session.commit()
        return True

    def find_by_type_and_project(
        self, agent_type: str, project_id: str = None
    ) -> list[Agent]:
        query = Agent.query.filter(Agent.agent_type == agent_type)
        if project_id:
            query = query.filter(Agent.project_id == project_id)
        return query.all()

    def heartbeat(self, agent_id: str) -> bool:
        agent = self.get(agent_id)
        if agent:
            agent.last_active_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
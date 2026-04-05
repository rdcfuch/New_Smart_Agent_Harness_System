from app.services.tool_registry import get_tool_registry, ToolRegistry


class AgentToolService:
    """Service that allows agents to execute tools."""

    def __init__(self):
        self.registry = get_tool_registry()

    def execute_tool(self, agent_id: str, tool_name: str, params: dict) -> dict:
        """
        Execute a tool on behalf of an agent.
        Returns the result of the tool execution.
        """
        from app.models import Agent, AgentType

        # Verify agent exists and is active
        from app import db
        agent = db.session.get(Agent, agent_id)
        if not agent:
            return {"error": "Agent not found"}
        if agent.status == "terminated":
            return {"error": "Agent is terminated"}

        # TASK_EXECUTOR can use tools, ORCHESTRATOR can also delegate
        allowed_types = [AgentType.TASK_EXECUTOR.value, AgentType.ORCHESTRATOR.value]
        if agent.agent_type not in allowed_types:
            return {"error": f"Agent type {agent.agent_type} cannot execute tools"}

        # Execute the tool
        result = self.registry.execute(tool_name, **params)

        return result.to_dict()

    def get_available_tools(self, agent_id: str = None) -> list:
        """Get list of tools available to agents."""
        return self.registry.list_tools()


def get_agent_tool_service() -> AgentToolService:
    return AgentToolService()
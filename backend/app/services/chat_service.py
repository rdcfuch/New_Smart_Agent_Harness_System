import uuid
from datetime import datetime
from app.models.conversation import Conversation
from app import db


class ChatService:
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
        from app.services.llm_service import get_llm_service
        self.llm = get_llm_service()

    def get_or_create_conversation(self, project_id: str, agent_id: str) -> Conversation:
        """Get existing conversation or create new one for project + agent."""
        conv = Conversation.query.filter_by(
            project_id=project_id,
            agent_id=agent_id
        ).first()

        if not conv:
            conv = Conversation(
                project_id=project_id,
                agent_id=agent_id,
                messages=list()
            )
            db.session.add(conv)
            db.session.commit()

        if conv.messages is None:
            conv.messages = []
            db.session.commit()

        return conv

    def send_message(self, project_id: str, agent_id: str, user_message: str) -> dict:
        """
        Send a message to an agent and get response.
        Only ORCHESTRATOR agents can respond to users.
        Parses LLM text output to detect and execute tool commands.
        """
        from app.models import Agent, AgentType
        from app.services.llm_service import get_tool_registry, TOOLS
        import re

        agent = db.session.get(Agent, agent_id)
        if not agent:
            return {"error": "Agent not found"}

        if agent.agent_type != AgentType.ORCHESTRATOR.value:
            return {"error": f"Agent type {agent.agent_type} cannot receive direct user messages. Only ORCHESTRATOR can."}

        from app.models import Project
        project = db.session.get(Project, project_id)
        if not project:
            return {"error": "Project not found"}

        conv = self.get_or_create_conversation(project_id, agent_id)
        history = list(conv.messages) if conv.messages else []
        system_prompt = self._build_system_prompt(agent, project)

        # Add user message
        history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Get LLM response with tools
        result = self.llm.chat_with_tools(
            system_prompt=system_prompt,
            messages=history,
            tools=TOOLS,
            max_tokens=4096
        )

        tool_calls = result.get("tool_calls", [])
        response_text = result.get("text")

        # Execute tool calls if LLM requested them
        if tool_calls:
            registry = get_tool_registry()
            tool_results = []

            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("input", {})
                try:
                    tool_result = registry.execute(tool_name, **tool_input)
                    tool_results.append({
                        "name": tool_name,
                        "result": tool_result.to_dict()
                    })
                except Exception as e:
                    tool_results.append({
                        "name": tool_name,
                        "result": {"success": False, "error": str(e)}
                    })

            # Add assistant tool use message
            history.append({
                "role": "assistant",
                "content": f"[TOOL_CALL: {tool_calls[0]['name']}]",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Add tool results as user message
            history.append({
                "role": "user",
                "content": f"Tool results: {tool_results}",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Get final response from LLM after tool execution
            response_text = self.llm.chat_with_context(
                system_prompt=system_prompt + "\n\nThe tools have been executed. Provide a summary of what was done.",
                messages=history,
                max_tokens=4096
            )

        # Persist conversation
        messages_copy = list(conv.messages)
        messages_copy.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        messages_copy.append({
            "role": "assistant",
            "content": response_text or "Processed",
            "timestamp": datetime.utcnow().isoformat()
        })
        conv.messages = messages_copy
        db.session.commit()

        return {
            "conversation_id": conv.id,
            "response": response_text,
            "messages": list(conv.messages)
        }

    def _build_system_prompt(self, agent: "Agent", project: "Project") -> str:
        """Build system prompt from agent and project context."""
        prompt_parts = [
            f"You are {agent.name}, an AI assistant.",
            f"Project: {project.name}",
        ]

        if project.description:
            prompt_parts.append(f"Description: {project.description}")

        if project.context:
            prompt_parts.append(f"Context: {project.context}")

        if project.sandbox_path:
            prompt_parts.append(f"Project files are in: {project.sandbox_path}")
            prompt_parts.append("To access files, use paths relative to ProjectSandbox directory, e.g., 'ProjectSandbox/myproject/sandbox/file.txt'")

        if agent.system_prompt:
            prompt_parts.append(f"\nAdditional instructions:\n{agent.system_prompt}")

        if project.sandbox_path:
            prompt_parts.append(
                f"\nProject files are in: {project.sandbox_path}"
                f"\nWhen creating files, use write_file tool with path: ProjectSandbox/{project.name}/sandbox/filename"
            )

        return "\n\n".join(prompt_parts)

    def get_conversation_history(self, project_id: str, agent_id: str) -> list:
        """Get conversation history for a project + agent."""
        conv = Conversation.query.filter_by(
            project_id=project_id,
            agent_id=agent_id
        ).first()
        return conv.messages if conv else []

    def clear_conversation(self, project_id: str, agent_id: str) -> bool:
        """Clear conversation history."""
        conv = Conversation.query.filter_by(
            project_id=project_id,
            agent_id=agent_id
        ).first()
        if conv:
            conv.messages = []
            db.session.commit()
            return True
        return False
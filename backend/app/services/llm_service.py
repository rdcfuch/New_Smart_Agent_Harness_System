import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)


# Tool definitions for the LLM (using input_schema for Anthropic API)
TOOLS = [
    {
        "name": "write_file",
        "description": "Write content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Read content from a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "bash",
        "description": "Execute a bash command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"},
                "cwd": {"type": "string", "description": "Working directory (optional)"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "search",
        "description": "Search the web using Serper API",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results (default 10)"}
            },
            "required": ["query"]
        }
    }
]


class LLMService:
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
        api_key = os.getenv("ANTHROPIC_API_KEY")
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        model_id = os.getenv("MODEL_ID", "MiniMax-M2.7")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")

        # Remove auth token if base_url is set (they use different auth)
        if base_url:
            os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

        self.client = Anthropic(base_url=base_url) if base_url else Anthropic()
        self.model_id = model_id
        print(f"LLMService initialized with model: {self.model_id}, base_url: {base_url}")

    def chat(self, system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
        """Send a chat message and return the response."""
        try:
            response = self.client.messages.create(
                model=self.model_id,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
            )
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text':
                    return block.text
            return str(response.content)
        except Exception as e:
            return f"Error: {str(e)}"

    def chat_with_tools(self, system_prompt: str, messages: list, tools: list = None, max_tokens: int = 4096) -> dict:
        """
        Send a chat message with tool calling capability.
        Returns dict with:
        - 'text': final text response (if stop_reason != 'tool_use')
        - 'tool_calls': list of (name, input) tuples if LLM wants to use tools
        """
        if tools is None:
            tools = TOOLS

        try:
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

            response = self.client.messages.create(
                model=self.model_id,
                system=system_prompt,
                messages=formatted_messages,
                tools=tools,
                max_tokens=max_tokens,
            )

            if response.stop_reason == "tool_use":
                tool_calls = []
                for block in response.content:
                    if hasattr(block, 'type') and block.type == 'tool_use':
                        tool_calls.append({
                            "name": block.name,
                            "input": block.input
                        })
                return {"tool_calls": tool_calls}
            else:
                # Return text response
                for block in response.content:
                    if hasattr(block, 'type') and block.type == 'text':
                        return {"text": block.text}
                return {"text": str(response.content)}
        except Exception as e:
            return {"text": f"Error: {str(e)}"}

    def chat_with_context(self, system_prompt: str, messages: list, max_tokens: int = 4096) -> str:
        """Send a chat message with conversation history."""
        try:
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

            response = self.client.messages.create(
                model=self.model_id,
                system=system_prompt,
                messages=formatted_messages,
                max_tokens=max_tokens,
            )
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text':
                    return block.text
            return str(response.content)
        except Exception as e:
            return f"Error: {str(e)}"


def get_llm_service() -> LLMService:
    return LLMService.get_instance()


def get_tool_registry():
    from app.services.tool_registry import ToolRegistry
    return ToolRegistry()
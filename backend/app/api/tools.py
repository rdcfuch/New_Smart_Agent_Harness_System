from flask import Blueprint, request, jsonify

bp = Blueprint("tools", __name__, url_prefix="/api/tools")


@bp.route("/execute", methods=["POST"])
def execute_tool():
    """
    Execute a tool on behalf of an agent.
    Only TASK_EXECUTOR and ORCHESTRATOR agents can execute tools.
    """
    from app.services.agent_tool_service import get_agent_tool_service

    data = request.json
    agent_id = data.get("agent_id")
    tool_name = data.get("tool")
    params = data.get("params", {})

    if not all([agent_id, tool_name]):
        return jsonify({"error": "agent_id and tool are required"}), 400

    service = get_agent_tool_service()
    result = service.execute_tool(agent_id, tool_name, params)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


@bp.route("/list", methods=["GET"])
def list_tools():
    """List all available tools."""
    from app.services.agent_tool_service import get_agent_tool_service

    agent_id = request.args.get("agent_id")
    service = get_agent_tool_service()
    tools = service.get_available_tools(agent_id)

    return jsonify({"tools": tools})


@bp.route("/bash", methods=["POST"])
def tool_bash():
    """Direct bash execution via tool registry."""
    from app.services.tool_registry import get_tool_registry

    data = request.json
    command = data.get("command", "")
    cwd = data.get("cwd")
    timeout = data.get("timeout", 120)

    registry = get_tool_registry()
    result = registry.execute("bash", command=command, cwd=cwd, timeout=timeout)

    return jsonify(result.to_dict())


@bp.route("/read", methods=["POST"])
def tool_read():
    """Direct file read via tool registry."""
    from app.services.tool_registry import get_tool_registry

    data = request.json
    path = data.get("path")
    limit = data.get("limit")

    if not path:
        return jsonify({"error": "path is required"}), 400

    registry = get_tool_registry()
    result = registry.execute("read_file", path=path, limit=limit)

    return jsonify(result.to_dict())


@bp.route("/write", methods=["POST"])
def tool_write():
    """Direct file write via tool registry."""
    from app.services.tool_registry import get_tool_registry

    data = request.json
    path = data.get("path")
    content = data.get("content", "")

    if not path:
        return jsonify({"error": "path is required"}), 400

    registry = get_tool_registry()
    result = registry.execute("write_file", path=path, content=content)

    return jsonify(result.to_dict())


@bp.route("/edit", methods=["POST"])
def tool_edit():
    """Direct file edit via tool registry."""
    from app.services.tool_registry import get_tool_registry

    data = request.json
    path = data.get("path")
    old_text = data.get("old_text")
    new_text = data.get("new_text")

    if not all([path, old_text, new_text]):
        return jsonify({"error": "path, old_text, and new_text are required"}), 400

    registry = get_tool_registry()
    result = registry.execute("edit_file", path=path, old_text=old_text, new_text=new_text)

    return jsonify(result.to_dict())


@bp.route("/search", methods=["POST"])
def tool_search():
    """Web search via Serper API."""
    from app.services.tool_registry import get_tool_registry

    data = request.json
    query = data.get("query")
    num_results = data.get("num_results", 10)

    if not query:
        return jsonify({"error": "query is required"}), 400

    registry = get_tool_registry()
    result = registry.execute("search", query=query, num_results=num_results)

    return jsonify(result.to_dict())
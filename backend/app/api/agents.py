from flask import Blueprint, request, jsonify

bp = Blueprint("agents", __name__, url_prefix="/api/agents")


@bp.route("", methods=["GET"])
def list_agents():
    from app.services import AgentRegistry

    registry = AgentRegistry.get_instance()
    agent_type = request.args.get("type")
    status = request.args.get("status")

    agents = registry.list_all(agent_type=agent_type, status=status)
    return jsonify({"agents": [a.to_dict() for a in agents]})


@bp.route("", methods=["POST"])
def create_agent():
    from app.services import AgentRegistry, EventBusService

    data = request.json
    registry = AgentRegistry.get_instance()
    event_bus = EventBusService.get_instance()

    try:
        agent = registry.create(
            name=data.get("name"),
            agent_type=data.get("agent_type"),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            resource_access=data.get("resource_access", []),
            permission_level=data.get("permission_level", "RESTRICTED"),
            memory_focus=data.get("memory_focus", ""),
            special_attributes=data.get("special_attributes", {}),
            parent_id=data.get("parent_id"),
            project_id=data.get("project_id"),
        )

        event_bus.emit_agent_registered(agent.id, agent.agent_type, agent.name)

        return jsonify({"agent": agent.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    from app.services import AgentRegistry

    registry = AgentRegistry.get_instance()
    agent = registry.get(agent_id)

    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    return jsonify({"agent": agent.to_dict()})


@bp.route("/<agent_id>", methods=["PATCH"])
def update_agent(agent_id):
    from app.services import AgentRegistry

    registry = AgentRegistry.get_instance()
    data = request.json

    try:
        if "status" in data:
            agent = registry.update_status(agent_id, data["status"])
        else:
            agent = registry.update(agent_id, **data)

        if not agent:
            return jsonify({"error": "Agent not found"}), 404

        return jsonify({"agent": agent.to_dict()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id):
    from app.services import AgentRegistry

    registry = AgentRegistry.get_instance()
    success = registry.terminate(agent_id)

    if not success:
        return jsonify({"error": "Agent not found"}), 404

    return jsonify({"status": "terminated", "agent_id": agent_id})


@bp.route("/<agent_id>/heartbeat", methods=["POST"])
def heartbeat(agent_id):
    from app.services import AgentRegistry

    registry = AgentRegistry.get_instance()
    success = registry.heartbeat(agent_id)

    if not success:
        return jsonify({"error": "Agent not found"}), 404

    return jsonify({"status": "ok"})


@bp.route("/active", methods=["GET"])
def list_active():
    from app.services import AgentRegistry

    registry = AgentRegistry.get_instance()
    agents = registry.list_active()
    return jsonify({"agents": [a.to_dict() for a in agents]})
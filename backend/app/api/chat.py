from flask import Blueprint, request, jsonify

bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@bp.route("/send", methods=["POST"])
def send_message():
    """
    Send a message to an orchestrator agent in a project.
    Only ORCHESTRATOR agents can receive direct user messages.
    """
    from app.services.chat_service import ChatService

    data = request.json
    project_id = data.get("project_id")
    agent_id = data.get("agent_id")
    message = data.get("message")

    if not all([project_id, agent_id, message]):
        return jsonify({"error": "project_id, agent_id, and message are required"}), 400

    chat_service = ChatService.get_instance()
    result = chat_service.send_message(project_id, agent_id, message)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


@bp.route("/history/<project_id>/<agent_id>", methods=["GET"])
def get_history(project_id, agent_id):
    """Get conversation history for a project + agent."""
    from app.services.chat_service import ChatService

    chat_service = ChatService.get_instance()
    messages = chat_service.get_conversation_history(project_id, agent_id)
    return jsonify({"messages": messages})


@bp.route("/clear/<project_id>/<agent_id>", methods=["POST"])
def clear_history(project_id, agent_id):
    """Clear conversation history."""
    from app.services.chat_service import ChatService

    chat_service = ChatService.get_instance()
    success = chat_service.clear_conversation(project_id, agent_id)
    return jsonify({"success": success})


@bp.route("/conversations/<project_id>", methods=["GET"])
def list_conversations(project_id):
    """List all conversations for a project."""
    from app.models import Conversation

    convs = Conversation.query.filter_by(project_id=project_id).all()
    return jsonify({"conversations": [c.to_dict() for c in convs]})
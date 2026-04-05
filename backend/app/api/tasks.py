from flask import Blueprint, request, jsonify

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@bp.route("", methods=["GET"])
def list_tasks():
    from app.services import TaskManagerService

    manager = TaskManagerService.get_instance()
    status = request.args.get("status")
    owner = request.args.get("owner")
    priority = request.args.get("priority", type=int)

    tasks = manager.list_all(status=status, owner=owner, priority=priority)
    return jsonify({"tasks": [t.to_dict() for t in tasks]})


@bp.route("", methods=["POST"])
def create_task():
    from app.services import TaskManagerService, EventBusService

    data = request.json
    manager = TaskManagerService.get_instance()
    event_bus = EventBusService.get_instance()

    try:
        task = manager.create(
            subject=data.get("subject"),
            description=data.get("description", ""),
            priority=data.get("priority", 2),
            owner=data.get("owner"),
            blocked_by=data.get("blocked_by", []),
        )

        event_bus.emit_task_created(task.id, task.subject)

        return jsonify({"task": task.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<task_id>", methods=["GET"])
def get_task(task_id):
    from app.services import TaskManagerService

    manager = TaskManagerService.get_instance()
    task = manager.get(task_id=task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"task": task.to_dict()})


@bp.route("/<task_id>", methods=["PATCH"])
def update_task(task_id):
    from app.services import TaskManagerService

    manager = TaskManagerService.get_instance()
    data = request.json

    try:
        if "status" in data:
            task = manager.update_status(task_id, data["status"])
        elif "agent_id" in data:
            task = manager.assign_agent(task_id, data["agent_id"])
        else:
            return jsonify({"error": "Invalid update"}), 400

        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"task": task.to_dict()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<task_id>/complete", methods=["POST"])
def complete_task(task_id):
    from app.services import TaskManagerService

    data = request.json or {}
    manager = TaskManagerService.get_instance()

    try:
        task = manager.complete(
            task_id,
            result=data.get("result"),
            error=data.get("error"),
        )

        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"task": task.to_dict()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    from app.services import TaskManagerService

    manager = TaskManagerService.get_instance()
    success = manager.delete(task_id)

    if not success:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"status": "deleted", "task_id": task_id})


@bp.route("/by-number/<int:task_number>", methods=["GET"])
def get_task_by_number(task_number):
    from app.services import TaskManagerService

    manager = TaskManagerService.get_instance()
    task = manager.get(task_number=task_number)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"task": task.to_dict()})
from flask import Blueprint, request, jsonify

bp = Blueprint("worktrees", __name__, url_prefix="/api/worktrees")


@bp.route("", methods=["GET"])
def list_worktrees():
    from app.services import WorktreeManagerService

    manager = WorktreeManagerService.get_instance()
    status = request.args.get("status")

    worktrees = manager.list_all(status=status)
    return jsonify({"worktrees": [w.to_dict() for w in worktrees]})


@bp.route("", methods=["POST"])
def create_worktree():
    from app.services import WorktreeManagerService, EventBusService

    data = request.json
    manager = WorktreeManagerService.get_instance()
    event_bus = EventBusService.get_instance()

    try:
        worktree = manager.create(
            name=data.get("name"),
            task_id=data.get("task_id"),
            agent_id=data.get("agent_id"),
            base_ref=data.get("base_ref", "HEAD"),
        )

        event_bus.emit_worktree_created(worktree.name, worktree.path, worktree.task_id)

        return jsonify({"worktree": worktree.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<name>", methods=["GET"])
def get_worktree(name):
    from app.services import WorktreeManagerService

    manager = WorktreeManagerService.get_instance()
    worktree = manager.get(name=name)

    if not worktree:
        return jsonify({"error": "Worktree not found"}), 404

    return jsonify({"worktree": worktree.to_dict()})


@bp.route("/<name>/status", methods=["GET"])
def worktree_status(name):
    from app.services import WorktreeManagerService

    manager = WorktreeManagerService.get_instance()
    status = manager.status(name)

    return jsonify(status)


@bp.route("/<name>/run", methods=["POST"])
def run_command(name):
    from app.services import WorktreeManagerService

    data = request.json
    manager = WorktreeManagerService.get_instance()

    if not data.get("command"):
        return jsonify({"error": "command is required"}), 400

    result = manager.run(
        name,
        data["command"],
        timeout=data.get("timeout", 300),
    )

    return jsonify(result)


@bp.route("/<name>/keep", methods=["POST"])
def keep_worktree(name):
    from app.services import WorktreeManagerService, EventBusService

    manager = WorktreeManagerService.get_instance()
    event_bus = EventBusService.get_instance()

    worktree = manager.keep(name)
    if not worktree:
        return jsonify({"error": "Worktree not found"}), 404

    return jsonify({"worktree": worktree.to_dict()})


@bp.route("/<name>", methods=["DELETE"])
def remove_worktree(name):
    from app.services import WorktreeManagerService, EventBusService

    data = request.json or {}
    manager = WorktreeManagerService.get_instance()
    event_bus = EventBusService.get_instance()

    result = manager.remove(
        name,
        force=data.get("force", False),
        complete_task=data.get("complete_task", False),
    )

    if "error" in result:
        return jsonify(result), 400

    event_bus.emit_worktree_removed(name)

    return jsonify({"status": "removed", "name": name})
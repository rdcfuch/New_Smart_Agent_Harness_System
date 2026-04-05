from flask import Blueprint, request, jsonify

bp = Blueprint("orchestrator", __name__, url_prefix="/api/orchestrator")


@bp.route("/delegate", methods=["POST"])
def delegate_task():
    from app.services import OrchestratorService

    data = request.json
    orchestrator_id = data.get("orchestrator_id")
    task_id = data.get("task_id")
    executor_type = data.get("executor_type", "TASK_EXECUTOR")
    instructions = data.get("instructions")

    orchestrator = OrchestratorService.get_instance()

    if not orchestrator_id:
        return jsonify({"error": "orchestrator_id is required"}), 400

    try:
        result = orchestrator.delegate_task(
            orchestrator_id=orchestrator_id,
            task_id=task_id,
            executor_type=executor_type,
            instructions=instructions,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/workers", methods=["GET"])
def list_workers():
    from app.services import OrchestratorService

    orchestrator = OrchestratorService.get_instance()
    workers = orchestrator.list_active_workers()

    return jsonify({"workers": workers})


@bp.route("/workers/<worker_id>/status", methods=["GET"])
def worker_status(worker_id):
    from app.services import OrchestratorService

    orchestrator = OrchestratorService.get_instance()
    status = orchestrator.get_worker_status(worker_id)

    return jsonify(status)


@bp.route("/workers/<worker_id>/halt", methods=["POST"])
def halt_worker(worker_id):
    from app.services import OrchestratorService

    data = request.json or {}
    orchestrator = OrchestratorService.get_instance()

    result = orchestrator.halt_worker(worker_id, reason=data.get("reason"))

    return jsonify(result)


@bp.route("/workers/<worker_id>/resume", methods=["POST"])
def resume_worker(worker_id):
    from app.services import OrchestratorService

    data = request.json or {}
    orchestrator = OrchestratorService.get_instance()

    result = orchestrator.resume_worker(worker_id, instructions=data.get("instructions"))

    return jsonify(result)


@bp.route("/tasks/<task_id>/complete", methods=["POST"])
def complete_task(task_id):
    from app.services import OrchestratorService

    data = request.json or {}
    orchestrator = OrchestratorService.get_instance()

    result = orchestrator.complete_task(task_id, result=data.get("result"))

    return jsonify(result)


@bp.route("/orchestrator", methods=["POST"])
def get_or_create_orchestrator():
    from app.services import OrchestratorService

    data = request.json or {}
    project_id = data.get("project_id")

    orchestrator = OrchestratorService.get_instance()
    agent = orchestrator.get_or_create_orchestrator(project_id=project_id)

    return jsonify({"orchestrator": agent.to_dict()})
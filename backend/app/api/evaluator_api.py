from flask import Blueprint, request, jsonify

bp = Blueprint("evaluator_api", __name__, url_prefix="/api/evaluator")


@bp.route("/evaluate", methods=["POST"])
def evaluate_task():
    from app.services import EvaluatorService

    data = request.json
    evaluator = EvaluatorService.get_instance()

    result = evaluator.evaluate(
        task_id=data.get("task_id"),
        output=data.get("output"),
        context=data.get("context"),
        risk_level=data.get("risk_level", 0.0),
    )

    return jsonify(result)


@bp.route("/consensus", methods=["POST"])
def evaluate_with_consensus():
    from app.services import EvaluatorService

    data = request.json
    evaluator = EvaluatorService.get_instance()

    result = evaluator.evaluate_with_consensus(
        task_id=data.get("task_id"),
        output=data.get("output"),
        models=data.get("models"),
    )

    return jsonify(result)


@bp.route("/threshold", methods=["POST"])
def set_threshold():
    from app.services import EvaluatorService

    data = request.json
    evaluator = EvaluatorService.get_instance()

    evaluator.set_threshold(
        key=data.get("key"),
        value=data.get("value"),
    )

    return jsonify({"status": "ok"})
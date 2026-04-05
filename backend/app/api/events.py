from flask import Blueprint, request, jsonify

bp = Blueprint("events", __name__, url_prefix="/api/events")


@bp.route("", methods=["GET"])
def list_events():
    from app.services import EventBusService

    event_bus = EventBusService.get_instance()
    limit = request.args.get("limit", 50, type=int)
    event_type = request.args.get("type")

    events = event_bus.list_recent(limit=limit, event_type=event_type)
    return jsonify({"events": events})


@bp.route("/trace/<trace_id>", methods=["GET"])
def get_events_by_trace(trace_id):
    from app.services import EventBusService

    event_bus = EventBusService.get_instance()
    events = event_bus.get_by_trace(trace_id)

    return jsonify({"events": [e.to_dict() for e in events]})


@bp.route("", methods=["POST"])
def emit_event():
    from app.services import EventBusService

    data = request.json
    event_bus = EventBusService.get_instance()

    event = event_bus.emit(
        event_type=data.get("event_type"),
        sender_id=data.get("sender_id"),
        receiver_id=data.get("receiver_id"),
        payload=data.get("payload", {}),
        error=data.get("error"),
        trace_id=data.get("trace_id"),
        priority=data.get("priority", 5),
    )

    return jsonify({"event": event.to_dict()}), 201
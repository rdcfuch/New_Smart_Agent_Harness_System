from flask_socketio import SocketIO, emit

from app import socketio


@socketio.on("connect", namespace="/ws/events")
def handle_connect():
    print("Client connected to events namespace")
    emit("connected", {"status": "ok"})


@socketio.on("disconnect", namespace="/ws/events")
def handle_disconnect():
    print("Client disconnected from events namespace")


@socketio.on("subscribe", namespace="/ws/events")
def handle_subscribe(data):
    event_types = data.get("event_types", [])
    print(f"Subscribing to event types: {event_types}")
    emit("subscribed", {"event_types": event_types})
import os
from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5555))

    print(f"Starting Agent Harness Backend on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
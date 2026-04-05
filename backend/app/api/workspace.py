from flask import Blueprint, request, jsonify
import os
from pathlib import Path

bp = Blueprint("workspace", __name__, url_prefix="/api/workspace")

WORKDIR = Path(os.getenv("WORKTREE_BASE_PATH", "/Users/jackyfox/New_Smart_Agent_Harness_System"))


def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not str(path).startswith(str(WORKDIR)):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


@bp.route("/read", methods=["GET"])
def read_file():
    file_path = request.args.get("path")
    limit = request.args.get("limit", type=int)

    if not file_path:
        return jsonify({"error": "path is required"}), 400

    try:
        fp = safe_path(file_path)
        lines = fp.read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        return jsonify({"content": "\n".join(lines)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/write", methods=["POST"])
def write_file():
    data = request.json
    file_path = data.get("path")
    content = data.get("content", "")

    if not file_path:
        return jsonify({"error": "path is required"}), 400

    try:
        fp = safe_path(file_path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return jsonify({"status": "ok", "bytes": len(content)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/edit", methods=["POST"])
def edit_file():
    data = request.json
    file_path = data.get("path")
    old_text = data.get("old_text")
    new_text = data.get("new_text")

    if not all([file_path, old_text, new_text]):
        return jsonify({"error": "path, old_text, and new_text are required"}), 400

    try:
        fp = safe_path(file_path)
        content = fp.read_text()
        if old_text not in content:
            return jsonify({"error": "Text not found in file"}), 400
        fp.write_text(content.replace(old_text, new_text, 1))
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/bash", methods=["POST"])
def run_bash():
    from app.services import EventBusService

    data = request.json
    command = data.get("command", "")
    cwd = data.get("cwd", str(WORKDIR))

    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return jsonify({"error": "Dangerous command blocked"}), 400

    import subprocess

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return jsonify({
            "stdout": result.stdout[:50000],
            "stderr": result.stderr[:50000],
            "returncode": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout (120s)"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400
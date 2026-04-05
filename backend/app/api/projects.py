from flask import Blueprint, request, jsonify

bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@bp.route("", methods=["GET"])
def list_projects():
    from app.models import Project
    projects = Project.query.all()
    return jsonify({"projects": [p.to_dict() for p in projects]})


@bp.route("", methods=["POST"])
def create_project():
    from app.models import Project
    from app import db
    from pathlib import Path

    data = request.json
    project_name = data.get("name", "")

    # Default paths based on project name
    base_path = Path("/Users/jackyfox/New_Smart_Agent_Harness_System/backend/ProjectSandbox")
    sandbox_path = data.get("sandbox_path") or str(base_path / project_name / "sandbox")
    memory_path = data.get("memory_path") or str(base_path / project_name / ".memory")

    try:
        # Create project directories
        Path(sandbox_path).mkdir(parents=True, exist_ok=True)
        Path(memory_path).mkdir(parents=True, exist_ok=True)

        project = Project(
            name=project_name,
            description=data.get("description", ""),
            sandbox_path=sandbox_path,
            context=data.get("context", ""),
            memory_path=memory_path,
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({"project": project.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<project_id>", methods=["GET"])
def get_project(project_id):
    from app.models import Project
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"project": project.to_dict()})


@bp.route("/<project_id>", methods=["PATCH"])
def update_project(project_id):
    from app.models import Project
    from app import db

    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    data = request.json
    for key in ["name", "description", "sandbox_path", "context", "memory_path"]:
        if key in data:
            setattr(project, key, data[key])
    db.session.commit()
    return jsonify({"project": project.to_dict()})


@bp.route("/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    from app.models import Project, Agent, Task, Conversation
    from app import db

    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    # Delete in correct order: conversations (refs agents), then agents, then tasks
    Conversation.query.filter_by(project_id=project_id).delete()
    Agent.query.filter_by(project_id=project_id).delete()
    Task.query.filter_by(project_id=project_id).delete()
    db.session.delete(project)
    db.session.commit()
    return jsonify({"status": "deleted"})


@bp.route("/<project_id>/agents", methods=["GET"])
def project_agents(project_id):
    from app.models import Project, Agent
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    agents = Agent.query.filter_by(project_id=project_id).all()
    return jsonify({"agents": [a.to_dict() for a in agents]})


@bp.route("/<project_id>/tasks", methods=["GET"])
def project_tasks(project_id):
    from app.models import Project, Task
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    tasks = Task.query.filter_by(project_id=project_id).all()
    return jsonify({"tasks": [t.to_dict() for t in tasks]})


@bp.route("/<project_id>/files", methods=["GET"])
def project_files(project_id):
    """List files in project's sandbox directory."""
    import os
    from app.models import Project
    from pathlib import Path

    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    base_path = Path(project.sandbox_path) if project.sandbox_path else None
    if not base_path or not base_path.exists():
        return jsonify({"files": [], "path": str(base_path) if base_path else None})

    files = []
    try:
        for item in sorted(base_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
            rel_path = item.relative_to(base_path)
            files.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else None
            })
    except Exception as e:
        return jsonify({"error": str(e), "files": []}), 400

    return jsonify({"files": files, "path": str(base_path)})
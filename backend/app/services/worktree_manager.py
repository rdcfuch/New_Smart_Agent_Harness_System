import os
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

from app import db
from app.models import Worktree, WorktreeStatus, Task, TaskStatus
from app.config import Config


class WorktreeManagerService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.base_path = Path(Config.WORKTREE_BASE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.git_available = self._check_git()

    def _check_git(self) -> bool:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_git(self, args: list, cwd: Path = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            timeout=Config.WORKTREE_GIT_TIMEOUT,
        )

    def _validate_name(self, name: str):
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,40}", name or ""):
            raise ValueError(
                "Invalid worktree name. Use 1-40 chars: letters, numbers, ., _, -"
            )

    def create(
        self,
        name: str,
        task_id: str = None,
        agent_id: str = None,
        base_ref: str = "HEAD",
    ) -> Worktree:
        self._validate_name(name)

        existing = Worktree.query.filter_by(name=name).first()
        if existing and existing.status != WorktreeStatus.REMOVED.value:
            raise ValueError(f"Worktree '{name}' already exists")

        if task_id:
            task = db.session.get(Task, task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

        path = self.base_path / name

        if self.git_available:
            branch = f"wt/{name}"
            result = self._run_git(
                ["worktree", "add", "-b", branch, str(path), base_ref]
            )
            if result.returncode != 0:
                raise RuntimeError(f"Git worktree creation failed: {result.stderr}")

        worktree = Worktree(
            id=str(Path(path).resolve().as_posix().split("/")[-1])
            if not self.git_available
            else str(name),
            name=name,
            path=str(path),
            branch=f"wt/{name}" if self.git_available else "",
            base_ref=base_ref,
            status=WorktreeStatus.ACTIVE.value,
            task_id=task_id,
            agent_id=agent_id,
        )

        db.session.add(worktree)

        if task_id:
            task = db.session.get(Task, task_id)
            if task and task.status == TaskStatus.PENDING.value:
                task.status = TaskStatus.IN_PROGRESS.value
                task.started_at = datetime.utcnow()

        db.session.commit()
        return worktree

    def get(self, name: str = None, worktree_id: str = None) -> Optional[Worktree]:
        if name:
            return Worktree.query.filter_by(name=name).first()
        if worktree_id:
            return db.session.get(Worktree, worktree_id)
        return None

    def list_all(self, status: str = None) -> list[Worktree]:
        query = Worktree.query
        if status:
            query = query.filter(Worktree.status == status)
        return query.all()

    def status(self, name: str) -> dict:
        worktree = self.get(name=name)
        if not worktree:
            return {"error": f"Unknown worktree '{name}'"}

        path = Path(worktree.path)
        if not path.exists():
            return {"error": f"Worktree path missing: {path}"}

        if self.git_available:
            result = self._run_git(["status", "--short", "--branch"], cwd=path)
            return {
                "name": name,
                "status": worktree.status,
                "git_status": result.stdout.strip() or "Clean",
                "branch": worktree.branch,
            }

        return {
            "name": name,
            "status": worktree.status,
            "path": str(path),
        }

    def run(self, name: str, command: str, timeout: int = 300) -> dict:
        dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
        if any(d in command for d in dangerous):
            return {"error": "Dangerous command blocked"}

        worktree = self.get(name=name)
        if not worktree:
            return {"error": f"Unknown worktree '{name}'"}

        path = Path(worktree.path)
        if not path.exists():
            return {"error": f"Worktree path missing: {path}"}

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout[:50000],
                "stderr": result.stderr[:50000],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Timeout ({timeout}s)"}

    def keep(self, name: str) -> Optional[Worktree]:
        worktree = self.get(name=name)
        if not worktree:
            return None
        worktree.status = WorktreeStatus.KEPT.value
        worktree.kept_at = datetime.utcnow()
        db.session.commit()
        return worktree

    def remove(
        self, name: str, force: bool = False, complete_task: bool = False
    ) -> dict:
        worktree = self.get(name=name)
        if not worktree:
            return {"error": f"Unknown worktree '{name}'"}

        if self.git_available:
            args = ["worktree", "remove"]
            if force:
                args.append("--force")
            args.append(worktree.path)
            result = self._run_git(args)
            if result.returncode != 0:
                return {"error": f"Git worktree remove failed: {result.stderr}"}

        if complete_task and worktree.task_id:
            task = db.session.get(Task, worktree.task_id)
            if task:
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.utcnow()

        worktree.status = WorktreeStatus.REMOVED.value
        worktree.removed_at = datetime.utcnow()

        db.session.commit()
        return {"success": True, "name": name}
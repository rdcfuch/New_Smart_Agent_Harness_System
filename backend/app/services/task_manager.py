import uuid
from datetime import datetime
from typing import Optional
from app import db
from app.models import Task, TaskStatus, TaskPriority


class TaskManagerService:
    _instance = None
    _next_task_number = 1

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._init_task_number()
        return cls._instance

    def _init_task_number(self):
        last_task = (
            db.session.query(Task).order_by(Task.task_number.desc()).first()
        )
        if last_task:
            self._next_task_number = last_task.task_number + 1

    def create(
        self,
        subject: str,
        description: str = "",
        priority: int = TaskPriority.NORMAL.value,
        owner: str = None,
        blocked_by: list = None,
    ) -> Task:
        task = Task(
            id=str(uuid.uuid4()),
            task_number=self._next_task_number,
            subject=subject,
            description=description,
            priority=priority,
            owner=owner,
            blocked_by=blocked_by or [],
            status=TaskStatus.PENDING.value,
        )
        self._next_task_number += 1
        db.session.add(task)
        db.session.commit()
        return task

    def get(self, task_id: str = None, task_number: int = None) -> Optional[Task]:
        if task_id:
            return db.session.get(Task, task_id)
        if task_number:
            return Task.query.filter_by(task_number=task_number).first()
        return None

    def list_all(
        self,
        status: str = None,
        owner: str = None,
        priority: int = None,
    ) -> list[Task]:
        query = Task.query
        if status:
            query = query.filter(Task.status == status)
        if owner:
            query = query.filter(Task.owner == owner)
        if priority:
            query = query.filter(Task.priority == priority)
        return query.order_by(Task.priority.desc(), Task.created_at.asc()).all()

    def update_status(self, task_id: str, status: str) -> Optional[Task]:
        task = self.get(task_id)
        if not task:
            return None

        task.status = status
        if status == TaskStatus.IN_PROGRESS.value:
            task.started_at = datetime.utcnow()
        elif status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            task.completed_at = datetime.utcnow()

        db.session.commit()
        return task

    def assign_agent(self, task_id: str, agent_id: str) -> Optional[Task]:
        task = self.get(task_id)
        if task:
            task.agent_id = agent_id
            task.status = TaskStatus.IN_PROGRESS.value
            task.started_at = datetime.utcnow()
            db.session.commit()
        return task

    def bind_worktree(self, task_id: str, worktree_name: str) -> Optional[Task]:
        task = self.get(task_id)
        if task:
            task.worktree_name = worktree_name
            db.session.commit()
        return task

    def unbind_worktree(self, task_id: str) -> Optional[Task]:
        task = self.get(task_id)
        if task:
            task.worktree_name = None
            db.session.commit()
        return task

    def complete(
        self, task_id: str, result: str = None, error: str = None
    ) -> Optional[Task]:
        task = self.get(task_id)
        if not task:
            return None
        task.status = (
            TaskStatus.FAILED.value if error else TaskStatus.COMPLETED.value
        )
        task.result = result
        task.error_message = error
        task.completed_at = datetime.utcnow()
        if task.worktree_name:
            task.worktree_name = None
        db.session.commit()
        return task

    def is_blocked(self, task_id: str) -> bool:
        task = self.get(task_id)
        if not task or not task.blocked_by:
            return False
        for blocked_id in task.blocked_by:
            blocked_task = self.get(task_id=blocked_id)
            if blocked_task and blocked_task.status != TaskStatus.COMPLETED.value:
                return True
        return False

    def delete(self, task_id: str) -> bool:
        task = self.get(task_id)
        if task:
            db.session.delete(task)
            db.session.commit()
            return True
        return False
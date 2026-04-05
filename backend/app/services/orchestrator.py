import uuid
import time
from typing import Optional

from app import db
from app.models import Agent, AgentType, AgentStatus, Task, TaskStatus
from app.services.agent_registry import AgentRegistry
from app.services.task_manager import TaskManagerService
from app.services.worktree_manager import WorktreeManagerService
from app.services.event_bus import EventBusService
from app.protocol import AgentEnvelope, Intent, CognitiveContext


class OrchestratorService:
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
        self.registry = AgentRegistry.get_instance()
        self.task_manager = TaskManagerService.get_instance()
        self.worktree_manager = WorktreeManagerService.get_instance()
        self.event_bus = EventBusService.get_instance()
        self.active_workers = {}

    def get_or_create_orchestrator(self, project_id: str = None) -> Agent:
        orchestrators = self.registry.find_by_type_and_project(
            AgentType.ORCHESTRATOR.value, project_id
        )
        if orchestrators:
            return orchestrators[0]

        return self.registry.create(
            name="orchestrator",
            agent_type=AgentType.ORCHESTRATOR.value,
            description="Main orchestrator for task coordination",
            system_prompt="You are the system orchestrator. You coordinate task execution through worker agents.",
            resource_access=["Agent_Registry", "Shared_State_Store"],
            permission_level="ADMIN",
            memory_focus="Collective_Memory",
            special_attributes={"max_concurrency": 10},
            project_id=project_id,
        )

    def delegate_task(
        self,
        orchestrator_id: str,
        task_id: str,
        executor_type: str = AgentType.TASK_EXECUTOR.value,
        instructions: str = None,
    ) -> dict:
        task = self.task_manager.get(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}

        worktree_name = f"task-{task.task_number}"
        worktree = self.worktree_manager.create(
            name=worktree_name,
            task_id=task_id,
            base_ref="HEAD",
        )

        executor = self.registry.create(
            name=f"executor-{task.task_number}",
            agent_type=executor_type,
            description=f"Task executor for task #{task.task_number}",
            system_prompt=instructions or f"Execute task: {task.subject}",
            resource_access=["MCP_Tools", "Local_Sandbox"],
            permission_level="RESTRICTED",
            memory_focus="Short_Term_Episodic",
            special_attributes={"sandboxed": True},
            parent_id=orchestrator_id,
            project_id=task.project_id if hasattr(task, "project_id") else None,
        )

        self.task_manager.assign_agent(task_id, executor.id)

        self.active_workers[executor.id] = {
            "task_id": task_id,
            "worktree_name": worktree_name,
            "start_time": time.time(),
        }

        self.event_bus.emit(
            event_type="task.delegated",
            sender_id=orchestrator_id,
            receiver_id=executor.id,
            payload={
                "task_id": task_id,
                "executor_id": executor.id,
                "worktree_name": worktree_name,
            },
        )

        return {
            "executor_id": executor.id,
            "worktree_name": worktree_name,
            "task_id": task_id,
        }

    def resume_worker(self, worker_id: str, instructions: str) -> dict:
        worker = self.registry.get(worker_id)
        if not worker:
            return {"error": f"Worker {worker_id} not found"}

        return {
            "status": "resumed",
            "worker_id": worker_id,
            "instructions": instructions,
        }

    def halt_worker(self, worker_id: str, reason: str = None) -> dict:
        worker = self.registry.get(worker_id)
        if not worker:
            return {"error": f"Worker {worker_id} not found"}

        if worker_id in self.active_workers:
            del self.active_workers[worker_id]

        self.registry.update_status(worker_id, AgentStatus.SUSPENDED.value)

        self.event_bus.emit(
            event_type="worker.halted",
            sender_id=worker_id,
            payload={"reason": reason, "worker_id": worker_id},
        )

        return {"status": "halted", "worker_id": worker_id}

    def get_worker_status(self, worker_id: str) -> dict:
        worker = self.registry.get(worker_id)
        if not worker:
            return {"error": f"Worker {worker_id} not found"}

        worker_info = self.active_workers.get(worker_id, {})
        return {
            "worker_id": worker_id,
            "status": worker.status,
            "task_id": worker_info.get("task_id"),
            "uptime": time.time() - worker_info.get("start_time", 0),
        }

    def list_active_workers(self) -> list[dict]:
        return [
            {
                "worker_id": wid,
                "task_id": info.get("task_id"),
                "uptime": time.time() - info.get("start_time", 0),
            }
            for wid, info in self.active_workers.items()
        ]

    def complete_task(self, task_id: str, result: str = None) -> dict:
        task = self.task_manager.complete(task_id, result=result)
        if not task:
            return {"error": f"Task {task_id} not found"}

        if task.agent_id and task.agent_id in self.active_workers:
            del self.active_workers[task.agent_id]

        self.registry.update_status(task.agent_id, AgentStatus.IDLE.value)

        self.event_bus.emit_task_completed(task_id)

        return {"status": "completed", "task_id": task_id, "result": result}
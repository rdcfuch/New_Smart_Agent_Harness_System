import uuid
from typing import Optional

from app import db
from app.models import Task, TaskStatus, Agent, AgentType
from app.services.agent_registry import AgentRegistry
from app.services.task_manager import TaskManagerService
from app.services.event_bus import EventBusService


class EvaluationResult:
    PASS = "PASS"
    REJECT = "REJECT"
    NEEDS_REVISION = "NEEDS_REVISION"


class EvaluatorService:
    _instance = None
    _rejection_counts = {}

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
        self.event_bus = EventBusService.get_instance()
        self._thresholds = {
            "risk_tolerance": 0.7,
            "quality_score_min": 0.8,
        }

    def create_evaluator(
        self, name: str = "evaluator", project_id: str = None
    ) -> Agent:
        evaluators = self.registry.find_by_type_and_project(
            AgentType.EVALUATOR.value, project_id
        )
        if evaluators:
            return evaluators[0]

        return self.registry.create(
            name=name,
            agent_type=AgentType.EVALUATOR.value,
            description="Quality audit and alignment evaluator",
            system_prompt="You are a quality auditor. You evaluate task outputs for correctness, safety, and completeness.",
            resource_access=["Verification_Logs", "Constraints_Schema"],
            permission_level="AUDITOR",
            memory_focus="Context_Constraints",
            special_attributes={"decision_power": "VETO_ONLY"},
            project_id=project_id,
        )

    def evaluate(
        self,
        task_id: str,
        output: str,
        context: dict = None,
        risk_level: float = 0.0,
    ) -> dict:
        task = self.task_manager.get(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}

        evaluation = {
            "task_id": task_id,
            "output": output,
            "context": context or {},
            "result": EvaluationResult.PASS,
            "score": 1.0,
            "issues": [],
            "evidence": [],
            "timestamp": __import__("time").time(),
        }

        if not output or len(output.strip()) == 0:
            evaluation["result"] = EvaluationResult.REJECT
            evaluation["issues"].append("Empty output")
            evaluation["score"] = 0.0

        if risk_level > self._thresholds["risk_tolerance"]:
            evaluation["issues"].append(f"Risk level {risk_level} exceeds threshold")
            evaluation["result"] = EvaluationResult.NEEDS_REVISION

        if task.agent_id:
            agent = self.registry.get(task.agent_id)
            if agent:
                evaluation["executor_id"] = agent.id
                evaluation["executor_type"] = agent.agent_type

        if evaluation["result"] == EvaluationResult.PASS:
            self._rejection_counts.pop(task_id, None)
        else:
            count = self._rejection_counts.get(task_id, 0) + 1
            self._rejection_counts[task_id] = count
            evaluation["rejection_count"] = count

            if count >= 3:
                evaluation["human_intervention_required"] = True

        self.event_bus.emit(
            event_type="task.evaluated",
            payload={
                "task_id": task_id,
                "result": evaluation["result"],
                "score": evaluation["score"],
                "issues": evaluation["issues"],
            },
        )

        return evaluation

    def evaluate_with_consensus(
        self, task_id: str, output: str, models: list = None
    ) -> dict:
        if models is None:
            models = ["gpt-4o", "claude-3-5-sonnet"]

        votes = []
        for model in models:
            result = self.evaluate(task_id, output, {"model": model})
            votes.append(result["result"])

        pass_count = votes.count(EvaluationResult.PASS)
        reject_count = votes.count(EvaluationResult.REJECT)

        return {
            "task_id": task_id,
            "votes": votes,
            "consensus": EvaluationResult.PASS if pass_count > reject_count else EvaluationResult.REJECT,
            "pass_count": pass_count,
            "reject_count": reject_count,
        }

    def set_threshold(self, key: str, value: float):
        if key in self._thresholds:
            self._thresholds[key] = value

    def get_rejection_count(self, task_id: str) -> int:
        return self._rejection_counts.get(task_id, 0)
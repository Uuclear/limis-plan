"""轻量状态机 - 工作流引擎"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class State:
    name: str
    terminal: bool = False

@dataclass
class Transition:
    name: str
    from_state: str
    to_state: str
    required_role: Optional[str] = None

@dataclass
class WorkflowDefinition:
    name: str
    states: Dict[str, State]
    transitions: Dict[str, Transition]
    initial_state: str

class StateMachine:
    def __init__(self, definition: WorkflowDefinition):
        self.definition = definition
        self.current_state = definition.initial_state
        self.history: List[Dict[str, Any]] = []

    def can_transition(self, action: str) -> bool:
        action = action.strip()
        for t in self.definition.transitions.values():
            if t.name == action and t.from_state == self.current_state:
                return True
        return False

    def transition(self, action: str, user: str, reason: str = "") -> bool:
        action = action.strip()
        for t in self.definition.transitions.values():
            if t.name == action and t.from_state == self.current_state:
                old = self.current_state
                self.current_state = t.to_state
                self.history.append({
                    "action": action,
                    "from": old,
                    "to": self.current_state,
                    "user": user,
                    "reason": reason,
                })
                return True
        return False

    def get_available_actions(self) -> List[str]:
        return [
            t.name for t in self.definition.transitions.values()
            if t.from_state == self.current_state
        ]

SAMPLE_WORKFLOW = WorkflowDefinition(
    name="sample_lifecycle",
    states={
        "draft": State("draft"),
        "received": State("received"),
        "testing": State("testing"),
        "reviewing": State("reviewing"),
        "approved": State("approved"),
        "completed": State("completed", terminal=True),
        "cancelled": State("cancelled", terminal=True),
    },
    transitions={
        "submit": Transition("submit", "draft", "received"),
        "start_testing": Transition("start_testing", "received", "testing"),
        "submit_review": Transition("submit_review", "testing", "reviewing"),
        "approve": Transition("approve", "reviewing", "approved"),
        "complete": Transition("complete", "approved", "completed"),
        "reject_to_testing": Transition("reject_to_testing", "reviewing", "testing"),
        "cancel": Transition("cancel", "draft", "cancelled"),
    },
    initial_state="draft",
)

ORDER_WORKFLOW = WorkflowDefinition(
    name="order_lifecycle",
    states={
        "draft": State("draft"),
        "submitted": State("submitted"),
        "in_progress": State("in_progress"),
        "completed": State("completed", terminal=True),
        "cancelled": State("cancelled", terminal=True),
    },
    transitions={
        "submit": Transition("submit", "draft", "submitted"),
        "start": Transition("start", "submitted", "in_progress"),
        "complete": Transition("complete", "in_progress", "completed"),
        "cancel_draft": Transition("cancel_draft", "draft", "cancelled"),
    },
    initial_state="draft",
)

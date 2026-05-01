class WorkflowEngine:
    def __init__(self, states: list[str], transitions: list[dict]):
        self.states = states
        self.transitions = transitions

    def can_transition(self, from_state: str, to_state: str, role: str) -> bool:
        for t in self.transitions:
            if t["from"] == from_state and t["to"] == to_state:
                return role in t.get("roles", [])
        return False

    @classmethod
    def from_template(cls, template) -> "WorkflowEngine":
        return cls(states=template.states, transitions=template.transitions)

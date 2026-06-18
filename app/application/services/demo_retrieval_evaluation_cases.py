from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DemoRetrievalEvaluationCaseDefinition:
    name: str
    query: str
    expected_stable_section_keys: tuple[str, ...]
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be blank")

        if not self.query.strip():
            raise ValueError("query must not be blank")

        if not self.expected_stable_section_keys:
            raise ValueError("expected_stable_section_keys must not be empty")

        for key in self.expected_stable_section_keys:
            if not key.strip():
                raise ValueError("expected_stable_section_keys must not contain blank values")

        if len(self.expected_stable_section_keys) != len(
            set(self.expected_stable_section_keys),
        ):
            raise ValueError(
                "expected_stable_section_keys must be unique within a case",
            )

        for tag in self.tags:
            if not tag.strip():
                raise ValueError("tags must not contain blank values")


_DEMO_RETRIEVAL_EVALUATION_CASE_DEFINITIONS: tuple[
    DemoRetrievalEvaluationCaseDefinition,
    ...
] = (
    DemoRetrievalEvaluationCaseDefinition(
        name="Project Atlas ownership",
        query="Who owns Project Atlas?",
        expected_stable_section_keys=("project-atlas-brief/ownership",),
        tags=("demo", "project-atlas", "retrieval-evaluation"),
    ),
    DemoRetrievalEvaluationCaseDefinition(
        name="Project Atlas overview",
        query="What is Project Atlas?",
        expected_stable_section_keys=("project-atlas-brief/overview",),
        tags=("demo", "project-atlas", "retrieval-evaluation"),
    ),
    DemoRetrievalEvaluationCaseDefinition(
        name="Support escalation checklist",
        query="What should support do before escalating a customer issue?",
        expected_stable_section_keys=(
            "customer-support-escalation-policy/pre-escalation-checklist",
        ),
        tags=("demo", "support", "retrieval-evaluation"),
    ),
    DemoRetrievalEvaluationCaseDefinition(
        name="Incident severity levels",
        query="What is the incident severity process?",
        expected_stable_section_keys=(
            "incident-response-playbook/severity-levels",
            "incident-response-playbook/response-process",
        ),
        tags=("demo", "incident-response", "retrieval-evaluation"),
    ),
    DemoRetrievalEvaluationCaseDefinition(
        name="Engineering first week",
        query="What should new engineers do in their first week?",
        expected_stable_section_keys=("engineering-onboarding-guide/first-week",),
        tags=("demo", "engineering", "retrieval-evaluation"),
    ),
)


def get_demo_retrieval_evaluation_case_definitions() -> tuple[
    DemoRetrievalEvaluationCaseDefinition,
    ...
]:
    return _DEMO_RETRIEVAL_EVALUATION_CASE_DEFINITIONS

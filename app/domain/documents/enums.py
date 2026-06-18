from enum import StrEnum


class SourceSystem(StrEnum):
    LOCAL_SEED_DOCUMENTS = "local_seed_documents"
    DEMO_DOCUMENTS = "demo_documents"


class SourceDocumentStatus(StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"


class IngestionRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
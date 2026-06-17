from enum import StrEnum


class LLMProviderCallStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
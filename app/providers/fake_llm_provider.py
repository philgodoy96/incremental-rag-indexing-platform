from app.providers.llm import (
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMProvider,
)


class FakeLLMProvider(LLMProvider):
    def generate_answer(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        first_chunk = request.context_chunks[0]

        return LLMGenerationResponse(
            answer=(
                "Based on the retrieved context, "
                f"{first_chunk.content}"
            ),
        )
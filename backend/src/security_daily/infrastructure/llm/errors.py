class LLMProviderError(Exception):
    """LLM Provider 호출 또는 응답 형식 오류."""


class LLMConnectionError(LLMProviderError):
    pass


class LLMResponseError(LLMProviderError):
    pass

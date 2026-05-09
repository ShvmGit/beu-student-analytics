from pydantic import BaseModel, Field
from typing import Literal
from schemas.result_schema import RawResult
from schemas.analysis_schema import AnalysisResult

class FetchRequest(BaseModel):
    """Agent A → Agent B"""
    reg_no: str
    semester: int = Field(ge=1, le=8)


class FetchError(BaseModel):
    """Agent B → Agent A on failure"""
    error_type: Literal[
        "api_unavailable",
        "invalid_reg_no",
        "result_not_found",
        "rate_limited",
        "parse_error"
    ]
    message: str
    retry_after: int | None = None  # seconds


class AgentContext(BaseModel):
    """Shared context passed through the full pipeline."""
    session_id: str
    reg_no: str | None = None
    semester: int | None = None
    raw_result: RawResult | None = None        # set by Agent B
    analysis_result: AnalysisResult | None = None  # set by Agent C
    conversation_history: list[dict] = []          # [{"role": "user"|"assistant", "content": str}]
    error: FetchError | None = None

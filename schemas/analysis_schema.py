from pydantic import BaseModel, Field
from typing import Literal

class ComputedMetrics(BaseModel):
    """Purely Python-computed metrics. No LLM involved."""
    total_max_marks: int
    total_obtained_marks: int
    percentage: float = Field(ge=0.0, le=100.0)
    sgpa: float | None
    backlogs: int                          # number of failed subjects
    passed_all: bool
    top_subjects: list[str]                # top 3 by marks, descending
    bottom_subjects: list[str]             # bottom 3 by marks, ascending
    per_subject_pass_fail: dict[str, bool]  # {subject_name: True/False}


class AcademicInsights(BaseModel):
    """LLM-generated insights. Output of Agent C LLM call."""
    strength_subjects: list[str]
    weak_subjects: list[str]
    performance_level: Literal["Excellent", "Good", "Average", "Poor"]
    overall_status: Literal["PASS", "FAIL", "PASS_WITH_BACKLOG"]
    improvement_suggestion: str            # 2-3 actionable sentences
    study_tips: list[str]                  # 2-4 specific tips


class AnalysisResult(BaseModel):
    """Full analysis. Agent C → Agent A."""
    reg_no: str
    student_name: str | None
    semester: int
    metrics: ComputedMetrics
    insights: AcademicInsights

    # Convenience properties for Agent A
    @property
    def summary_line(self) -> str:
        status = self.insights.overall_status
        pct = self.metrics.percentage
        sgpa = self.metrics.sgpa
        sgpa_str = f", SGPA: {sgpa}" if sgpa else ""
        return f"Status: {status} | Percentage: {pct:.1f}%{sgpa_str}"

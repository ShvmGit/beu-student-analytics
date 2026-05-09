import json
from pathlib import Path
from loguru import logger
from schemas.result_schema import RawResult
from schemas.analysis_schema import ComputedMetrics, AcademicInsights, AnalysisResult
from services.model_router import route_completion

def load_prompt(filename: str) -> str:
    """Load a prompt file from the prompts/ directory."""
    prompt_path = Path(__file__).parent.parent / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8").strip()

def build_analysis_user_message(raw_result: RawResult, metrics: ComputedMetrics) -> str:
    """
    Combine raw result and computed metrics into a single user message for the LLM.
    """
    payload = {
        "student_name": raw_result.student_name,
        "semester": raw_result.semester,
        "course": raw_result.course,
        "sgpa": raw_result.sgpa,
        "cgpa": raw_result.cgpa,
        "overall_status": raw_result.overall_status,
        "percentage": metrics.percentage,
        "backlogs": metrics.backlogs,
        "subjects": [
            {
                "name": s.subject_name,
                "type": "Practical" if s.is_practical else "Theory",
                "obtained": s.obtained_marks,
                "max": s.max_marks,
                "percentage": round(s.obtained_marks / s.max_marks * 100, 1) if s.max_marks > 0 else 0,
                "passed": s.is_pass,
                "grade": s.grade,
                "credit": s.credit,
            }
            for s in raw_result.subjects
        ],
    }
    return f"Analyze this student result:\n{json.dumps(payload, indent=2)}"

def parse_llm_analysis(raw_response: str) -> AcademicInsights:
    """
    Safely parse LLM JSON output.
    """
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in LLM response: {raw_response[:200]}")

    json_str = cleaned[start:end]

    try:
        parsed = json.loads(json_str)
        return AcademicInsights(**parsed)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to parse LLM analysis: {e}\nRaw: {raw_response[:300]}")
        raise ValueError(f"LLM returned invalid analysis format: {e}")

class AnalysisAgent:
    def __init__(self):
        self.system_prompt = load_prompt("analysis_system.txt")

    def compute_metrics(self, raw: RawResult) -> ComputedMetrics:
        # Pure Python - no LLM
        subjects = raw.subjects
        total_max = sum(s.max_marks for s in subjects)
        total_obtained = sum(s.obtained_marks for s in subjects)
        percentage = (total_obtained / total_max * 100) if total_max > 0 else 0.0
        backlogs = sum(1 for s in subjects if not s.is_pass)
        sorted_by_marks = sorted(subjects, key=lambda s: s.obtained_marks, reverse=True)
        top = [s.subject_name for s in sorted_by_marks[:3]]
        bottom = [s.subject_name for s in sorted_by_marks[-3:]]
        pass_fail = {s.subject_name: s.is_pass for s in subjects}

        return ComputedMetrics(
            total_max_marks=total_max,
            total_obtained_marks=total_obtained,
            percentage=round(percentage, 2),
            sgpa=raw.sgpa,
            backlogs=backlogs,
            passed_all=(backlogs == 0),
            top_subjects=top,
            bottom_subjects=bottom,
            per_subject_pass_fail=pass_fail,
        )

    async def generate_insights(self, raw: RawResult, metrics: ComputedMetrics) -> AcademicInsights:
        user_message = build_analysis_user_message(raw, metrics)
        raw_response = await route_completion(
            task_type="analysis",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ]
        )
        return parse_llm_analysis(raw_response)

    async def analyze(self, raw: RawResult) -> AnalysisResult:
        metrics = self.compute_metrics(raw)
        insights = await self.generate_insights(raw, metrics)
        return AnalysisResult(
            reg_no=raw.reg_no,
            student_name=raw.student_name,
            semester=raw.semester,
            metrics=metrics,
            insights=insights,
        )

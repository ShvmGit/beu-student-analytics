from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from schemas.agent_schema import FetchRequest, FetchError
from agents.fetch_agent import FetchAgent
from agents.analysis_agent import AnalysisAgent
from agents.chat_agent import ChatAgent
from agents.analysis_agent import load_prompt
from services.model_router import route_completion
import uuid

router = APIRouter(prefix="/result", tags=["result"])


class FullResultResponse(BaseModel):
    """Enriched response combining raw data + analysis + explanation."""
    success: bool
    student_name: str | None = None
    reg_no: str | None = None
    semester: int | None = None
    college_name: str | None = None
    course: str | None = None
    sgpa: float | None = None
    cgpa: float | None = None
    overall_status: str | None = None
    percentage: float | None = None
    backlogs: int | None = None
    performance_level: str | None = None
    improvement_suggestion: str | None = None
    study_tips: list[str] = []
    strength_subjects: list[str] = []
    weak_subjects: list[str] = []
    explanation: str | None = None
    subjects: list[dict] = []
    error: str | None = None


@router.post("/analyze")
async def analyze_result(request: FetchRequest):
    """
    POST /result/analyze
    Body: {"reg_no": "24153125054", "semester": 2}
    Returns: Full analysis with explanation
    """
    fetch_agent = FetchAgent()
    analysis_agent = AnalysisAgent()

    raw = await fetch_agent.run(request)
    if isinstance(raw, FetchError):
        return FullResultResponse(success=False, error=raw.message)

    try:
        analysis = await analysis_agent.analyze(raw)
    except Exception as e:
        return FullResultResponse(
            success=False,
            error=f"Analysis failed: {str(e)}",
            student_name=raw.student_name,
            reg_no=raw.reg_no,
            semester=raw.semester,
        )

    # Generate natural-language explanation
    explanation = ""
    try:
        chat_agent = ChatAgent()
        explanation = await chat_agent._generate_explanation(analysis)
    except Exception:
        explanation = "Could not generate explanation."

    # Build subject list for frontend
    subjects = []
    for s in raw.subjects:
        pct = round(s.obtained_marks / s.max_marks * 100, 1) if s.max_marks > 0 else 0
        subjects.append({
            "name": s.subject_name,
            "code": s.subject_code,
            "obtained": s.obtained_marks,
            "max": s.max_marks,
            "percentage": pct,
            "grade": s.grade,
            "credit": s.credit,
            "is_pass": s.is_pass,
            "is_practical": s.is_practical,
            "ese": s.ese_marks,
            "ia": s.ia_marks,
        })

    return FullResultResponse(
        success=True,
        student_name=raw.student_name,
        reg_no=raw.reg_no,
        semester=raw.semester,
        college_name=raw.college_name,
        course=raw.course,
        sgpa=raw.sgpa,
        cgpa=raw.cgpa,
        overall_status=analysis.insights.overall_status,
        percentage=analysis.metrics.percentage,
        backlogs=analysis.metrics.backlogs,
        performance_level=analysis.insights.performance_level,
        improvement_suggestion=analysis.insights.improvement_suggestion,
        study_tips=analysis.insights.study_tips,
        strength_subjects=analysis.insights.strength_subjects,
        weak_subjects=analysis.insights.weak_subjects,
        explanation=explanation,
        subjects=subjects,
    )


class ChatRequest(BaseModel):
    message: str
    context: dict | None = None  # The analysis result for context


@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    POST /result/chat
    Body: {"message": "What can I do to improve in Math?", "context": {...}}
    Returns: {"reply": "..."}
    """
    system_prompt = (
        "You are a friendly and knowledgeable academic assistant for Bihar Engineering University (BEU) students. "
        "You are helping a student understand their exam result. "
        "Answer their questions clearly and concisely. Use simple language. "
        "Be encouraging and constructive. If the student asks about improvement, give specific, actionable tips. "
        "Keep responses to 3-5 sentences unless the student asks for detail. "
        "Never make up data — only use the context provided."
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Inject result context if available
    if request.context:
        ctx = request.context
        context_text = (
            f"[Student Result Context]\n"
            f"Name: {ctx.get('student_name', 'N/A')}\n"
            f"Semester: {ctx.get('semester', 'N/A')}\n"
            f"Percentage: {ctx.get('percentage', 'N/A')}%\n"
            f"SGPA: {ctx.get('sgpa', 'N/A')}, CGPA: {ctx.get('cgpa', 'N/A')}\n"
            f"Status: {ctx.get('overall_status', 'N/A')}\n"
            f"Performance: {ctx.get('performance_level', 'N/A')}\n"
            f"Strengths: {', '.join(ctx.get('strength_subjects', []))}\n"
            f"Weaknesses: {', '.join(ctx.get('weak_subjects', []))}\n"
            f"Subjects: {', '.join(s.get('name', '') + ' (' + str(s.get('percentage', '')) + '%)' for s in ctx.get('subjects', []))}\n"
        )
        messages.append({"role": "system", "content": context_text})

    messages.append({"role": "user", "content": request.message})

    try:
        reply = await route_completion(task_type="chat", messages=messages)
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Sorry, I encountered an error: {str(e)}"}


@router.get("/health")
async def health():
    return {"status": "ok"}

import re
from loguru import logger
from schemas.agent_schema import AgentContext, FetchRequest, FetchError
from schemas.analysis_schema import AnalysisResult
from agents.fetch_agent import FetchAgent
from agents.analysis_agent import AnalysisAgent, load_prompt
from services.model_router import route_completion


class ChatAgent:
    def __init__(self):
        self.system_prompt = load_prompt("chat_system.txt")
        self.explanation_template = load_prompt("explanation_template.txt")
        self.fetch_agent = FetchAgent()
        self.analysis_agent = AnalysisAgent()

    async def _ask_for_reg_no(self, user_message: str, context: AgentContext) -> str:
        """Extract reg_no from user message, or ask for it."""
        match = re.search(r'\b(\d{10,12})\b', user_message)
        if match:
            context.reg_no = match.group(1)
            # Check if semester is also in same message
            return await self.handle_message(user_message, context)

        return (
            "Hello! 👋 I'd be happy to help you check your BEU result. "
            "Please provide your registration number."
        )

    async def _ask_for_semester(self, user_message: str, context: AgentContext) -> str:
        """Extract semester from user message, or ask for it."""
        # Try "sem 3" or "semester 3" or "3rd"
        match = re.search(r'[sS]em(?:ester)?\s*(\d)', user_message)
        if match:
            try:
                context.semester = int(match.group(1))
                return await self.handle_message(user_message, context)
            except ValueError:
                pass

        # Try ordinal: "3rd", "2nd"
        match = re.search(r'(\d)(?:st|nd|rd|th)', user_message)
        if match:
            try:
                context.semester = int(match.group(1))
                return await self.handle_message(user_message, context)
            except ValueError:
                pass

        # Try bare digit 1-8
        match = re.search(r'\b([1-8])\b', user_message)
        if match:
            try:
                context.semester = int(match.group(1))
                return await self.handle_message(user_message, context)
            except ValueError:
                pass

        return "Got it! Which semester result would you like to check? (1-8)"

    async def _fetch_and_analyze(self, context: AgentContext) -> str:
        """Fetch result from BEU API and run analysis pipeline."""
        request = FetchRequest(reg_no=context.reg_no, semester=context.semester)

        print("⏳ Fetching your result from BEU servers...")

        raw_result = await self.fetch_agent.run(request)
        if isinstance(raw_result, FetchError):
            context.error = raw_result

            if raw_result.error_type == "invalid_reg_no":
                context.reg_no = None

            return f"❌ I ran into an issue: {raw_result.message}. Please try again."

        context.raw_result = raw_result

        print("📊 Analyzing your result...")

        try:
            analysis = await self.analysis_agent.analyze(raw_result)
            context.analysis_result = analysis
            return await self._generate_explanation(analysis)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return (
                f"I fetched your result but encountered an error during analysis: {e}"
            )

    async def _generate_explanation(self, analysis: AnalysisResult) -> str:
        """Use the LLM to generate a natural-language explanation of the result."""
        # Build subject-wise breakdown for the prompt
        subject_lines = []
        for s_name, passed in analysis.metrics.per_subject_pass_fail.items():
            status = "✅ Pass" if passed else "❌ Fail"
            subject_lines.append(f"  - {s_name}: {status}")
        subject_breakdown = "\n".join(subject_lines) if subject_lines else "  (no subjects)"

        user_prompt = self.explanation_template.format(
            student_name=analysis.student_name or "Student",
            semester=analysis.semester,
            percentage=analysis.metrics.percentage,
            sgpa=analysis.metrics.sgpa or "N/A",
            overall_status=analysis.insights.overall_status,
            backlogs=analysis.metrics.backlogs,
            strength_subjects=", ".join(analysis.insights.strength_subjects) or "None",
            weak_subjects=", ".join(analysis.insights.weak_subjects) or "None",
            performance_level=analysis.insights.performance_level,
            improvement_suggestion=analysis.insights.improvement_suggestion,
            subject_breakdown=subject_breakdown,
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return await route_completion(task_type="explanation", messages=messages)

    async def _handle_followup(self, user_message: str, context: AgentContext) -> str:
        """Answer follow-up questions using conversation history + result context."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Include recent conversation history for multi-turn context
        for msg in context.conversation_history[-6:]:
            messages.append(msg)

        # Inject analysis context if available
        if context.analysis_result:
            a = context.analysis_result
            result_context = (
                f"[Context for answering — do not repeat this verbatim]\n"
                f"Student: {a.student_name}, Semester: {a.semester}\n"
                f"Result: {a.summary_line}\n"
                f"Performance: {a.insights.performance_level}\n"
                f"Strong subjects: {', '.join(a.insights.strength_subjects)}\n"
                f"Weak subjects: {', '.join(a.insights.weak_subjects)}\n"
                f"Study tips: {'; '.join(a.insights.study_tips)}\n"
            )
            messages.append({"role": "system", "content": result_context})

        messages.append({"role": "user", "content": user_message})

        return await route_completion(task_type="chat", messages=messages)

    async def handle_message(self, user_message: str, context: AgentContext) -> str:
        """Main entry point — routes the message to the right stage."""
        # Stage 1: Collect reg_no
        if not context.reg_no:
            response = await self._ask_for_reg_no(user_message, context)
            context.conversation_history.append({"role": "user", "content": user_message})
            context.conversation_history.append({"role": "assistant", "content": response})
            return response

        # Stage 2: Collect semester
        if not context.semester:
            response = await self._ask_for_semester(user_message, context)
            context.conversation_history.append({"role": "user", "content": user_message})
            context.conversation_history.append({"role": "assistant", "content": response})
            return response

        # Stage 3: Fetch + analyze if not done yet
        if not context.raw_result:
            response = await self._fetch_and_analyze(context)
            context.conversation_history.append({"role": "user", "content": user_message})
            context.conversation_history.append({"role": "assistant", "content": response})
            return response

        # Stage 4: Handle follow-up questions
        response = await self._handle_followup(user_message, context)
        context.conversation_history.append({"role": "user", "content": user_message})
        context.conversation_history.append({"role": "assistant", "content": response})
        return response

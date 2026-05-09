import streamlit as st
import asyncio
import pandas as pd

from agents.fetch_agent import FetchAgent
from agents.analysis_agent import AnalysisAgent
from agents.chat_agent import ChatAgent
from schemas.agent_schema import FetchRequest, FetchError
from services.config import setup_logging

setup_logging("INFO")

st.set_page_config(page_title="BEU Result AI", page_icon="🎓", layout="wide")

st.title("🎓 BEU Result Intelligence Assistant")
st.markdown("AI-powered exam result analysis for Bihar Engineering University students.")

@st.cache_resource
def get_agents():
    return FetchAgent(), AnalysisAgent(), ChatAgent()

fetch_agent, analysis_agent, chat_agent = get_agents()

# Sidebar for Chat
with st.sidebar:
    st.header("💬 Ask AI")
    st.markdown("Ask any questions about your result after analyzing it!")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    chat_input = st.chat_input("Ask a question...")

if chat_input:
    st.session_state.messages.append({"role": "user", "content": chat_input})
    with st.sidebar.chat_message("user"):
        st.markdown(chat_input)

    with st.sidebar.chat_message("assistant"):
        with st.spinner("Thinking..."):
            async def ask_chat():
                system_prompt = (
                    "You are a friendly and knowledgeable academic assistant for Bihar Engineering University (BEU) students. "
                    "You are helping a student understand their exam result. "
                    "Answer their questions clearly and concisely. Use simple language. "
                    "Be encouraging and constructive. If the student asks about improvement, give specific, actionable tips. "
                    "Keep responses to 3-5 sentences unless the student asks for detail. "
                    "Never make up data — only use the context provided."
                )
                messages = [{"role": "system", "content": system_prompt}]
                
                if 'analysis_context' in st.session_state:
                    ctx = st.session_state['analysis_context']
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
                    )
                    messages.append({"role": "system", "content": context_text})
                
                for m in st.session_state.messages[:-1]:
                    messages.append(m)
                
                messages.append({"role": "user", "content": chat_input})
                
                from services.model_router import route_completion
                return await route_completion(task_type="chat", messages=messages)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                reply = loop.run_until_complete(ask_chat())
            except Exception as e:
                reply = f"Error: {str(e)}"
            
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})


# Main form
with st.form("result_form"):
    col1, col2 = st.columns(2)
    with col1:
        reg_no = st.text_input("Registration Number", placeholder="e.g. 24153125054")
    with col2:
        semester = st.selectbox("Semester", options=list(range(1, 9)))
    submit = st.form_submit_button("Analyze Result", type="primary")

if submit:
    if not reg_no:
        st.error("Please enter a registration number.")
    else:
        with st.spinner("Fetching and analyzing your result from BEU servers..."):
            async def run_analysis():
                req = FetchRequest(reg_no=reg_no, semester=semester)
                raw = await fetch_agent.run(req)
                if isinstance(raw, FetchError):
                    return False, raw.message, None, None, None
                
                try:
                    analysis = await analysis_agent.analyze(raw)
                except Exception as e:
                    return False, f"Analysis failed: {str(e)}", raw, None, None

                try:
                    explanation = await chat_agent._generate_explanation(analysis)
                except Exception as e:
                    explanation = "Could not generate explanation."

                return True, None, raw, analysis, explanation

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, error_msg, raw, analysis, explanation = loop.run_until_complete(run_analysis())

        if not success:
            st.error(f"Failed to fetch result: {error_msg}")
        else:
            st.success("Analysis Complete!")
            
            # Save context for chat
            st.session_state['analysis_context'] = {
                "student_name": raw.student_name,
                "semester": raw.semester,
                "percentage": analysis.metrics.percentage,
                "sgpa": analysis.metrics.sgpa,
                "overall_status": analysis.insights.overall_status,
                "performance_level": analysis.insights.performance_level,
                "strength_subjects": analysis.insights.strength_subjects,
                "weak_subjects": analysis.insights.weak_subjects,
            }
            
            # Layout metrics
            st.subheader(f"👤 {raw.student_name or 'Unknown Student'} | Reg: {raw.reg_no}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Percentage", f"{analysis.metrics.percentage}%")
            c2.metric("SGPA", analysis.metrics.sgpa or "N/A")
            c3.metric("Status", analysis.insights.overall_status)
            c4.metric("Performance", analysis.insights.performance_level)

            # AI Analysis
            st.markdown("### ✦ AI Explanation")
            st.info(explanation)

            # Insights
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 💪 Strengths")
                for s in analysis.insights.strength_subjects:
                    st.markdown(f"- {s}")
            with col2:
                st.markdown("#### 📌 Needs Improvement")
                for s in analysis.insights.weak_subjects:
                    st.markdown(f"- {s}")

            st.markdown("#### 💡 Study Tips")
            for tip in analysis.insights.study_tips:
                st.markdown(f"- {tip}")

            # Subjects table
            st.markdown("### 📊 Subject-wise Performance")
            subject_data = []
            for s in raw.subjects:
                subject_data.append({
                    "Subject": s.subject_name,
                    "Type": "Practical" if s.is_practical else "Theory",
                    "Marks Obtained": s.obtained_marks,
                    "Max Marks": s.max_marks,
                    "Grade": s.grade,
                    "Credit": s.credit,
                    "Status": "✅ Pass" if s.is_pass else "❌ Fail"
                })
            df = pd.DataFrame(subject_data)
            st.dataframe(df, use_container_width=True)

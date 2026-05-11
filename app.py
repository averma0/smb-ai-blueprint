
import streamlit as st
from openai import OpenAI
import pandas as pd
from datetime import datetime

# ============================================================
# API KEY SETUP
# For Streamlit public deployment, add this in Streamlit Secrets:
# OPENAI_API_KEY = "your-key-here"
# ============================================================
client = OpenAI(api_key="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")
st.sidebar.caption("API key ending: " + client.api_key[-4:])

st.set_page_config(
    page_title="SMB AI Blueprint Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE
# ============================================================
if "response_text" not in st.session_state:
    st.session_state.response_text = ""

if "followup_history" not in st.session_state:
    st.session_state.followup_history = []

if "scores" not in st.session_state:
    st.session_state.scores = None

if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {}

if "report_generated_at" not in st.session_state:
    st.session_state.report_generated_at = None

# ============================================================
# CSS
# ============================================================
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #f8fafc 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .hero-card {
        padding: 2rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #111827 0%, #1e3a8a 55%, #312e81 100%);
        color: white;
        box-shadow: 0 20px 45px rgba(0,0,0,0.18);
        margin-bottom: 1.5rem;
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 850;
        margin-bottom: 0.3rem;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        opacity: 0.9;
        line-height: 1.6;
    }

    .section-card {
        padding: 1.4rem;
        border-radius: 22px;
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(148,163,184,0.3);
        box-shadow: 0 8px 22px rgba(15,23,42,0.06);
        margin-bottom: 1rem;
    }

    .pill {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: #e0e7ff;
        color: #3730a3;
        font-weight: 700;
        font-size: 0.8rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }

    .success-pill {
        background: #dcfce7;
        color: #166534;
    }

    .warning-pill {
        background: #fef3c7;
        color: #92400e;
    }

    .danger-pill {
        background: #fee2e2;
        color: #991b1b;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #475569;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
    }

    .metric-value {
        font-size: 2.4rem;
        font-weight: 850;
        color: #0f172a;
        line-height: 1.1;
        margin-top: 0.3rem;
    }

    .metric-helper {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.85);
        padding: 1rem;
        border-radius: 18px;
        border: 1px solid rgba(148,163,184,0.25);
        box-shadow: 0 6px 18px rgba(15,23,42,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# FUNCTIONS
# ============================================================
def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(value, max_value))


def score_readiness(data):
    readiness = (
        data["workflow_clarity"] * 0.18 +
        data["ai_literacy"] * 0.16 +
        data["governance_maturity"] * 0.20 +
        data["risk_tolerance"] * 0.10 +
        data["process_standardization"] * 0.12 +
        data["leadership_support"] * 0.12 +
        (6 - data["data_sensitivity"]) * 0.06 +
        (6 - data["task_complexity"]) * 0.06
    ) * 20

    friction = (
        data["data_sensitivity"] * 0.20 +
        data["task_complexity"] * 0.18 +
        (6 - data["governance_maturity"]) * 0.18 +
        (6 - data["ai_literacy"]) * 0.14 +
        (6 - data["workflow_clarity"]) * 0.14 +
        (6 - data["process_standardization"]) * 0.10 +
        (6 - data["leadership_support"]) * 0.06
    ) * 20

    risk = (
        data["data_sensitivity"] * 0.26 +
        data["task_complexity"] * 0.20 +
        (6 - data["governance_maturity"]) * 0.24 +
        (6 - data["workflow_clarity"]) * 0.12 +
        (6 - data["process_standardization"]) * 0.10 +
        (6 - data["ai_literacy"]) * 0.08
    ) * 20

    autonomy = (
        data["governance_maturity"] * 0.25 +
        data["workflow_clarity"] * 0.20 +
        data["process_standardization"] * 0.20 +
        data["ai_literacy"] * 0.15 +
        (6 - data["data_sensitivity"]) * 0.12 +
        (6 - data["task_complexity"]) * 0.08
    ) * 20

    return (
        round(clamp(readiness), 2),
        round(clamp(friction), 2),
        round(clamp(risk), 2),
        round(clamp(autonomy), 2)
    )


def score_band(score):
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Strong"
    elif score >= 50:
        return "Moderate"
    elif score >= 35:
        return "Weak"
    else:
        return "Critical"


def recommendation_label(readiness, friction, risk):
    if readiness >= 75 and friction <= 45 and risk <= 45:
        return "Adopt Now"
    elif readiness >= 55 and risk <= 65:
        return "Proceed Cautiously"
    elif readiness >= 40:
        return "Pilot Only"
    else:
        return "Delay and Prepare"


def model_mode_to_temperature(accuracy_focus, creativity_focus):
    base = 0.35
    temp = base + (creativity_focus / 100) * 0.55 - (accuracy_focus / 100) * 0.20
    return round(min(max(temp, 0.05), 1.0), 2)


def gauge_html(label, value, description):
    value = clamp(value)

    if value >= 75:
        color = "#16a34a"
    elif value >= 50:
        color = "#f59e0b"
    else:
        color = "#dc2626"

    return f"""
    <div class="section-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value:.1f}</div>
                <div class="metric-helper">{description}</div>
            </div>
            <div style="
                width:120px;
                height:120px;
                border-radius:50%;
                background: conic-gradient({color} {value}%, #e5e7eb {value}%);
                display:flex;
                align-items:center;
                justify-content:center;
                box-shadow: inset 0 0 0 12px #ffffff;
            ">
                <div style="
                    width:78px;
                    height:78px;
                    background:#ffffff;
                    border-radius:50%;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-weight:850;
                    color:#0f172a;
                ">
                    {int(value)}%
                </div>
            </div>
        </div>
    </div>
    """


def build_score_dataframe(readiness, friction, risk, autonomy):
    return pd.DataFrame({
        "Metric": [
            "AI Readiness",
            "Human-AI Friction",
            "Implementation Risk",
            "Autonomy Potential"
        ],
        "Score": [readiness, friction, risk, autonomy]
    })


def build_input_dataframe(data):
    return pd.DataFrame({
        "Factor": [
            "Workflow Clarity",
            "AI Literacy",
            "Governance Maturity",
            "Risk Tolerance",
            "Data Sensitivity",
            "Task Complexity",
            "Process Standardization",
            "Leadership Support"
        ],
        "Value": [
            data["workflow_clarity"],
            data["ai_literacy"],
            data["governance_maturity"],
            data["risk_tolerance"],
            data["data_sensitivity"],
            data["task_complexity"],
            data["process_standardization"],
            data["leadership_support"]
        ]
    })


def build_prompt(workflow, company_profile, data, readiness, friction, risk, autonomy, accuracy_focus, creativity_focus, depth):
    return f"""
You are a senior human-centered AI strategy consultant designing an applied AI adoption blueprint for a small or medium-sized business.

Your task is to produce a highly detailed, practical, executive-ready AI Blueprint.

BUSINESS WORKFLOW:
{workflow}

COMPANY PROFILE:
- Industry: {company_profile["industry"]}
- Company size: {company_profile["company_size"]}
- Primary business goal: {company_profile["primary_goal"]}
- Estimated budget level: {company_profile["budget_level"]}
- Implementation timeline: {company_profile["timeline"]}
- Current tools/software: {company_profile["current_tools"]}
- Main pain point: {company_profile["main_pain_point"]}

ORGANIZATIONAL INPUT SCORES, 1 LOW TO 5 HIGH:
- Workflow clarity: {data["workflow_clarity"]}
- AI literacy: {data["ai_literacy"]}
- Governance maturity: {data["governance_maturity"]}
- Risk tolerance: {data["risk_tolerance"]}
- Data sensitivity: {data["data_sensitivity"]}
- Task complexity: {data["task_complexity"]}
- Process standardization: {data["process_standardization"]}
- Leadership support: {data["leadership_support"]}

SYSTEM SCORES, 0 TO 100:
- AI Readiness Score: {readiness}
- Human-AI Friction Score: {friction}
- Implementation Risk Score: {risk}
- Autonomy Potential Score: {autonomy}

RESPONSE BEHAVIOR:
- Accuracy focus: {accuracy_focus}/100
- Creativity focus: {creativity_focus}/100
- Blueprint depth requested: {depth}

Produce a comprehensive report with these exact sections:

# 1. Executive Decision Summary
Give a direct boardroom-level answer: should this SMB adopt AI now, pilot first, delay, or proceed cautiously?

# 2. SMB AI Readiness Diagnosis
Explain the readiness score in plain English.
Identify what is helping adoption and what is blocking adoption.

# 3. AI Opportunity Map
Identify 6 to 8 specific AI use cases for this workflow.
For each use case include:
- Use case name
- Where it fits in the workflow
- Business value
- Difficulty
- Risk level
- Human oversight required
- Suggested tool type

# 4. Automation vs Augmentation Blueprint
Create three categories:
- Safe to automate
- AI should assist but human must approve
- Should remain human-controlled
Be very specific to the workflow.

# 5. Human-AI Friction Analysis
Explain the likely sources of employee resistance, trust breakdown, workflow disruption, and cognitive overload.

# 6. Governance and Risk Controls
Include policies for:
- Data handling
- Employee use
- Customer-facing AI
- Review and approval
- Bias and error management
- Audit logs
- Vendor/tool selection

# 7. Accuracy vs Creativity Settings
Explain how the company should set AI temperature or creativity controls for:
- Compliance-sensitive tasks
- Drafting and brainstorming
- Customer support
- Internal operations
- Strategic planning

# 8. Phased Implementation Roadmap
Create a phased roadmap:
- Phase 0: Preparation
- Phase 1: Low-risk quick wins
- Phase 2: Controlled pilots
- Phase 3: Workflow integration
- Phase 4: Scaled AI operating model
For each phase include actions, owners, risks, and success metrics.

# 9. KPI Dashboard
Recommend measurable KPIs:
- Efficiency KPIs
- Quality KPIs
- Financial KPIs
- Employee adoption KPIs
- Risk and governance KPIs

# 10. Final Strategic Recommendation
End with a direct recommendation and the next five actions the business should take.

Important:
- Do not be generic.
- Tie every recommendation directly to the workflow and company profile.
- Write like a consultant delivering a premium applied project.
- Use markdown headers, bullet points, and tables where useful.
"""


def create_download_text():
    if not st.session_state.response_text:
        return ""

    return f"""
SMB AI BLUEPRINT STUDIO REPORT
Generated: {st.session_state.report_generated_at}

SCORES:
{st.session_state.scores}

INPUTS:
{st.session_state.last_inputs}

REPORT:
{st.session_state.response_text}
"""

# ============================================================
# HERO
# ============================================================
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">SMB AI Blueprint Studio</div>
        <div class="hero-subtitle">
            A human-centered AI readiness dashboard for small and medium-sized businesses.
            Score readiness, diagnose human-AI friction, map AI opportunities, tune accuracy versus creativity,
            and generate a strategic implementation blueprint.
        </div>
        <br>
        <span class="pill success-pill">0 to 100 Readiness Scoring</span>
        <span class="pill">Interactive Dashboard</span>
        <span class="pill warning-pill">Risk and Governance Analysis</span>
        <span class="pill">AI Blueprint Generator</span>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Model Controls")

    model_choice = st.selectbox(
        "OpenAI model",
        ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
        index=0
    )

    accuracy_focus = st.slider(
        "Accuracy Focus",
        0,
        100,
        80,
        help="Higher accuracy makes the model more conservative."
    )

    creativity_focus = st.slider(
        "Creativity Focus",
        0,
        100,
        35,
        help="Higher creativity makes the model more expansive."
    )

    temperature = model_mode_to_temperature(accuracy_focus, creativity_focus)

    st.markdown(
        gauge_html(
            "Response Temperature",
            temperature * 100,
            f"Calculated model temperature: {temperature}"
        ),
        unsafe_allow_html=True
    )

    depth = st.select_slider(
        "Blueprint Depth",
        options=["Brief", "Standard", "Detailed", "Very Detailed"],
        value="Very Detailed"
    )

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Assessment Builder",
    "Dashboard",
    "AI Blueprint",
    "Follow-Up Consultant",
    "Export"
])

# ============================================================
# TAB 1
# ============================================================
with tab1:
    st.markdown("## Build the SMB AI Profile")

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Business Workflow")

        workflow = st.text_area(
            "Describe the workflow you want to evaluate",
            height=220,
            placeholder="Example: Our accounting team manually reviews invoices, matches them to purchase orders, emails managers for approvals, and enters data into QuickBooks."
        )

        main_pain_point = st.text_input(
            "Main pain point",
            placeholder="Example: Manual document review creates delays and errors."
        )

        current_tools = st.text_input(
            "Current tools/software",
            placeholder="Example: QuickBooks, Excel, Gmail, Google Drive, Salesforce"
        )

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Company Context")

        c1, c2 = st.columns(2)

        with c1:
            industry = st.selectbox(
                "Industry",
                [
                    "Professional Services",
                    "Accounting/Finance",
                    "Legal Services",
                    "Healthcare",
                    "Retail",
                    "Real Estate",
                    "Education/Training",
                    "Construction",
                    "Manufacturing",
                    "Hospitality",
                    "Nonprofit",
                    "Other"
                ]
            )

            company_size = st.selectbox(
                "Company size",
                [
                    "1-10 employees",
                    "11-50 employees",
                    "51-200 employees",
                    "201-500 employees",
                    "500+ employees"
                ]
            )

        with c2:
            primary_goal = st.selectbox(
                "Primary AI goal",
                [
                    "Reduce manual work",
                    "Improve customer experience",
                    "Increase revenue",
                    "Improve decision-making",
                    "Reduce errors",
                    "Scale operations",
                    "Improve compliance",
                    "Other"
                ]
            )

            budget_level = st.selectbox(
                "Budget level",
                [
                    "Very limited",
                    "Low",
                    "Moderate",
                    "High",
                    "Enterprise-level"
                ]
            )

        timeline = st.selectbox(
            "Desired implementation timeline",
            [
                "Immediate, 0-30 days",
                "Short-term, 1-3 months",
                "Medium-term, 3-6 months",
                "Long-term, 6-12 months",
                "Exploratory only"
            ]
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Organizational Inputs")

        workflow_clarity = st.slider("Workflow Clarity", 1, 5, 3)
        ai_literacy = st.slider("AI Literacy", 1, 5, 3)
        governance_maturity = st.slider("Governance Maturity", 1, 5, 3)
        risk_tolerance = st.slider("Risk Tolerance", 1, 5, 3)
        data_sensitivity = st.slider("Data Sensitivity", 1, 5, 3)
        task_complexity = st.slider("Task Complexity", 1, 5, 3)
        process_standardization = st.slider("Process Standardization", 1, 5, 3)
        leadership_support = st.slider("Leadership Support", 1, 5, 3)

        st.markdown('</div>', unsafe_allow_html=True)

        run_assessment = st.button(
            "Generate AI Readiness Blueprint",
            type="primary",
            use_container_width=True
        )

    data = {
        "workflow_clarity": workflow_clarity,
        "ai_literacy": ai_literacy,
        "governance_maturity": governance_maturity,
        "risk_tolerance": risk_tolerance,
        "data_sensitivity": data_sensitivity,
        "task_complexity": task_complexity,
        "process_standardization": process_standardization,
        "leadership_support": leadership_support
    }

    company_profile = {
        "industry": industry,
        "company_size": company_size,
        "primary_goal": primary_goal,
        "budget_level": budget_level,
        "timeline": timeline,
        "current_tools": current_tools,
        "main_pain_point": main_pain_point
    }

    readiness, friction, risk, autonomy = score_readiness(data)

    st.session_state.scores = {
        "readiness": readiness,
        "friction": friction,
        "risk": risk,
        "autonomy": autonomy
    }

    st.session_state.last_inputs = {
        "workflow": workflow,
        "company_profile": company_profile,
        "data": data,
        "accuracy_focus": accuracy_focus,
        "creativity_focus": creativity_focus,
        "temperature": temperature
    }

    if run_assessment:
        if workflow.strip() == "":
            st.warning("Please enter a workflow description before generating the blueprint.")
        else:
            prompt = build_prompt(
                workflow,
                company_profile,
                data,
                readiness,
                friction,
                risk,
                autonomy,
                accuracy_focus,
                creativity_focus,
                depth
            )

            with st.spinner("Generating your SMB AI Blueprint..."):
                try:
                    response = client.responses.create(
                        model=model_choice,
                        input=prompt,
                        temperature=temperature
                    )

                    st.session_state.response_text = response.output_text
                    st.session_state.report_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.success("Blueprint generated. Open the AI Blueprint tab to review the full report.")

                except Exception as e:
                    st.error("The AI report could not be generated.")
                    st.exception(e)

# ============================================================
# TAB 2
# ============================================================
with tab2:
    st.markdown("## AI Readiness Dashboard")

    if st.session_state.scores is None:
        st.info("Complete the assessment first.")
    else:
        readiness = st.session_state.scores["readiness"]
        friction = st.session_state.scores["friction"]
        risk = st.session_state.scores["risk"]
        autonomy = st.session_state.scores["autonomy"]

        rec = recommendation_label(readiness, friction, risk)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AI Readiness", f"{readiness:.1f}/100", score_band(readiness))
        m2.metric("Human-AI Friction", f"{friction:.1f}/100", score_band(100 - friction))
        m3.metric("Implementation Risk", f"{risk:.1f}/100", score_band(100 - risk))
        m4.metric("Autonomy Potential", f"{autonomy:.1f}/100", score_band(autonomy))

        if rec == "Adopt Now":
            st.success(f"Strategic Recommendation: {rec}")
        elif rec in ["Proceed Cautiously", "Pilot Only"]:
            st.warning(f"Strategic Recommendation: {rec}")
        else:
            st.error(f"Strategic Recommendation: {rec}")

        g1, g2 = st.columns(2)

        with g1:
            st.markdown(
                gauge_html(
                    "AI Readiness",
                    readiness,
                    "How prepared the organization is to adopt AI responsibly."
                ),
                unsafe_allow_html=True
            )
            st.markdown(
                gauge_html(
                    "Implementation Risk",
                    risk,
                    "How much operational, data, and governance risk exists."
                ),
                unsafe_allow_html=True
            )

        with g2:
            st.markdown(
                gauge_html(
                    "Human-AI Friction",
                    friction,
                    "How likely AI is to disrupt people, trust, or workflow stability."
                ),
                unsafe_allow_html=True
            )
            st.markdown(
                gauge_html(
                    "Autonomy Potential",
                    autonomy,
                    "How safely AI can act with reduced human intervention."
                ),
                unsafe_allow_html=True
            )

        st.markdown("### Score Comparison")
        score_df = build_score_dataframe(readiness, friction, risk, autonomy)
        st.bar_chart(score_df.set_index("Metric"))

        st.markdown("### Input Breakdown")
        input_df = build_input_dataframe(st.session_state.last_inputs["data"])
        st.bar_chart(input_df.set_index("Factor"))

        st.dataframe(score_df, use_container_width=True)
        st.dataframe(input_df, use_container_width=True)

# ============================================================
# TAB 3
# ============================================================
with tab3:
    st.markdown("## Generated AI Blueprint")

    if not st.session_state.response_text:
        st.info("Generate a blueprint from the Assessment Builder tab first.")
    else:
        st.markdown(st.session_state.response_text)

# ============================================================
# TAB 4
# ============================================================
with tab4:
    st.markdown("## Follow-Up Consultant")

    if not st.session_state.response_text:
        st.info("Generate a blueprint first, then ask follow-up questions.")
    else:
        user_question = st.text_input(
            "Ask a consulting follow-up",
            placeholder="Example: What should we automate first if the business has a limited budget?"
        )

        if st.button("Ask Follow-Up Consultant", type="primary"):
            if not user_question.strip():
                st.warning("Enter a question first.")
            else:
                followup_prompt = f"""
You are continuing an AI consulting engagement.

Prior AI Blueprint:
{st.session_state.response_text}

User follow-up question:
{user_question}

Answer as a senior SMB AI strategy consultant.

Provide:
1. Direct answer
2. Reasoning tied to the prior blueprint
3. Practical next steps
4. Risks or cautions
5. A concise recommendation
"""

                with st.spinner("Thinking through your follow-up..."):
                    try:
                        followup_response = client.responses.create(
                            model=model_choice,
                            input=followup_prompt,
                            temperature=temperature
                        )

                        answer = followup_response.output_text

                        st.session_state.followup_history.append({
                            "question": user_question,
                            "answer": answer,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })

                    except Exception as e:
                        st.error("The follow-up response could not be generated.")
                        st.exception(e)

        if st.session_state.followup_history:
            st.markdown("### Follow-Up History")
            for item in reversed(st.session_state.followup_history):
                with st.expander(f"{item['time']} — {item['question']}"):
                    st.markdown(item["answer"])

# ============================================================
# TAB 5
# ============================================================
with tab5:
    st.markdown("## Export")

    if not st.session_state.response_text:
        st.info("Generate a blueprint first to unlock export options.")
    else:
        export_text = create_download_text()

        st.download_button(
            label="Download Full AI Blueprint Report",
            data=export_text,
            file_name="smb_ai_blueprint_report.txt",
            mime="text/plain",
            use_container_width=True
        )

        snapshot = pd.DataFrame({
            "Category": [
                "AI Readiness",
                "Human-AI Friction",
                "Implementation Risk",
                "Autonomy Potential",
                "Strategic Recommendation",
                "Generated"
            ],
            "Value": [
                f'{st.session_state.scores["readiness"]:.1f}/100',
                f'{st.session_state.scores["friction"]:.1f}/100',
                f'{st.session_state.scores["risk"]:.1f}/100',
                f'{st.session_state.scores["autonomy"]:.1f}/100',
                recommendation_label(
                    st.session_state.scores["readiness"],
                    st.session_state.scores["friction"],
                    st.session_state.scores["risk"]
                ),
                st.session_state.report_generated_at
            ]
        })

        st.dataframe(snapshot, use_container_width=True)

        st.download_button(
            label="Download Executive Snapshot CSV",
            data=snapshot.to_csv(index=False),
            file_name="smb_ai_blueprint_snapshot.csv",
            mime="text/csv",
            use_container_width=True
        )

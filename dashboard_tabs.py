import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from pathlib import Path
import requests
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="Salesforce Training Analytics - Tab View",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="☁️"
)

# Salesforce color palette
SF_BLUE = "#0070D2"
SF_LIGHT_BLUE = "#00A1DE"
SF_DARK_BLUE = "#003D7A"
SF_GREEN = "#04844B"
SF_ORANGE = "#FF6B6B"
SF_COLORS = ["#0070D2", "#00A1DE", "#1589EE", "#003D7A"]
SF_GRADIENT = ["#003D7A", "#0070D2", "#00A1DE", "#FFFFFF"]

# Platform-specific colors
PLATFORM_COLORS = {
    "plusplus": "#2D7A4A",
    "trailhead": "#9DB93F",
    "pluralsight": "#F59E42",
    "oreilly": "#FF6B7A"
}

# ============================================================================
# CONFIGURATION
# ============================================================================

JOE_DEPARTMENTS = ["Engineering", "Product", "DevOps", "Platform"]
API_BASE = "http://localhost:8008"

# ============================================================================
# API CLIENTS
# ============================================================================

@lru_cache(maxsize=1)
def fetch_reach_participation():
    try:
        resp = requests.get(f"{API_BASE}/api/reach-participation", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Reach & Participation API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_engagement_quality():
    try:
        resp = requests.get(f"{API_BASE}/api/engagement-quality", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Engagement Quality API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_all_courses():
    try:
        resp = requests.get(f"{API_BASE}/api/all-courses?limit=200", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Courses API error: {e}")
    return {"courses": [], "total": 0}

@lru_cache(maxsize=1)
def fetch_platform_stats():
    try:
        resp = requests.get(f"{API_BASE}/api/stats", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Stats API error: {e}")
    return {"platforms": {}, "totals": {}}

def fetch_department_stats(department):
    try:
        resp = requests.get(f"{API_BASE}/api/departments/{department}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Department stats error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_knowledge_outcomes():
    try:
        resp = requests.get(f"{API_BASE}/api/knowledge-outcomes", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Knowledge outcomes API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_business_impact():
    try:
        resp = requests.get(f"{API_BASE}/api/business-impact", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Business impact API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_operational_health():
    try:
        resp = requests.get(f"{API_BASE}/api/operational-health", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Operational health API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_trends_cohorts():
    try:
        resp = requests.get(f"{API_BASE}/api/trends-cohorts", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Trends & cohorts API error: {e}")
    return {}

# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================

st.sidebar.title("🎓 Dashboard Controls")

selected_depts = st.sidebar.multiselect(
    "Joe Inzerillo's Departments",
    JOE_DEPARTMENTS,
    default=JOE_DEPARTMENTS
)

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("End Date", datetime.now())

st.sidebar.divider()

st.sidebar.subheader("📚 Platforms")
show_plusplus = st.sidebar.checkbox("PlusPlus (Learn++)", value=True)
show_trailhead = st.sidebar.checkbox("Trailhead", value=True)
show_pluralsight = st.sidebar.checkbox("Pluralsight", value=True)
show_oreilly = st.sidebar.checkbox("O'Reilly", value=True)

st.sidebar.divider()

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ============================================================================
# MAIN DASHBOARD HEADER
# ============================================================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("salesforce logo.jpg", width=200)

st.markdown(f"<h1 style='text-align: center; color: {SF_BLUE}; font-size: 2.5em; margin-top: 0;'>Training Analytics Dashboard - Tab View</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 0.9em;'>Alternate layout with sections as tabs</p>", unsafe_allow_html=True)

# ============================================================================
# TABS FOR EACH SECTION
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "📊 Reach & Participation",
    "⭐ Engagement Quality",
    "📈 Overall Metrics",
    "🎯 Platform Distribution",
    "⚖️ Platform Comparison",
    "🏢 Department Metrics",
    "📚 All Courses",
    "🎓 Knowledge Outcomes",
    "💼 Business Impact",
    "⚙️ Operational Health",
    "📈 Trends & Cohorts"
])

# ============================================================================
# TAB 1: REACH & PARTICIPATION
# ============================================================================

with tab1:
    st.header("Reach & Participation")
    reach = fetch_reach_participation()

    if reach:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Enrollments", reach.get("total_enrollments", 0))
        with col2:
            st.metric("Total Completions", reach.get("total_completions", 0))
        with col3:
            st.metric("Completion Rate", f"{reach.get('completion_rate', 0):.1f}%")
        with col4:
            st.metric("Active Users", reach.get("active_users", 0))

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Enrollments by Platform")
            enrollment_data = reach.get("enrollments_by_platform", {})
            if enrollment_data:
                fig = go.Figure(data=[go.Pie(
                    labels=[p.title() for p in enrollment_data.keys()],
                    values=list(enrollment_data.values()),
                    marker=dict(colors=[PLATFORM_COLORS.get(p, "#999") for p in enrollment_data.keys()])
                )])
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Completion Rate by Platform")
            completion_rates = reach.get("completion_rates_by_platform", {})
            if completion_rates:
                fig = px.bar(
                    x=list(completion_rates.keys()),
                    y=list(completion_rates.values()),
                    title="Completion Rate by Platform",
                    labels={"x": "Platform", "y": "Completion Rate %"},
                    color=list(completion_rates.keys()),
                    color_discrete_map={p: PLATFORM_COLORS.get(p, "#999") for p in completion_rates.keys()}
                )
                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Live Session Attendance")
            sessions = reach.get("live_sessions", {})
            if sessions:
                col1_1, col1_2, col1_3 = st.columns(3)
                with col1_1:
                    st.metric("Total Sessions", sessions.get("total_sessions", 0))
                with col1_2:
                    st.metric("Avg Attendance", f"{sessions.get('avg_attendance', 0):.0f}")
                with col1_3:
                    st.metric("Attendance Rate", f"{sessions.get('attendance_rate', 0):.1f}%")

        with col2:
            st.subheader("Content Consumption Trends")
            trends_data = reach.get("weekly_trend", [])
            if trends_data:
                trends_df = pd.DataFrame(trends_data)
                fig = px.line(
                    trends_df,
                    x="week",
                    y=["enrollments", "completions"],
                    markers=True,
                    title="Weekly Enrollment vs Completion Trend"
                )
                fig.update_layout(height=350, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2: ENGAGEMENT QUALITY
# ============================================================================

with tab2:
    st.header("Engagement Quality")
    quality = fetch_engagement_quality()

    if quality:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall NPS Score", f"{quality.get('overall_nps', 0):.0f}")
        with col2:
            st.metric("Avg Course Rating", f"{quality.get('avg_course_rating', 0):.1f}/5.0")
        with col3:
            st.metric("Total Feedback Responses", quality.get("total_feedback_responses", 0))

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("NPS Score by Platform")
            nps_data = quality.get("nps_by_platform", {})
            if nps_data:
                fig = px.bar(
                    x=list(nps_data.keys()),
                    y=list(nps_data.values()),
                    title="NPS Score by Platform",
                    labels={"x": "Platform", "y": "NPS Score"},
                    color=list(nps_data.keys()),
                    color_discrete_map={p: PLATFORM_COLORS.get(p, "#999") for p in nps_data.keys()}
                )
                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Feedback Sentiment Distribution")
            sentiment = quality.get("feedback_sentiment", {})
            if sentiment:
                fig = go.Figure(data=[go.Pie(
                    labels=list(sentiment.keys()),
                    values=list(sentiment.values()),
                    marker=dict(colors=["#04844B", "#FFB81C", "#E74C3C"])
                )])
                fig.update_layout(height=350, title="Feedback Themes")
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("Qualitative Feedback Themes")
        themes = quality.get("feedback_themes", {})
        if themes:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Positive Themes**")
                positive = themes.get("positive", [])
                for theme in positive:
                    st.caption(f"✓ {theme}")

            with col2:
                st.markdown("**Neutral Themes**")
                neutral = themes.get("neutral", [])
                for theme in neutral:
                    st.caption(f"○ {theme}")

            with col3:
                st.markdown("**Blocker Themes**")
                blockers = themes.get("blockers", [])
                for theme in blockers:
                    st.caption(f"✗ {theme}")

# ============================================================================
# TAB 3: OVERALL TRAINING METRICS
# ============================================================================

with tab3:
    st.header("Overall Training Metrics")
    stats = fetch_platform_stats()

    if stats:
        totals = stats.get("totals", {})

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Courses", totals.get("total_courses", 0))
        with col2:
            st.metric("Total Enrollments", f"{totals.get('total_enrollments', 0):,}")
        with col3:
            st.metric("Total Completions", f"{totals.get('total_completions', 0):,}")
        with col4:
            st.metric("Learning Hours", f"{totals.get('total_learning_hours', 0):,}")
        with col5:
            st.metric("Active Users", f"{totals.get('active_users', 0):,}")

        st.divider()

        st.subheader("Platform Statistics")
        platforms = stats.get("platforms", {})
        if platforms:
            platform_rows = []
            for platform, data in platforms.items():
                row = {"Platform": platform.title()}
                for key, val in data.items():
                    if key != "name":
                        row[key.replace("_", " ").title()] = val
                platform_rows.append(row)

            platform_df = pd.DataFrame(platform_rows)
            st.dataframe(platform_df, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 4: PLATFORM DISTRIBUTION
# ============================================================================

with tab4:
    st.header("Training Platform Distribution")
    stats = fetch_platform_stats()

    if stats:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Total Enrollments by Platform")
            platforms = stats.get("platforms", {})
            if platforms:
                enrollment_data = {p: data.get("enrollments", 0) for p, data in platforms.items()}
                fig = go.Figure(data=[go.Pie(
                    labels=[p.title() for p in enrollment_data.keys()],
                    values=list(enrollment_data.values()),
                    marker=dict(colors=[PLATFORM_COLORS.get(p, "#999") for p in enrollment_data.keys()])
                )])
                fig.update_layout(height=400, title="Enrollment Distribution")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Completion Rate by Platform")
            if platforms:
                completion_data = []
                for platform, data in platforms.items():
                    completion_data.append({
                        "Platform": platform.title(),
                        "Completion Rate": (data.get("completions", 0) / data.get("enrollments", 1) * 100) if data.get("enrollments", 0) > 0 else 0
                    })
                completion_df = pd.DataFrame(completion_data)
                fig = px.bar(
                    completion_df,
                    x="Platform",
                    y="Completion Rate",
                    title="Completion Rate by Platform",
                    color="Completion Rate",
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 5: PLATFORM COMPARISON
# ============================================================================

with tab5:
    st.header("Platform Comparison")
    stats = fetch_platform_stats()

    if stats:
        platforms = stats.get("platforms", {})
        if platforms:
            st.subheader("Side-by-Side Comparison")
            comparison_rows = []
            for platform, data in platforms.items():
                comparison_rows.append({
                    "Platform": platform.title(),
                    "Courses/Modules": data.get("courses", data.get("modules", data.get("books", 0))),
                    "Enrollments": data.get("enrollments", 0),
                    "Completions": data.get("completions", 0),
                    "Active Users": data.get("active_users", 0),
                    "Avg Rating": data.get("avg_rating", "N/A")
                })

            comparison_df = pd.DataFrame(comparison_rows)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 6: DEPARTMENT METRICS
# ============================================================================

with tab6:
    st.header("Department Metrics")

    if selected_depts:
        dept_tabs = st.tabs(selected_depts)

        for idx, dept in enumerate(selected_depts):
            with dept_tabs[idx]:
                dept_data = fetch_department_stats(dept)

                if dept_data:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Learners", dept_data.get("total_learners", 0))
                    with col2:
                        st.metric("Enrollments", dept_data.get("total_enrollments", 0))
                    with col3:
                        st.metric("Completions", dept_data.get("total_completions", 0))
                    with col4:
                        st.metric("Completion Rate", f"{dept_data.get('completion_rate', 0):.1f}%")

                    st.divider()

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Top Courses")
                        top_courses = dept_data.get("top_courses", [])
                        if top_courses:
                            course_df = pd.DataFrame(top_courses[:5])
                            st.dataframe(course_df, use_container_width=True, hide_index=True)

                    with col2:
                        st.subheader("Enrollment by Platform")
                        platform_dist = dept_data.get("enrollments_by_platform", {})
                        if platform_dist:
                            fig = go.Figure(data=[go.Pie(
                                labels=[p.title() for p in platform_dist.keys()],
                                values=list(platform_dist.values()),
                                marker=dict(colors=[PLATFORM_COLORS.get(p, "#999") for p in platform_dist.keys()])
                            )])
                            fig.update_layout(height=350)
                            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 7: ALL COURSES
# ============================================================================

with tab7:
    st.header("All Available Courses")
    courses_data = fetch_all_courses()

    if courses_data:
        courses = courses_data.get("courses", [])
        total = courses_data.get("total", 0)

        st.metric("Total Courses Available", total)

        if courses:
            course_df = pd.DataFrame(courses)

            st.subheader("Course Catalog")
            filtered_df = course_df.copy()

            col1, col2 = st.columns(2)
            with col1:
                search = st.text_input("Search courses...")
                if search:
                    filtered_df = filtered_df[filtered_df["title"].str.contains(search, case=False, na=False)]

            with col2:
                platform_filter = st.multiselect("Filter by platform", filtered_df["platform"].unique())
                if platform_filter:
                    filtered_df = filtered_df[filtered_df["platform"].isin(platform_filter)]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 8: KNOWLEDGE OUTCOMES
# ============================================================================

with tab8:
    st.header("Knowledge & Skill Outcomes")
    outcomes = fetch_knowledge_outcomes()

    if outcomes:
        st.subheader("Pre/Post Assessment Score Deltas")
        deltas = outcomes.get("assessment_deltas", {})

        col1, col2, col3, col4, col5 = st.columns(5)
        for idx, (platform, data) in enumerate([("PlusPlus", deltas.get("plusplus", {})),
                                                  ("Trailhead", deltas.get("trailhead", {})),
                                                  ("Pluralsight", deltas.get("pluralsight", {})),
                                                  ("O'Reilly", deltas.get("oreilly", {})),
                                                  ("Overall", deltas.get("overall", {}))]):
            col = [col1, col2, col3, col4, col5][idx]
            with col:
                st.metric(
                    platform,
                    f"+{data.get('improvement', 0):.1f}pts",
                    f"{data.get('pre_avg', 0):.0f} → {data.get('post_avg', 0):.0f}"
                )

        st.divider()

        st.subheader("Certification Pass Rates")
        cert_data = outcomes.get("certification_pass_rates", {})

        cert_rows = []
        for platform, rates in cert_data.items():
            cert_rows.append({
                "Platform": platform.replace("_", " ").title(),
                "First Attempt": f"{rates.get('first_attempt', 0)}%",
                "Retake": f"{rates.get('retake', 0)}%",
                "Overall": f"{rates.get('overall', 0)}%"
            })

        cert_df = pd.DataFrame(cert_rows)
        st.dataframe(cert_df, use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("Skill Proficiency Self-Assessment")
        skills = outcomes.get("skill_proficiency", {})

        skill_rows = []
        for skill, data in skills.items():
            skill_rows.append({
                "Skill": skill,
                "Pre-Assessment": f"{data.get('pre', 0):.1f}/5",
                "Post-Assessment": f"{data.get('post', 0):.1f}/5",
                "Improvement": f"+{data.get('post', 0) - data.get('pre', 0):.1f}",
                "Learners": data.get('learners', 0)
            })

        skills_df = pd.DataFrame(skill_rows)
        st.dataframe(skills_df, use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("Manager-Rated Skill Application (30/60/90-Day Check-ins)")
        manager_app = outcomes.get("manager_skill_application", {})

        dept_tabs = st.tabs(list(manager_app.keys()))

        for idx, (dept, checkpoints) in enumerate(manager_app.items()):
            with dept_tabs[idx]:
                col1, col2, col3 = st.columns(3)

                for col_idx, (timepoint, label) in enumerate([("30_day", "30-Day"),
                                                               ("60_day", "60-Day"),
                                                               ("90_day", "90-Day")]):
                    col = [col1, col2, col3][col_idx]
                    with col:
                        data = checkpoints.get(timepoint, {})
                        improved = data.get("improved", 0)
                        maintained = data.get("maintained", 0)
                        no_change = data.get("no_change", 0)
                        total = improved + maintained + no_change

                        fig = go.Figure(data=[go.Pie(
                            labels=["Improved", "Maintained", "No Change"],
                            values=[improved, maintained, no_change],
                            marker=dict(colors=[SF_GREEN, SF_BLUE, "#FFB81C"])
                        )])
                        fig.update_layout(
                            title=f"{label} Check-in",
                            height=350,
                            showlegend=True
                        )
                        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 9: BUSINESS IMPACT
# ============================================================================

with tab9:
    st.header("Business Impact")
    impact = fetch_business_impact()

    if impact:
        st.subheader("Performance Metric Correlations")
        correlations = impact.get("performance_correlations", {})

        col1, col2, col3, col4 = st.columns(4)

        for idx, (dept, data) in enumerate(correlations.items()):
            col = [col1, col2, col3, col4][idx]
            with col:
                st.markdown(f"### {dept}")
                st.metric("Topic", data.get("topic", ""))

                if "quota_attainment" in data:
                    pre_qa = data["quota_attainment"]["pre_training"]
                    post_qa = data["quota_attainment"]["post_training"]
                    corr = data["quota_attainment"]["correlation"]
                    st.metric("Quota Attainment", f"{post_qa}%", f"+{post_qa-pre_qa}% (r={corr})")

                if "ticket_resolution_time" in data:
                    pre_time = data["ticket_resolution_time"]["pre_hours"]
                    post_time = data["ticket_resolution_time"]["post_hours"]
                    imp_pct = data["ticket_resolution_time"]["improvement_pct"]
                    st.metric("Ticket Resolution", f"{post_time}h", f"{imp_pct}% faster")

                if "code_quality_score" in data:
                    pre_cq = data["code_quality_score"]["pre"]
                    post_cq = data["code_quality_score"]["post"]
                    imp_pct = data["code_quality_score"]["improvement_pct"]
                    st.metric("Code Quality", f"{post_cq}", f"+{post_cq-pre_cq} ({imp_pct}%)")

                if "feature_delivery_velocity" in data:
                    pre_vel = data["feature_delivery_velocity"]["pre_sprints"]
                    post_vel = data["feature_delivery_velocity"]["post_sprints"]
                    imp_pct = data["feature_delivery_velocity"]["improvement_pct"]
                    st.metric("Delivery Velocity", f"{post_vel} /sprint", f"+{imp_pct}%")

                st.caption(f"👥 {data.get('trained_count', 0)} trained")

        st.divider()

        st.subheader("Cost Analysis")
        cost_data = impact.get("cost_analysis", {})

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Program Cost", f"${cost_data.get('total_program_cost', 0):,.0f}")
        with col2:
            st.metric("Total Learners", cost_data.get('total_learners', 0))
        with col3:
            st.metric("Total Completions", cost_data.get('total_completions', 0))
        with col4:
            st.metric("Cost per Learner", f"${cost_data.get('cost_per_learner', 0):.2f}")
        with col5:
            st.metric("Cost per Completion", f"${cost_data.get('cost_per_completion', 0):.2f}")

        breakdown = cost_data.get("breakdown", {})
        if breakdown:
            fig = go.Figure(data=[go.Pie(
                labels=list(breakdown.keys()),
                values=list(breakdown.values()),
                marker=dict(colors=[SF_BLUE, SF_LIGHT_BLUE, SF_GREEN, SF_ORANGE])
            )])
            fig.update_layout(
                title="Program Cost Breakdown",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("ROI Estimates by Department")
        roi_data = impact.get("roi_estimates", {})

        roi_items = [k for k in roi_data.keys() if k != "total"]
        col1, col2, col3, col4 = st.columns(4)

        for idx, key in enumerate(roi_items):
            col = [col1, col2, col3, col4][idx]
            with col:
                data = roi_data[key]
                st.markdown(f"### {data.get('metric', key)}")
                st.metric(
                    "Annual Impact",
                    f"${data.get('annual_impact_value', 0):,.0f}",
                    f"{data.get('roi_pct', 0):.1f}% ROI"
                )
                st.caption(f"Payback: {data.get('payback_months', 0):.1f} months")

        st.divider()
        total_roi = roi_data.get("total", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Annual Impact Value", f"${total_roi.get('annual_impact_value', 0):,.0f}")
        with col2:
            st.metric("Program ROI", f"{total_roi.get('roi_pct', 0):.0f}%")
        with col3:
            st.metric("Program Payback Period", f"{total_roi.get('payback_months', 0):.1f} months")

        roi_chart_data = []
        for key in roi_items:
            data = roi_data[key]
            roi_chart_data.append({
                "Department": data.get("metric", key).replace(" Impact", ""),
                "ROI %": data.get("roi_pct", 0),
                "Annual Impact": data.get("annual_impact_value", 0) / 1000
            })

        roi_df = pd.DataFrame(roi_chart_data)
        fig = px.bar(
            roi_df,
            x="Department",
            y="ROI %",
            color="Annual Impact",
            color_continuous_scale="Viridis",
            title="ROI % by Department",
            labels={"Annual Impact": "Annual Impact ($K)"}
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 10: OPERATIONAL HEALTH
# ============================================================================

with tab10:
    st.header("Operational Health")
    health = fetch_operational_health()

    if health:
        st.subheader("Content Freshness")
        freshness = health.get("content_freshness", {})
        courses = freshness.get("courses", [])

        if courses:
            freshness_df = pd.DataFrame([
                {
                    "Course": c.get("title", ""),
                    "Platform": c.get("platform", "").title(),
                    "Last Updated": c.get("last_updated", ""),
                    "Days Ago": c.get("days_since_update", 0)
                }
                for c in courses
            ])
            st.dataframe(freshness_df, use_container_width=True, hide_index=True)
            st.metric("Average Days Since Update", f"{freshness.get('average_days_since_update', 0):.0f}")

        st.divider()

        st.subheader("Content Library Health")
        library = health.get("content_library", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Courses", library.get("total_courses", 0))
        with col2:
            st.metric("Total Learning Hours", f"{library.get('total_learning_hours', 0):,}")
        with col3:
            st.metric("Actively Used", f"{library.get('actively_used_pct', 0):.1f}%")
        with col4:
            st.metric("Stale Content", f"{library.get('stale_pct', 0):.1f}%")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Content Distribution by Platform**")
            platform_data = library.get("by_platform", {})
            platform_rows = []
            for platform, data in platform_data.items():
                platform_rows.append({
                    "Platform": platform.title(),
                    "Total": data.get("total", 0),
                    "Active": data.get("active", 0),
                    "Active %": f"{data.get('active_pct', 0):.1f}%"
                })
            platform_df = pd.DataFrame(platform_rows)
            st.dataframe(platform_df, use_container_width=True, hide_index=True)

        with col2:
            usage_data = {
                "Actively Used": library.get("actively_used_count", 0),
                "Moderately Used": library.get("moderately_used_count", 0),
                "Stale": library.get("stale_count", 0)
            }
            fig = go.Figure(data=[go.Pie(
                labels=list(usage_data.keys()),
                values=list(usage_data.values()),
                marker=dict(colors=[SF_GREEN, "#FFB81C", "#E74C3C"])
            )])
            fig.update_layout(
                title="Content Usage Status",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("Facilitator/Instructor Ratings")
        ratings = health.get("facilitator_ratings", {})
        instructors = ratings.get("instructors", [])

        if instructors:
            ratings_df = pd.DataFrame([
                {
                    "Instructor": i.get("name", ""),
                    "Platform": i.get("platform", "").title(),
                    "Avg Rating": f"{i.get('avg_rating', 0):.1f}/5.0",
                    "Reviews": i.get("reviews", 0)
                }
                for i in instructors
            ])
            st.dataframe(ratings_df, use_container_width=True, hide_index=True)
            st.metric("Overall Average Rating", f"{ratings.get('overall_avg_rating', 0):.1f}/5.0", f"{ratings.get('total_reviews', 0)} reviews")

        st.divider()

        st.subheader("SLA Performance")
        slas = health.get("sla_metrics", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            custom = slas.get("custom_training_requests", {})
            st.markdown("**Custom Training Requests**")
            st.metric("Avg Days to Delivery", f"{custom.get('avg_days_to_delivery', 0)}", delta=f"{custom.get('sla_met_pct', 0):.0f}% on-time")
            st.caption(f"Target: {custom.get('sla_target_days', 0)} days")

        with col2:
            updates = slas.get("content_update_requests", {})
            st.markdown("**Content Update Requests**")
            st.metric("Avg Days to Publish", f"{updates.get('avg_days_to_publish', 0)}", delta=f"{updates.get('sla_met_pct', 0):.0f}% on-time")
            st.caption(f"Pending: {updates.get('pending_count', 0)} requests")

        with col3:
            support = slas.get("support_ticket_response", {})
            st.markdown("**Support Tickets**")
            st.metric("Avg Response Time", f"{support.get('avg_response_hours', 0):.1f}h", delta=f"{support.get('sla_met_pct', 0):.0f}% on-time")
            st.caption(f"Target: {support.get('sla_target_hours', 0)}h")

        trend_data = slas.get("monthly_trend", [])
        if trend_data:
            trend_df = pd.DataFrame(trend_data)
            fig = px.line(
                trend_df,
                x="month",
                y="sla_met_pct",
                markers=True,
                title="SLA Compliance Trend (Custom Training)",
                labels={"sla_met_pct": "SLA Met %", "month": "Month"},
                line_shape="linear"
            )
            fig.update_layout(height=300, hovermode="x unified")
            fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="Target: 95%")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("Training Backlog")
        backlog = health.get("training_backlog", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requested", backlog.get("total_requested", 0))
        with col2:
            st.metric("In Progress", backlog.get("in_progress", 0))
        with col3:
            st.metric("Queued", backlog.get("queued", 0))
        with col4:
            st.metric("On Hold", backlog.get("on_hold", 0))

        col1, col2 = st.columns(2)
        with col1:
            priority = backlog.get("by_priority", {})
            fig = px.pie(
                values=list(priority.values()),
                names=list(priority.keys()),
                title="Backlog by Priority",
                color_discrete_map={"high": "#E74C3C", "medium": "#F39C12", "low": "#F1C40F"}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            btype = backlog.get("by_type", {})
            fig = px.pie(
                values=list(btype.values()),
                names=list(btype.keys()),
                title="Backlog by Type",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        oldest = backlog.get("oldest_request", {})
        if oldest:
            st.warning(f"⏰ **Oldest Request**: {oldest.get('title', '')} (requested {oldest.get('days_in_backlog', 0)} days ago)")

        st.subheader("Recently Completed Trainings")
        completed = backlog.get("recently_completed", [])
        if completed:
            completed_df = pd.DataFrame([
                {
                    "Training": c.get("title", ""),
                    "Completed": c.get("completed_date", ""),
                    "Days to Build": c.get("days_to_build", 0)
                }
                for c in completed
            ])
            st.dataframe(completed_df, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 11: TRENDS & COHORT VIEWS
# ============================================================================

with tab11:
    st.header("Trends & Cohort Views")
    trends = fetch_trends_cohorts()

    if trends:
        st.subheader("Month-over-Month Completion Trends")
        monthly = trends.get("monthly_trends", [])

        if monthly:
            monthly_df = pd.DataFrame(monthly)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_df["month"],
                y=monthly_df["enrollments"],
                mode="lines+markers",
                name="Enrollments",
                line=dict(color=SF_BLUE, width=2),
                marker=dict(size=8)
            ))
            fig.add_trace(go.Scatter(
                x=monthly_df["month"],
                y=monthly_df["completions"],
                mode="lines+markers",
                name="Completions",
                line=dict(color=SF_GREEN, width=2),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Enrollments vs Completions Trend",
                xaxis_title="Month",
                yaxis_title="Count",
                hovermode="x unified",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            fig = px.line(
                monthly_df,
                x="month",
                y="completion_rate",
                markers=True,
                title="Monthly Completion Rate Trend",
                labels={"completion_rate": "Completion Rate %", "month": "Month"},
                line_shape="linear"
            )
            fig.update_layout(height=350, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("Cohort Comparison")
        cohort_data = trends.get("cohort_analysis", {})

        st.markdown("**By Hire Cohort**")
        hire_cohorts = cohort_data.get("by_hire_cohort", [])
        if hire_cohorts:
            hire_df = pd.DataFrame(hire_cohorts)
            hire_display = hire_df.copy()
            hire_display["completion_rate"] = hire_display["avg_completion_rate"].apply(lambda x: f"{x:.1f}%")
            hire_display = hire_display[["cohort", "learners", "enrollments", "completions", "completion_rate", "avg_time_to_first_completion"]]
            hire_display.columns = ["Cohort", "Learners", "Enrollments", "Completions", "Avg Completion Rate", "Avg Days to First Completion"]
            st.dataframe(hire_display, use_container_width=True, hide_index=True)

            fig = px.bar(
                hire_df,
                x="cohort",
                y="avg_completion_rate",
                title="Completion Rate by Hire Cohort",
                labels={"avg_completion_rate": "Completion Rate %", "cohort": "Cohort"},
                color="avg_completion_rate",
                color_continuous_scale="Viridis"
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("**By Department**")
        dept_cohorts = cohort_data.get("by_department", [])
        if dept_cohorts:
            dept_df = pd.DataFrame(dept_cohorts)
            dept_display = dept_df.copy()
            dept_display["completion_rate"] = dept_display["avg_completion_rate"].apply(lambda x: f"{x:.1f}%")
            dept_display = dept_display[["department", "learners", "enrollments", "completions", "completion_rate"]]
            dept_display.columns = ["Department", "Learners", "Enrollments", "Completions", "Avg Completion Rate"]
            st.dataframe(dept_display, use_container_width=True, hide_index=True)

            fig = px.bar(
                dept_df,
                x="department",
                y=["enrollments", "completions"],
                title="Enrollments vs Completions by Department",
                labels={"value": "Count", "variable": "Metric"},
                barmode="group"
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("Recognition Leaderboards")
        leaderboard = trends.get("leaderboard", {})

        st.info(f"ℹ️ {leaderboard.get('note', 'Recognition only, not performance evaluation')}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Top Teams by Completions**")
            top_teams = leaderboard.get("top_teams", [])
            if top_teams:
                teams_df = pd.DataFrame(top_teams)
                teams_display = teams_df.copy()
                teams_display["completion_rate"] = teams_display["completion_rate"].apply(lambda x: f"{x:.1f}%")
                teams_display = teams_display[["rank", "team", "completions", "members", "completion_rate"]]
                teams_display.columns = ["Rank", "Team", "Completions", "Members", "Completion Rate"]
                st.dataframe(teams_display, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("**Top Individual Completers**")
            top_individuals = leaderboard.get("top_individual_completers", [])
            if top_individuals:
                indiv_df = pd.DataFrame(top_individuals)
                indiv_display = indiv_df.copy()
                indiv_display = indiv_display[["rank", "name", "team", "completions", "learning_hours"]]
                indiv_display.columns = ["Rank", "Name", "Team", "Completions", "Learning Hours"]
                st.dataframe(indiv_display, use_container_width=True, hide_index=True)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🔄 Auto-refresh enabled | API: {API_BASE} | Platforms: PlusPlus • Trailhead • Pluralsight • O'Reilly")

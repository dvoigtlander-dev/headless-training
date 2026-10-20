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

# Helper function for styled collapsible section headers
def section_header(number, title, emoji=""):
    return st.expander(f"{emoji} {number} {title}", expanded=True)

# Page config
st.set_page_config(
    page_title="Salesforce Training Analytics",
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
    "plusplus": "#2D7A4A",      # Dark Green
    "trailhead": "#9DB93F",     # Olive Green
    "pluralsight": "#F59E42",   # Orange
    "oreilly": "#FF6B7A"        # Coral Red
}

# ============================================================================
# CONFIGURATION
# ============================================================================

# Joe Inzerillo's departments
JOE_DEPARTMENTS = ["Engineering", "Product", "DevOps", "Platform"]

# API endpoints
API_BASE = "http://localhost:8008"

# ============================================================================
# API CLIENTS
# ============================================================================

@lru_cache(maxsize=1)
def fetch_reach_participation():
    """Fetch reach and participation metrics"""
    try:
        resp = requests.get(f"{API_BASE}/api/reach-participation", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Reach & Participation API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_engagement_quality():
    """Fetch engagement quality metrics (NPS and feedback)"""
    try:
        resp = requests.get(f"{API_BASE}/api/engagement-quality", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Engagement Quality API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_all_courses():
    """Fetch courses from all platforms"""
    try:
        resp = requests.get(f"{API_BASE}/api/all-courses?limit=200", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Courses API error: {e}")
    return {"courses": [], "total": 0}

@lru_cache(maxsize=1)
def fetch_platform_stats():
    """Fetch aggregated stats from all platforms"""
    try:
        resp = requests.get(f"{API_BASE}/api/stats", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Stats API error: {e}")
    return {"platforms": {}, "totals": {}}

def fetch_department_stats(department):
    """Fetch stats for a specific department"""
    try:
        resp = requests.get(f"{API_BASE}/api/departments/{department}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Department stats error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_knowledge_outcomes():
    """Fetch knowledge & skill outcomes metrics"""
    try:
        resp = requests.get(f"{API_BASE}/api/knowledge-outcomes", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Knowledge outcomes API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_business_impact():
    """Fetch business impact and ROI metrics"""
    try:
        resp = requests.get(f"{API_BASE}/api/business-impact", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Business impact API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_operational_health():
    """Fetch operational health metrics"""
    try:
        resp = requests.get(f"{API_BASE}/api/operational-health", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"Operational health API error: {e}")
    return {}

@lru_cache(maxsize=1)
def fetch_trends_cohorts():
    """Fetch trends and cohort analysis"""
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

# Department selector
selected_depts = st.sidebar.multiselect(
    "Joe Inzerillo's Departments",
    JOE_DEPARTMENTS,
    default=JOE_DEPARTMENTS
)

# Date range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=90))
with col2:
    end_date = st.date_input("End Date", datetime.now())

st.sidebar.divider()

# Platform toggles
st.sidebar.subheader("📚 Platforms")
show_plusplus = st.sidebar.checkbox("PlusPlus (Learn++)", value=True)
show_trailhead = st.sidebar.checkbox("Trailhead", value=True)
show_pluralsight = st.sidebar.checkbox("Pluralsight", value=True)
show_oreilly = st.sidebar.checkbox("O'Reilly", value=True)

st.sidebar.divider()

# Refresh button
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("Salesforce Logo.jpg", width=200)

st.markdown(f"<h1 style='text-align: center; color: {SF_BLUE}; font-size: 2.5em; margin-top: 0;'>Training Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {SF_DARK_BLUE}; font-size: 1.1em;'><strong>Period:</strong> {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SECTION 1: REACH & PARTICIPATION
# ============================================================================

with section_header("1️⃣", "Reach & Participation", "📊"):
    reach_data = fetch_reach_participation()

    if reach_data:
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📋 Total Enrollments", f"{reach_data.get('total_enrollments', 0):,}")
        col2.metric("✅ Completions", f"{reach_data.get('total_completions', 0):,}")
        col3.metric("📊 Completion Rate", f"{reach_data.get('completion_rates', {}).get('overall', 0):.1f}%")
        col4.metric("🎤 Live Sessions", reach_data.get('live_sessions', {}).get('total', 0))

        # Enrollment & completion by platform
        st.subheader("Enrollment & Completion by Platform")
        enroll_by_platform = reach_data.get('enrollment_by_platform', {})
        if enroll_by_platform:
            col1, col2, col3 = st.columns(3)

            # Bar chart - Enrollments
            with col1:
                enroll_platforms = list(enroll_by_platform.keys())
                enroll_values = list(enroll_by_platform.values())

                # Map platform names to their colors
                enroll_colors = []
                for platform in enroll_platforms:
                    platform_lower = platform.lower()
                    if platform_lower == "plusplus":
                        enroll_colors.append(PLATFORM_COLORS["plusplus"])
                    elif platform_lower == "trailhead":
                        enroll_colors.append(PLATFORM_COLORS["trailhead"])
                    elif platform_lower == "pluralsight":
                        enroll_colors.append(PLATFORM_COLORS["pluralsight"])
                    elif platform_lower == "oreilly":
                        enroll_colors.append(PLATFORM_COLORS["oreilly"])

                fig_enroll = go.Figure(data=[
                    go.Bar(x=enroll_platforms, y=enroll_values, marker=dict(color=enroll_colors))
                ])
                fig_enroll.update_layout(
                    title="Total Enrollments by Platform",
                    xaxis_title="Platform",
                    yaxis_title="Enrollments",
                    height=350,
                    showlegend=False,
                    title_font_color=SF_DARK_BLUE,
                    xaxis_title_font_color=SF_DARK_BLUE,
                    yaxis_title_font_color=SF_DARK_BLUE
                )
                st.plotly_chart(fig_enroll, use_container_width=True)

            # Completion rates
            with col2:
                completion_by_platform = reach_data.get('completion_rates', {})
                platforms = [k for k in completion_by_platform.keys() if k != 'overall']
                rates = [completion_by_platform[p] for p in platforms]

                fig_completion = px.bar(
                    x=platforms,
                    y=rates,
                    labels={'x': 'Platform', 'y': 'Completion Rate (%)'},
                    title="Completion Rate by Platform",
                    color=rates,
                    color_continuous_scale=[[0, SF_ORANGE], [0.5, "#FFB81C"], [1, SF_GREEN]]
                )
                fig_completion.update_layout(
                    height=350,
                    showlegend=False,
                    title_font_color=SF_DARK_BLUE,
                    xaxis_title_font_color=SF_DARK_BLUE,
                    yaxis_title_font_color=SF_DARK_BLUE
                )
                st.plotly_chart(fig_completion, use_container_width=True)

            # Platform summary table
            with col3:
                platform_summary = []
                for platform, enrollments in enroll_by_platform.items():
                    completion_rate = completion_by_platform.get(platform, 0)
                    completion_count = int(enrollments * completion_rate / 100)
                    platform_summary.append({
                        "Platform": platform.capitalize(),
                        "Enrollments": enrollments,
                        "Completions": completion_count,
                        "Rate": f"{completion_rate:.1f}%"
                    })
                summary_df = pd.DataFrame(platform_summary)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Top courses
        st.subheader("Top 5 Courses by Enrollment")
        enrollment_by_course = reach_data.get('enrollment_by_course', [])
        if enrollment_by_course:
            courses_df = pd.DataFrame(enrollment_by_course)
            st.dataframe(
                courses_df[['course', 'platform', 'enrollments']].head(5),
                use_container_width=True,
                hide_index=True
            )

        # Live sessions & attendance
        st.subheader("Live Sessions Attendance")
        live_data = reach_data.get('live_sessions', {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sessions", live_data.get('total_sessions', 0))
        col2.metric("Sessions Attended", live_data.get('attended', 0))
        col3.metric("Attendance Rate", f"{live_data.get('attendance_rate', 0):.1f}%")

        # Department engagement
        st.subheader("Engagement by Department")
        dept_engagement = reach_data.get('engagement_by_department', {})
        if dept_engagement:
            dept_data = []
            for dept, metrics in dept_engagement.items():
                dept_data.append({
                    'Department': dept,
                    'Enrollments': metrics['enrollments'],
                    'Completions': metrics['completions'],
                    'Completion Rate': f"{metrics['completion_rate']:.1f}%"
                })

            dept_df = pd.DataFrame(dept_data)
            st.dataframe(dept_df, use_container_width=True, hide_index=True)

st.divider()

# ============================================================================
# SECTION 2: ENGAGEMENT QUALITY
# ============================================================================

with section_header("2️⃣", "Engagement Quality", "⭐"):
    quality_data = fetch_engagement_quality()

    if quality_data:
        # NPS metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 Overall NPS", quality_data.get('nps_overall', 0))
        col2.metric("😊 Positive Feedback", f"{quality_data.get('feedback_themes', {}).get('positive', {}).get('percentage', 0)}%")
        col3.metric("😐 Negative Feedback", f"{quality_data.get('feedback_themes', {}).get('negative', {}).get('percentage', 0)}%")
        col4.metric("🚫 Blockers", f"{quality_data.get('feedback_themes', {}).get('blocker', {}).get('percentage', 0)}%")

        # NPS by Platform
        st.subheader("NPS Score by Platform")
        nps_by_platform = quality_data.get('nps_by_platform', {})
        if nps_by_platform:
            col1, col2 = st.columns(2)

            # NPS Gauge Chart
            with col1:
                platforms = list(nps_by_platform.keys())
                scores = list(nps_by_platform.values())

                # Map platform names to their colors
                bar_colors = []
                for platform in platforms:
                    platform_lower = platform.lower()
                    if platform_lower == "plusplus":
                        bar_colors.append(PLATFORM_COLORS["plusplus"])
                    elif platform_lower == "trailhead":
                        bar_colors.append(PLATFORM_COLORS["trailhead"])
                    elif platform_lower == "pluralsight":
                        bar_colors.append(PLATFORM_COLORS["pluralsight"])
                    elif platform_lower == "oreilly":
                        bar_colors.append(PLATFORM_COLORS["oreilly"])

                fig_nps = go.Figure(data=[
                    go.Bar(x=platforms, y=scores, marker=dict(color=bar_colors))
                ])
                fig_nps.update_layout(
                    title="NPS by Platform",
                    xaxis_title="Platform",
                    yaxis_title="NPS Score",
                    height=350,
                    showlegend=False,
                    title_font_color=SF_DARK_BLUE,
                    xaxis_title_font_color=SF_DARK_BLUE,
                    yaxis_title_font_color=SF_DARK_BLUE
                )
                st.plotly_chart(fig_nps, use_container_width=True)

            # Department NPS
            with col2:
                dept_nps = quality_data.get('satisfaction_by_department', {})
                depts = list(dept_nps.keys())
                dept_scores = [dept_nps[d].get('nps', 0) for d in depts]

                fig_dept_nps = px.bar(
                    x=depts,
                    y=dept_scores,
                    labels={'x': 'Department', 'y': 'NPS Score'},
                    title="NPS by Department",
                    color=dept_scores,
                    color_continuous_scale=[[0, SF_ORANGE], [0.5, "#FFB81C"], [1, SF_GREEN]]
                )
                fig_dept_nps.update_layout(
                    height=350,
                    showlegend=False,
                    title_font_color=SF_DARK_BLUE,
                    xaxis_title_font_color=SF_DARK_BLUE,
                    yaxis_title_font_color=SF_DARK_BLUE
                )
                st.plotly_chart(fig_dept_nps, use_container_width=True)

        # Feedback Themes
        st.subheader("Feedback Themes Distribution")
        feedback_themes = quality_data.get('feedback_themes', {})

        col1, col2, col3 = st.columns(3)

        # Positive feedback
        with col1:
            st.markdown(f"<h4 style='color: {SF_GREEN};'>✅ Positive ({feedback_themes.get('positive', {}).get('percentage', 0)}%)</h4>", unsafe_allow_html=True)
            positive_tags = feedback_themes.get('positive', {}).get('tags', [])
            for tag in positive_tags[:5]:
                st.write(f"• {tag.get('tag')} ({tag.get('count')})")

        # Negative feedback
        with col2:
            st.markdown(f"<h4 style='color: #FFB81C;'>😐 Negative ({feedback_themes.get('negative', {}).get('percentage', 0)}%)</h4>", unsafe_allow_html=True)
            negative_tags = feedback_themes.get('negative', {}).get('tags', [])
            for tag in negative_tags[:5]:
                st.write(f"• {tag.get('tag')} ({tag.get('count')})")

        # Blockers
        with col3:
            st.markdown(f"<h4 style='color: {SF_ORANGE};'>🚫 Blockers ({feedback_themes.get('blocker', {}).get('percentage', 0)}%)</h4>", unsafe_allow_html=True)
            blocker_tags = feedback_themes.get('blocker', {}).get('tags', [])
            for tag in blocker_tags[:5]:
                st.write(f"• {tag.get('tag')} ({tag.get('count')})")

        # Top performers and areas for improvement
        st.subheader("Course Performance")
        perf_col1, perf_col2 = st.columns(2)

        with perf_col1:
            st.write("**🏆 Top Performers (High NPS)**")
            top_performers = quality_data.get('top_performers', [])
            for course in top_performers[:3]:
                st.write(f"• {course.get('course')} - NPS: {course.get('nps')} ({course.get('platform')})")

        with perf_col2:
            st.write("**⚠️ Areas for Improvement (Low NPS)**")
            areas = quality_data.get('areas_for_improvement', [])
            for course in areas[:3]:
                st.write(f"• {course.get('course')} - NPS: {course.get('nps')}")
                for issue in course.get('issues', [])[:2]:
                    st.write(f"  - {issue}")

st.divider()

# ============================================================================
# SECTION 3: OVERALL METRICS
# ============================================================================

with section_header("3️⃣", "Overall Training Metrics", "📈"):
    stats = fetch_platform_stats()
    totals = stats.get("totals", {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📚 Total Courses", totals.get("total_courses", 0))
    col2.metric("👥 Total Enrollments", totals.get("total_enrollments", 0))
    col3.metric("💻 Active Users", totals.get("total_active_users", 0))
    col4.metric("📊 Platforms", "4")

st.divider()

# ============================================================================
# SECTION 4: PLATFORM BREAKDOWN
# ============================================================================

with section_header("4️⃣", "Training Platform Distribution", "🌐"):
    platforms_data = stats.get("platforms", {})
    platform_names = []
    enrollments = []
    active_users = []

    if show_plusplus and "plusplus" in platforms_data:
        p = platforms_data["plusplus"]
        platform_names.append("PlusPlus")
        enrollments.append(p.get("enrollments", 0))
        active_users.append(p.get("active_users", 0))

    if show_trailhead and "trailhead" in platforms_data:
        p = platforms_data["trailhead"]
        platform_names.append("Trailhead")
        enrollments.append(p.get("enrollments", 0))
        active_users.append(p.get("active_users", 0))

    if show_pluralsight and "pluralsight" in platforms_data:
        p = platforms_data["pluralsight"]
        platform_names.append("Pluralsight")
        enrollments.append(p.get("enrollments", 0))
        active_users.append(p.get("active_users", 0))

    if show_oreilly and "oreilly" in platforms_data:
        p = platforms_data["oreilly"]
        platform_names.append("O'Reilly")
        enrollments.append(p.get("enrollments", 0))
        active_users.append(p.get("active_users", 0))

    col1, col2 = st.columns(2)

    # Enrollments pie chart
    with col1:
        # Map platform names to their colors
        pie_colors = []
        for name in platform_names:
            name_lower = name.lower()
            if name_lower == "plusplus":
                pie_colors.append(PLATFORM_COLORS["plusplus"])
            elif name_lower == "trailhead":
                pie_colors.append(PLATFORM_COLORS["trailhead"])
            elif name_lower == "pluralsight":
                pie_colors.append(PLATFORM_COLORS["pluralsight"])
            elif name_lower == "o'reilly":
                pie_colors.append(PLATFORM_COLORS["oreilly"])

        fig_pie = go.Figure(data=[go.Pie(labels=platform_names, values=enrollments, marker=dict(colors=pie_colors))])
        fig_pie.update_layout(
            title="Enrollments by Platform",
            height=400,
            title_font_color=SF_DARK_BLUE,
            font=dict(color=SF_DARK_BLUE)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Active users pie chart
    with col2:
        # Map platform names to their colors
        pie_colors = []
        for name in platform_names:
            name_lower = name.lower()
            if name_lower == "plusplus":
                pie_colors.append(PLATFORM_COLORS["plusplus"])
            elif name_lower == "trailhead":
                pie_colors.append(PLATFORM_COLORS["trailhead"])
            elif name_lower == "pluralsight":
                pie_colors.append(PLATFORM_COLORS["pluralsight"])
            elif name_lower == "o'reilly":
                pie_colors.append(PLATFORM_COLORS["oreilly"])

        fig_pie2 = go.Figure(data=[go.Pie(labels=platform_names, values=active_users, marker=dict(colors=pie_colors))])
        fig_pie2.update_layout(
            title="Active Users by Platform",
            height=400,
            title_font_color=SF_DARK_BLUE,
            font=dict(color=SF_DARK_BLUE)
        )
        st.plotly_chart(fig_pie2, use_container_width=True)

st.divider()

# ============================================================================
# SECTION 5: PLATFORM COMPARISON TABLE
# ============================================================================

with section_header("5️⃣", "Platform Comparison", "⚖️"):
    platform_comparison = []
    for key, platform in platforms_data.items():
        if key == "totals":
            continue

        platform_comparison.append({
            "Platform": platform.get("name", key.title()),
            "Courses": platform.get("courses", platform.get("modules", 0)),
            "Enrollments": platform.get("enrollments", 0),
            "Active Users": platform.get("active_users", 0),
        })

    if platform_comparison:
        comp_df = pd.DataFrame(platform_comparison)
        st.dataframe(comp_df, use_container_width=True)

st.divider()

# ============================================================================
# SECTION 6: DEPARTMENT METRICS
# ============================================================================

with section_header("6️⃣", "Joe Inzerillo's Department Metrics", "👥"):
    if selected_depts:
        dept_tabs = st.tabs(selected_depts)

        for idx, dept in enumerate(selected_depts):
            with dept_tabs[idx]:
                dept_stats = fetch_department_stats(dept)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("👥 Active Learners", dept_stats.get("metrics", {}).get("active_learners", 0))
                col2.metric("📋 Enrollment Rate", f"{dept_stats.get('metrics', {}).get('enrollment_rate', 0)}%")
                col3.metric("✅ Completion Rate", f"{dept_stats.get('metrics', {}).get('completion_rate', 0)}%")
                col4.metric("⏱️ Avg Time (days)", f"{dept_stats.get('metrics', {}).get('avg_time_to_complete', 0)}")

                # Platform breakdown for this department
                breakdown = dept_stats.get("platformBreakdown", {})
                if breakdown:
                    st.subheader(f"Platform Distribution - {dept}")

                    # Map platform names to their colors
                    breakdown_colors = []
                    for platform in breakdown.keys():
                        platform_lower = platform.lower()
                        if platform_lower == "plusplus":
                            breakdown_colors.append(PLATFORM_COLORS["plusplus"])
                        elif platform_lower == "trailhead":
                            breakdown_colors.append(PLATFORM_COLORS["trailhead"])
                        elif platform_lower == "pluralsight":
                            breakdown_colors.append(PLATFORM_COLORS["pluralsight"])
                        elif platform_lower == "oreilly":
                            breakdown_colors.append(PLATFORM_COLORS["oreilly"])

                    fig_breakdown = go.Figure(data=[
                        go.Bar(
                            x=list(breakdown.keys()),
                            y=list(breakdown.values()),
                            marker_color=breakdown_colors
                        )
                    ])
                    fig_breakdown.update_layout(
                        title=f"{dept} - Courses by Platform",
                        xaxis_title="Platform",
                        yaxis_title="Number of Courses",
                        height=350,
                        title_font_color=SF_DARK_BLUE,
                        xaxis_title_font_color=SF_DARK_BLUE,
                        yaxis_title_font_color=SF_DARK_BLUE
                    )
                    st.plotly_chart(fig_breakdown, use_container_width=True)

                # Trend
                trend = dept_stats.get("trend", {})
                if trend:
                    st.subheader("Enrollment Trend")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("This Week", trend.get("this_week", 0))
                    col2.metric("Last Week", trend.get("last_week", 0))
                    col3.metric("Change", trend.get("change", "N/A"))

st.divider()

# ============================================================================
# SECTION 7: ALL COURSES
# ============================================================================

with section_header("7️⃣", "All Available Courses", "📚"):
    courses_data = fetch_all_courses()
    courses = courses_data.get("courses", [])

    if courses:
        # Filter by selected platform
        selected_platforms = []
        if show_plusplus:
            selected_platforms.append("PlusPlus")
        if show_trailhead:
            selected_platforms.append("Trailhead")
        if show_pluralsight:
            selected_platforms.append("Pluralsight")
        if show_oreilly:
            selected_platforms.append("O'Reilly")

        filtered_courses = [c for c in courses if c.get("platform") in selected_platforms]

        # Create dataframe
        courses_df = pd.DataFrame([
            {
                "Platform": c.get("platform", "Unknown"),
                "Course": c.get("name", "Unknown"),
                "Type": c.get("type", "course"),
            }
            for c in filtered_courses
        ])

        st.dataframe(courses_df, use_container_width=True)
        st.caption(f"Showing {len(filtered_courses)} courses across selected platforms")
    else:
        st.info("No course data available yet")

st.divider()

# ============================================================================
# SECTION 8: KNOWLEDGE & SKILL OUTCOMES
# ============================================================================

with section_header("8️⃣", "Knowledge & Skill Outcomes", "🎯"):
    outcomes = fetch_knowledge_outcomes()

    if outcomes:
        # Assessment Score Deltas
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

        # Certification Pass Rates
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

        # Skill Proficiency Self-Assessment
        st.subheader("Skill Proficiency Self-Assessment (Before/After)")
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

        # Manager-Rated Skill Application
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

                        # Create pie chart
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
# SECTION 9: BUSINESS IMPACT
# ============================================================================

with section_header("9️⃣", "Business Impact", "💼"):
    impact = fetch_business_impact()

    if impact:
        # Performance Correlations
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

        # Cost Analysis
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

        # Cost Breakdown Pie Chart
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

        # ROI Estimates
        st.subheader("ROI Estimates by Department")
        roi_data = impact.get("roi_estimates", {})

        # ROI Summary Cards
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

        # Total ROI Highlight
        st.divider()
        total_roi = roi_data.get("total", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Annual Impact Value", f"${total_roi.get('annual_impact_value', 0):,.0f}")
        with col2:
            st.metric("Program ROI", f"{total_roi.get('roi_pct', 0):.0f}%")
        with col3:
            st.metric("Program Payback Period", f"{total_roi.get('payback_months', 0):.1f} months")

        # ROI by Department Bar Chart
        roi_chart_data = []
        for key in roi_items:
            data = roi_data[key]
            roi_chart_data.append({
                "Department": data.get("metric", key).replace(" Impact", ""),
                "ROI %": data.get("roi_pct", 0),
                "Annual Impact": data.get("annual_impact_value", 0) / 1000  # In thousands
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
# SECTION 10: OPERATIONAL HEALTH
# ============================================================================

with section_header("🔟", "Operational Health", "⚙️"):
    health = fetch_operational_health()

    if health:
        # Content Freshness
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

        # Content Library Size & Usage
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

        # Content by Platform
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
            # Content Usage Pie Chart
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

        # Facilitator Ratings
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

        # SLA Metrics
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

        # SLA Trend Chart
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

        # Training Backlog
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

        # Backlog by Priority and Type
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

        # Oldest Request Alert
        oldest = backlog.get("oldest_request", {})
        if oldest:
            st.warning(f"⏰ **Oldest Request**: {oldest.get('title', '')} (requested {oldest.get('days_in_backlog', 0)} days ago)")

        # Recently Completed
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
# SECTION 11: TRENDS & COHORT VIEWS
# ============================================================================

with section_header("🕐", "Trends & Cohort Views", "📈"):
    trends = fetch_trends_cohorts()

    if trends:
        # Month-over-Month Completion Trends
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

            # Completion Rate Trend
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

        # Cohort Analysis
        st.subheader("Cohort Comparison")
        cohort_data = trends.get("cohort_analysis", {})

        # Hire Cohort Comparison
        st.markdown("**By Hire Cohort**")
        hire_cohorts = cohort_data.get("by_hire_cohort", [])
        if hire_cohorts:
            hire_df = pd.DataFrame(hire_cohorts)
            hire_display = hire_df.copy()
            hire_display["completion_rate"] = hire_display["avg_completion_rate"].apply(lambda x: f"{x:.1f}%")
            hire_display = hire_display[["cohort", "learners", "enrollments", "completions", "completion_rate", "avg_time_to_first_completion"]]
            hire_display.columns = ["Cohort", "Learners", "Enrollments", "Completions", "Avg Completion Rate", "Avg Days to First Completion"]
            st.dataframe(hire_display, use_container_width=True, hide_index=True)

            # Cohort Comparison Chart
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

        # Department Comparison
        st.markdown("**By Department**")
        dept_cohorts = cohort_data.get("by_department", [])
        if dept_cohorts:
            dept_df = pd.DataFrame(dept_cohorts)
            dept_display = dept_df.copy()
            dept_display["completion_rate"] = dept_display["avg_completion_rate"].apply(lambda x: f"{x:.1f}%")
            dept_display = dept_display[["department", "learners", "enrollments", "completions", "completion_rate"]]
            dept_display.columns = ["Department", "Learners", "Enrollments", "Completions", "Avg Completion Rate"]
            st.dataframe(dept_display, use_container_width=True, hide_index=True)

            # Department Comparison Chart
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

        # Leaderboards
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

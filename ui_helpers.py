"""Shared UI helpers for Streamlit app."""

import os
from pathlib import Path

from PIL import Image, ImageOps
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def load_custom_css() -> None:
    css_path = Path(__file__).parent / "assets" / "custom.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def create_gauge_chart(score: int, title: str, color: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": title,
                "font": {"size": 16, "color": "#0F172A", "weight": "bold", "family": "Inter"},
            },
            gauge={
                "axis": {"range": [0, 10], "tickwidth": 1.5, "tickcolor": "#0F172A"},
                "bar": {"color": color, "thickness": 0.75},
                "bgcolor": "#E2E8F0",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 4], "color": "#FEE2E2"},
                    {"range": [4, 7], "color": "#FEF08A"},
                    {"range": [7, 10], "color": "#DCFCE3"},
                ],
            },
        )
    )
    fig.update_layout(
        height=220,
        margin=dict(l=15, r=15, t=45, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A"),
    )
    return fig


def render_score_breakdown(breakdown: dict) -> None:
    if not breakdown:
        return
    st.markdown("**Score breakdown**")
    cols = st.columns(4)
    labels = [
        ("Visual hierarchy", "visual_hierarchy"),
        ("Color psychology", "color_psychology"),
        ("Message clarity", "message_clarity"),
        ("Audience fit", "audience_fit"),
    ]
    for col, (label, key) in zip(cols, labels):
        with col:
            st.metric(label, breakdown.get(key, "—"))


def render_color_chart(colors: list[dict]) -> None:
    if not colors:
        return
    st.markdown("**Color palette analytics**")
    fig = px.bar(
        x=[c["name"] for c in colors],
        y=[c["coverage_pct"] for c in colors],
        color=[c["psychology"] for c in colors],
        labels={"x": "Color", "y": "Coverage %"},
        title="Dominant colors by pixel coverage",
    )
    fig.update_layout(showlegend=True, height=320, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    for c in colors:
        st.caption(f"{c['hex']} · {c['name']} · {c['coverage_pct']}% · {c['psychology']}")


def render_wcag_badge(wcag: dict) -> None:
    passed = wcag.get("wcag_aa_pass")
    ratio = wcag.get("min_contrast_ratio")
    if passed is True:
        st.markdown(
            f"<span class='badge-wcag-pass'>WCAG AA (heuristic): Pass</span> "
            f"<small>min contrast {ratio}</small>",
            unsafe_allow_html=True,
        )
    elif passed is False:
        st.markdown(
            f"<span class='badge-wcag-fail'>WCAG AA (heuristic): Review</span> "
            f"<small>min contrast {ratio}</small>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("WCAG: no text regions detected for contrast check.")


def render_audit_result(res: dict, vision_data: dict) -> None:
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(
            create_gauge_chart(res["design_score"], "Design Score", "#0EA5E9"),
            use_container_width=True,
        )
    with g2:
        st.plotly_chart(
            create_gauge_chart(res["business_score"], "Business Score", "#10B981"),
            use_container_width=True,
        )

    render_score_breakdown(res.get("score_breakdown", {}))
    render_wcag_badge(vision_data.get("wcag", {}))

    if vision_data.get("color_insight"):
        st.info(vision_data["color_insight"])

    render_color_chart(vision_data.get("color_analytics", []))

    st.markdown(
        f"<div class='ai-rec-box'><strong>Recommendation:</strong><br><br>{res['actionable_feedback']}</div>",
        unsafe_allow_html=True,
    )
    if res.get("campaign_type_guess"):
        st.caption(f"Campaign type: {res['campaign_type_guess']}")

    with st.expander("Vision & OCR details"):
        st.markdown(
            f"- **People:** {vision_data['person_count']}\n"
            f"- **Colors:** {vision_data['dominant_colors']}\n"
            f"- **Raw OCR:** {vision_data['raw_ocr_text']}\n"
            f"- **Cleaned:** {res['corrected_text']}\n"
            f"- **Processing:** {vision_data.get('processing_ms', '—')} ms"
        )


def open_uploaded_image(uploaded_file) -> Image.Image:
    """Open upload and apply EXIF orientation (fixes sideways phone photos)."""
    uploaded_file.seek(0)
    return ImageOps.exif_transpose(Image.open(uploaded_file))


def save_uploaded_image(uploaded_file, path: str) -> None:
    """Save upload with correct orientation for CV pipeline."""
    img = open_uploaded_image(uploaded_file)
    img.save(path, quality=95)


def run_single_analysis(uploaded_file, temp_prefix: str = "temp_") -> tuple[dict | None, dict | None]:
    """Analyze one uploaded file; returns (llm_result, vision_data)."""
    from run_pipeline import evaluate_with_groq
    from vision_ops import analyze_image_vision

    temp_path = f"{temp_prefix}{uploaded_file.name}"
    try:
        save_uploaded_image(uploaded_file, temp_path)
        vision_data = analyze_image_vision(temp_path)
        res = evaluate_with_groq(vision_data, uploaded_file.name)
        return res, vision_data
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


__all__ = [
    "load_custom_css",
    "create_gauge_chart",
    "render_score_breakdown",
    "render_color_chart",
    "render_wcag_badge",
    "render_audit_result",
    "open_uploaded_image",
    "save_uploaded_image",
    "run_single_analysis",
]


# region agent log
def _agent_log_ui_helpers_loaded() -> None:
    import json
    import time

    log_path = Path(__file__).resolve().parent / "debug-990a14.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "990a14",
                    "hypothesisId": "A",
                    "location": "ui_helpers.py:module_end",
                    "message": "ui_helpers module loaded",
                    "data": {
                        "file": str(Path(__file__).resolve()),
                        "has_open_uploaded_image": "open_uploaded_image" in globals(),
                        "exports": __all__,
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )


_agent_log_ui_helpers_loaded()
# endregion

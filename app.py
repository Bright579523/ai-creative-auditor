import config  # noqa: F401 — loads .env for local dev

import json
import re

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

# region agent log
def _agent_log_app_import() -> None:
    import json
    import time
    from pathlib import Path

    log_path = Path(__file__).resolve().parent / "debug-990a14.log"
    try:
        from ui_helpers import open_uploaded_image as _oui  # noqa: F401

        ok, err = True, None
    except ImportError as e:
        ok, err = False, str(e)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "990a14",
                    "hypothesisId": "B",
                    "location": "app.py:pre_import",
                    "message": "ui_helpers import probe",
                    "data": {"ok": ok, "error": err},
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )


_agent_log_app_import()
# endregion

from ui_helpers import (
    load_custom_css,
    open_uploaded_image,
    render_audit_result,
    run_single_analysis,
)

BUDDHIST_ERA_YEAR_OFFSET = 543


def normalize_created_at(df: pd.DataFrame) -> pd.DataFrame:
    """Convert DuckDB Buddhist-calendar timestamps to Gregorian for pandas/plotly."""
    if "created_at" not in df.columns or df.empty:
        return df

    def to_gregorian(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return pd.NaT

        if isinstance(value, pd.Timestamp):
            ts = value
        else:
            raw = str(value)
            if "(BC)" in raw or re.match(r"2[4-9]\d{2}-", raw):
                m = re.match(r"(\d{4})-(\d{2})-(\d{2})\s*(.*)", raw.replace(" (BC)", ""))
                if m:
                    ce_year = int(m.group(1)) - BUDDHIST_ERA_YEAR_OFFSET
                    time_part = m.group(4).strip() or "00:00:00"
                    ts = pd.to_datetime(
                        f"{ce_year}-{m.group(2)}-{m.group(3)} {time_part}",
                        errors="coerce",
                    )
                else:
                    ts = pd.NaT
            else:
                ts = pd.to_datetime(raw, errors="coerce")

        if pd.isna(ts):
            return pd.NaT

        year = int(ts.year)
        if year > 2400:
            return ts.replace(year=year - BUDDHIST_ERA_YEAR_OFFSET)
        if year < 1970:
            return ts.replace(year=abs(year) + 1 - BUDDHIST_ERA_YEAR_OFFSET)
        return ts

    out = df.copy()
    out["created_at"] = out["created_at"].apply(to_gregorian)
    return out


st.set_page_config(
    page_title="AI Creative Auditor",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_custom_css()


# ─────────────────────────────────────────────
# SIDEBAR: Minimal Brand Panel
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; margin-top: 20px;">
            <span style="font-size: 3.5rem;">🛡️</span>
            <h3 style="font-family: 'Poppins', sans-serif; margin-top: 10px; color: #0F172A;">AI Creative Auditor</h3>
            <p style="font-size: 0.85rem; color: #64748B;">v2.0.0 · Local CV + Llama 3.3</p>
        </div>
        <hr style="margin: 20px 0; border: 0; border-top: 1px solid #E2E8F0;" />
        <div style="font-size: 0.88rem; color: #475569; line-height: 1.6; padding: 0 10px;">
            This platform combines local Computer Vision algorithms with large language models to evaluate ad creatives.
            <br><br>
            Navigate to the <b>Methodology & Architecture</b> tab for details on GDPR, data flows, and scoring rubrics.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _check_runtime_deps() -> list[str]:
    missing = []
    for mod, pkg in [("easyocr", "easyocr"), ("ultralytics", "ultralytics")]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    return missing


_missing = _check_runtime_deps()
if _missing:
    st.error(
        "Missing packages: **"
        + ", ".join(_missing)
        + "**. Stop Streamlit, then run: `pip install -r requirements.txt`"
    )

st.markdown(
    """
    <div class='main-header'>
        <h1>AI Creative Auditor</h1>
        <p>Marketing creative audit with Computer Vision, structured LLM scoring,
        and DuckDB analytics for data-driven campaign decisions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="background-color: #FFFFFF; border-radius: 16px; padding: 24px; box-shadow: 0 10px 40px rgba(15, 23, 42, 0.03); border: 1px solid #E2E8F0; margin-bottom: 2rem;">
        <h3 style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 1.2rem; color: #1E3A8A; margin-bottom: 12px; margin-top: 0px;">💡 Quick Start & Platform Walkthrough:</h3>
        <ol style="margin-left: 20px; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.6; padding-left: 0px;">
            <li><b>1. AI Creative Audit:</b> Upload a single ad creative to run local CV analytics (YOLOv8, EasyOCR, K-Means) and get instant structured scoring + strategic feedback.</li>
            <li><b>2. A/B Creative Comparison:</b> Upload two creative variations (e.g. text/color tweaks) to compare their scores and delta analysis side-by-side.</li>
            <li><b>3. Mock Analytics:</b> Benchmarks all analyzed creatives, segment performance, and exports DuckDB historical data to CSV for downstream marketing reports.</li>
            <li><b>4. System Architecture:</b> Review the visual flow diagram of the platform architecture, data handling, and GDPR compliance details.</li>
        </ol>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_analyze, tab_ab, tab_analytics, tab_overview = st.tabs([
    "🎯 1. AI Creative Audit", 
    "⚖️ 2. A/B Creative Comparison", 
    "📈 3. Mock Analytics", 
    "⚙️ 4. System Architecture"
])


# ─────────────────────────────────────────────
# TAB 1: Single creative analysis
# ─────────────────────────────────────────────
with tab_analyze:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A; font-weight: 800; font-family: Poppins, sans-serif; margin-bottom: 0px;'>🎯 Instant AI Creative Audit</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; margin-bottom: 25px;'>Upload a single ad creative to run local CV analytics (YOLOv8, EasyOCR, K-Means) and get instant structured scoring.</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload image",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="single_upload",
    )

    if uploaded_file:
        col_img, col_res = st.columns([1, 1.2], gap="large")
        with col_img:
            st.markdown("<div class='card-title'>Target Creative</div>", unsafe_allow_html=True)
            st.image(open_uploaded_image(uploaded_file), use_container_width=True)
            run_button = st.button("Analyze Now", type="primary", key="analyze_btn")

        with col_res:
            st.markdown("<div class='card-title'>Audit Results</div>", unsafe_allow_html=True)
            if run_button:
                with st.spinner("Running vision pipeline and LLM evaluation..."):
                    try:
                        res, vision_data = run_single_analysis(uploaded_file)
                        if res:
                            render_audit_result(res, vision_data)
                        else:
                            st.error("LLM evaluation failed. Check GROQ_API_KEY.")
                    except Exception as e:
                        st.error(f"Analysis error: {e}")
            else:
                st.info("Click **Analyze Now** to start.")


# ─────────────────────────────────────────────
# TAB 2: A/B comparison
# ─────────────────────────────────────────────
with tab_ab:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A; font-weight: 800; font-family: Poppins, sans-serif; margin-bottom: 0px;'>⚖️ A/B Creative Comparison</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; margin-bottom: 25px;'>Upload two creative variations to compare their AI scores and delta analysis side-by-side.</p>", unsafe_allow_html=True)
    ab_col1, ab_col2 = st.columns(2)
    with ab_col1:
        file_a = st.file_uploader("Creative A", type=["jpg", "jpeg", "png"], key="ab_a")
        if file_a:
            st.image(open_uploaded_image(file_a), use_container_width=True)
    with ab_col2:
        file_b = st.file_uploader("Creative B", type=["jpg", "jpeg", "png"], key="ab_b")
        if file_b:
            st.image(open_uploaded_image(file_b), use_container_width=True)

    if st.button("Compare A vs B", type="primary", key="ab_compare"):
        if not file_a or not file_b:
            st.warning("Upload both creatives before comparing.")
        else:
            with st.spinner("Analyzing both creatives..."):
                try:
                    res_a, vis_a = run_single_analysis(file_a, temp_prefix="temp_a_")
                    res_b, vis_b = run_single_analysis(file_b, temp_prefix="temp_b_")
                    if not res_a or not res_b:
                        st.error("One or both evaluations failed.")
                    else:
                        st.subheader("Score comparison")
                        cmp = pd.DataFrame(
                            {
                                "Metric": [
                                    "Design",
                                    "Business",
                                    "Total",
                                    "Visual hierarchy",
                                    "Message clarity",
                                ],
                                "Creative A": [
                                    res_a["design_score"],
                                    res_a["business_score"],
                                    res_a["design_score"] + res_a["business_score"],
                                    res_a["score_breakdown"]["visual_hierarchy"],
                                    res_a["score_breakdown"]["message_clarity"],
                                ],
                                "Creative B": [
                                    res_b["design_score"],
                                    res_b["business_score"],
                                    res_b["design_score"] + res_b["business_score"],
                                    res_b["score_breakdown"]["visual_hierarchy"],
                                    res_b["score_breakdown"]["message_clarity"],
                                ],
                            }
                        )
                        cmp["Delta (B - A)"] = cmp["Creative B"] - cmp["Creative A"]
                        st.dataframe(cmp, use_container_width=True, hide_index=True)

                        winner = "A" if cmp.loc[2, "Creative A"] >= cmp.loc[2, "Creative B"] else "B"
                        st.success(
                            f"Creative **{winner}** leads on combined score. "
                            f"A: {res_a['actionable_feedback']} | B: {res_b['actionable_feedback']}"
                        )

                        r1, r2 = st.columns(2)
                        with r1:
                            st.markdown("#### Creative A")
                            render_audit_result(res_a, vis_a)
                        with r2:
                            st.markdown("#### Creative B")
                            render_audit_result(res_b, vis_b)
                except Exception as e:
                    st.error(f"Comparison error: {e}")


# ─────────────────────────────────────────────
# TAB 3: BA Analytics dashboard
# ─────────────────────────────────────────────
@st.cache_data
def load_historical_data():
    try:
        conn = duckdb.connect("ad_database.duckdb", read_only=True)
        df = conn.execute("SELECT * FROM ad_evaluations ORDER BY created_at DESC").df()
        conn.close()
        return normalize_created_at(df)
    except Exception:
        return pd.DataFrame()


with tab_analytics:
    df = load_historical_data()

    if df.empty:
        st.info(
            "No historical data. Run `python init_db.py` then `python run_pipeline.py` "
            "to populate DuckDB from ads_dataset."
        )
    else:
        df = df.copy()
        df["total_score"] = df["design_score"] + df["business_score"]
        low_threshold = 12
        df["needs_improvement"] = df["total_score"] < low_threshold

        st.markdown("<h2 style='text-align: center; color: #1E3A8A; font-weight: 800; font-family: Poppins, sans-serif; margin-bottom: 0px; margin-top: 15px;'>📈 Global Campaign Analytics Dashboard</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B; margin-bottom: 30px;'>Comprehensive view of your historical creative performance and AI-driven benchmarks.</p>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Ads analyzed", len(df))
        k2.metric("Avg design score", f"{df['design_score'].mean():.1f}")
        k3.metric("Avg business score", f"{df['business_score'].mean():.1f}")
        k4.metric("Low performers", int(df["needs_improvement"].sum()))

        st.download_button(
            "Download full dataset (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            "ad_evaluations_export.csv",
            "text/csv",
        )



        if "person_count" in df.columns:
            seg = (
                df.groupby("person_count")[["design_score", "business_score", "total_score"]]
                .mean()
                .reset_index()
            )
            st.markdown("**Segment: average scores by people count**")
            st.dataframe(seg, use_container_width=True, hide_index=True)

        if "color_hex_json" in df.columns and df["color_hex_json"].notna().any():
            psych_tags = []
            for val in df["color_hex_json"].dropna():
                try:
                    colors = json.loads(val) if isinstance(val, str) else val
                    if colors:
                        psych_tags.append(colors[0].get("psychology", "unknown"))
                except (json.JSONDecodeError, TypeError):
                    pass
            if psych_tags:
                psych_df = pd.Series(psych_tags).value_counts().reset_index()
                psych_df.columns = ["psychology", "count"]
                fig_p = px.pie(psych_df, names="psychology", values="count", title="Dominant color psychology mix")
                st.plotly_chart(fig_p, use_container_width=True)



        st.markdown("**Low performers** (total score < 12)")
        low_df = df[df["needs_improvement"]][
            [
                "image_filename",
                "design_score",
                "business_score",
                "total_score",
                "campaign_type_guess",
                "actionable_feedback",
            ]
        ].sort_values("total_score")
        st.dataframe(low_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🏆 Top Performers Showcase")
        top_3 = df.nlargest(3, "total_score")
        cols = st.columns(3)
        for col, (_, row) in zip(cols, top_3.iterrows()):
            with col:
                # 1. Try to load image file using absolute path resolution
                image_loaded = False
                img = None
                try:
                    from pathlib import Path
                    base_dir = Path(__file__).parent.resolve()
                    img_path = base_dir / "ads_dataset" / row['image_filename']
                    if img_path.exists():
                        img = Image.open(img_path)
                        image_loaded = True
                except Exception:
                    pass

                # 2. Render image if loaded successfully, otherwise show fallback card
                if image_loaded and img is not None:
                    st.image(img, use_container_width=True)
                else:
                    # Parse color hex json for visual preview
                    color_dots_html = ""
                    try:
                        colors = json.loads(row['color_hex_json']) if isinstance(row['color_hex_json'], str) else row['color_hex_json']
                        if colors:
                            for c in colors[:4]:
                                color_dots_html += f"""
                                <div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
                                    <span style="display:inline-block; width:22px; height:22px; border-radius:50%; background-color:{c['hex']}; border:1.5px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);" title="{c['name']}"></span>
                                    <span style="font-size: 0.65rem; color: #64748B; font-weight: 600;">{c['coverage_pct']}%</span>
                                </div>
                                """
                    except Exception:
                        pass
                    
                    category = row['campaign_type_guess'] or 'N/A'
                    people = row.get('person_count', 0)
                    
                    st.html(f"""
                    <div style="background: linear-gradient(135deg, #F8FAFC 0%, #EDF2F7 100%); 
                                border-radius: 16px; 
                                padding: 24px; 
                                border: 1px solid #E2E8F0; 
                                box-shadow: 0 4px 20px rgba(15, 23, 42, 0.02); 
                                margin-bottom: 16px; 
                                text-align: center;
                                position: relative;
                                overflow: hidden;">
                        <!-- Glassmorphic category tag -->
                        <div style="position: absolute; top: 12px; right: 12px; 
                                    background: rgba(255, 255, 255, 0.85); 
                                    backdrop-filter: blur(4px);
                                    border: 1px solid #E2E8F0;
                                    padding: 4px 10px; 
                                    border-radius: 9999px; 
                                    font-size: 0.65rem; 
                                    font-weight: 700; 
                                    color: #475569; 
                                    text-transform: uppercase; 
                                    letter-spacing: 0.5px;">
                            🏷️ {category}
                        </div>
                        <div style="font-size: 3rem; margin-top: 10px; margin-bottom: 12px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.05));">🖼️</div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: #1E293B; word-break: break-all; margin-bottom: 6px;">{row['image_filename']}</div>
                        <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 14px;">👥 People Count: <b>{people}</b></div>
                        
                        <!-- Dominant color preview panel -->
                        <div style="background: rgba(255, 255, 255, 0.6); border-radius: 10px; padding: 8px 12px; display: inline-flex; gap: 12px; justify-content: center; align-items: center; border: 1.5px solid rgba(226, 232, 240, 0.6); margin: 0 auto 10px auto;">
                            {color_dots_html or '<span style="font-size: 0.7rem; color: #94A3B8;">No colors analyzed</span>'}
                        </div>
                        
                        <div style="font-size: 0.7rem; color: #94A3B8; font-style: italic; margin-top: 6px;">Image not found in ads_dataset/</div>
                    </div>
                    """)

                # 3. Render matching scores and strategic feedback card
                st.markdown(
                    f"<div style='display:flex; gap:8px; margin-bottom: 8px; justify-content: center;'>"
                    f"<span class='badge-design'>Design: {row['design_score']}/10</span>"
                    f"<span class='badge-biz'>Business: {row['business_score']}/10</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                st.info(row["actionable_feedback"])

        st.markdown("---")
        st.subheader("🖼️ Historical Ad Gallery")
        
        from pathlib import Path
        base_dir = Path(__file__).parent.resolve()
        
        # Filter rows where image exists
        valid_gallery_rows = []
        for idx, row in df.iterrows():
            img_path = base_dir / "ads_dataset" / row['image_filename']
            if img_path.exists():
                valid_gallery_rows.append(row)
                
        if valid_gallery_rows:
            # Display images in 4 columns
            cols_per_row = 4
            grid_cols = st.columns(cols_per_row)
            for idx, row in enumerate(valid_gallery_rows):
                col_index = idx % cols_per_row
                with grid_cols[col_index]:
                    img_path = base_dir / "ads_dataset" / row['image_filename']
                    try:
                        img = Image.open(img_path)
                        st.image(img, use_container_width=True)
                        st.markdown(
                            f"<div style='text-align: center; margin-top: -8px; margin-bottom: 20px;'>"
                            f"<span style='font-size: 0.85rem; font-weight: 700; color: #1E293B; word-break: break-all; display: block; height: 38px; overflow: hidden; text-overflow: ellipsis;'>{row['image_filename']}</span>"
                            f"<span class='badge-design' style='font-size: 0.75rem; padding: 2px 8px; margin-right: 4px;'>D: {row['design_score']}</span>"
                            f"<span class='badge-biz' style='font-size: 0.75rem; padding: 2px 8px;'>B: {row['business_score']}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    except Exception:
                        pass
        else:
            st.info("No images found in ads_dataset/ to show in the gallery.")

        st.markdown("---")
        with st.expander("Full database"):
            st.dataframe(df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# TAB 4: Methodology & Architecture
# ─────────────────────────────────────────────
with tab_overview:
    st.markdown(
        """
        <div style="background-color: #FFFFFF; border-radius: 16px; padding: 32px; box-shadow: 0 10px 40px rgba(15, 23, 42, 0.03); border: 1px solid #E2E8F0; margin-bottom: 2rem;">
            <h2 style="font-family: 'Poppins', sans-serif; font-weight: 800; color: #1E3A8A; margin-top: 0px; margin-bottom: 20px;">🔬 Methodology & System Architecture</h2>
            <p style="font-family: 'Inter', sans-serif; font-size: 1rem; color: #475569; line-height: 1.6; margin-bottom: 0px;">
                AI Creative Auditor is designed using a <b>hybrid edge-cloud model</b> that guarantees data privacy while leveraging advanced deep learning. Images are processed locally on the client or hosting server for computer vision tasks, and only anonymized structured metadata is sent to remote large language models (LLMs) for final cognitive analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col_tech1, col_tech2 = st.columns(2, gap="large")
    
    with col_tech1:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border-radius: 16px; padding: 28px; box-shadow: 0 10px 40px rgba(15, 23, 42, 0.02); border: 1px solid #E2E8F0; height: 100%;">
                <h3 style="font-family: 'Poppins', sans-serif; color: #117A65; margin-top: 0px; margin-bottom: 15px;">🔍 1. Edge-Side Computer Vision</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.6;">
                    The client-side vision pipeline extracts quantitative features directly from the raw image matrix:
                </p>
                <ul style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.7; margin-left: 20px; padding-left: 0px;">
                    <li><b>Object & Face Detection (YOLOv8)</b>: Runs a lightweight deep-learning model locally to detect and count human figures, aiding segment analysis.</li>
                    <li><b>Optical Character Recognition (EasyOCR)</b>: Uses local PyTorch models to extract Thai and English text scripts directly from visual boundaries.</li>
                    <li><b>Color Psychology (K-Means Clustering)</b>: Resizes and clusters pixels in RGB/HSV space to identify top dominant colors, mapping them to marketing emotional impact categories.</li>
                    <li><b>Text Contrast Heuristic (WCAG 2.1)</b>: Calculates the relative luminance contrast ratio between the text and background bounding boxes to flag readability risks.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with col_tech2:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border-radius: 16px; padding: 28px; box-shadow: 0 10px 40px rgba(15, 23, 42, 0.02); border: 1px solid #E2E8F0; height: 100%;">
                <h3 style="font-family: 'Poppins', sans-serif; color: #0EA5E9; margin-top: 0px; margin-bottom: 15px;">🧠 2. Cloud LLM Cognitive Scoring</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.6;">
                    Once raw features are processed, they are structured into a prompt and evaluated using API-based models:
                </p>
                <ul style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.7; margin-left: 20px; padding-left: 0px;">
                    <li><b>Llama 3.3 (via Groq API)</b>: An optimized 70B parameter model processes the derived metadata (OCR text, color ratios, WCAG results) to generate a business rubric evaluation.</li>
                    <li><b>Pydantic Schema Enforcement</b>: The JSON output structure is strictly validated via typing schemas before database insert, avoiding malformed AI outputs.</li>
                    <li><b>Double-blind Scoring</b>: Evaluates creatives on 4 main sub-scores: Visual Hierarchy, Color Psychology, Message Clarity, and Target Audience Fit.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_gdpr, col_kpi = st.columns(2, gap="large")
    
    with col_gdpr:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border-radius: 16px; padding: 28px; box-shadow: 0 10px 40px rgba(15, 23, 42, 0.02); border: 1px solid #E2E8F0; height: 100%;">
                <h3 style="font-family: 'Poppins', sans-serif; color: #B91C1C; margin-top: 0px; margin-bottom: 15px;">🔒 GDPR & Data Privacy Compliance</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.6;">
                    For deployments in the European Union (EU) or Germany, strict data handling is required:
                </p>
                <ul style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.7; margin-left: 20px; padding-left: 0px;">
                    <li><b>Local Image Hosting</b>: Raw ad graphics are never sent to external visual LLM endpoints by default.</li>
                    <li><b>PII Scrubbing</b>: No personally identifiable information (PII) is included in the prompt payloads sent to external LLMs.</li>
                    <li><b>Security Audit</b>: Groq API acts purely as a text sub-processor. Ideal architecture for corporate environments concerned with intellectual property protection.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with col_kpi:
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border-radius: 16px; padding: 28px; box-shadow: 0 10px 40px rgba(15, 23, 42, 0.02); border: 1px solid #E2E8F0; height: 100%;">
                <h3 style="font-family: 'Poppins', sans-serif; color: #475569; margin-top: 0px; margin-bottom: 15px;">📊 Key Performance Indicators (KPIs)</h3>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.6;">
                    The platform computes aggregate metrics inside DuckDB to benchmark campaign creatives:
                </p>
                <ul style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569; line-height: 1.7; margin-left: 20px; padding-left: 0px;">
                    <li><b>Design Score (1-10)</b>: Overall score evaluating spatial layout, focal flow, contrast, and visual balance.</li>
                    <li><b>Business Score (1-10)</b>: Assessment of marketing call-to-action (CTA) clarity, commercial intent, and value proposition readability.</li>
                    <li><b>Low Performers</b>: Creatives with a combined score below 12. These are flagged for immediate revision before campaign deployment to prevent waste of media spend.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

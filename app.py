import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import os
import duckdb
import pandas as pd

# ==========================================
# PAGE CONFIG & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="AI Creative Auditor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');

        .stApp { background-color: #F4F7F9; }
        html, body, [class*="css"], p, h1, h2, h3, h4, h5, h6, span, div { color: #0F172A !important; }

        /* Main card containers */
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            background-color: #FFFFFF; border-radius: 20px; padding: 2rem;
            box-shadow: 0 10px 40px rgba(15, 23, 42, 0.03); border: 1px solid #E2E8F0;
        }

        /* Hero header */
        .main-header { text-align: center; margin-bottom: 3.5rem; margin-top: 1.5rem; }
        .main-header h1 { font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 3.2rem; letter-spacing: -1.5px; color: #0F172A !important; margin-bottom: 0.5rem !important;}
        .main-header p { font-family: 'Inter', sans-serif; font-weight: 500; color: #475569 !important; font-size: 1.25rem; max-width: 700px; margin: 0 auto; line-height: 1.6;}

        /* Upload area */
        .upload-subtitle { text-align: center; font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 700; color: #117A65 !important; margin-bottom: 1.2rem; }

        div[data-testid="stFileUploader"] { background-color: #FFFFFF !important; padding: 2rem !important; border-radius: 12px !important; margin-bottom: 2rem; }
        div[data-testid="stFileUploader"] section { border: 2px dashed #117A65 !important; background-color: #F8FAFC !important; padding: 3rem !important; border-radius: 12px !important; }

        div[data-testid="stFileUploader"] section button {
            background-color: #117A65 !important; color: #FFFFFF !important; border-radius: 8px !important; font-weight: 600 !important; padding: 0.6rem 2rem !important; border: none !important;
        }
        div[data-testid="stFileUploader"] section svg { color: #117A65 !important; fill: #117A65 !important; width: 50px !important; height: 50px !important; }
        [data-testid="stFileUploadDropzone"] div div::before { display: none !important; }
        button[aria-label="Remove file"] { background-color: transparent !important; border: none !important; box-shadow: none !important; }

        /* Card title */
        .card-title { font-family: 'Poppins', sans-serif; font-size: 1.4rem; font-weight: 800; color: #1E3A8A !important; margin-bottom: 1.8rem; border-bottom: 2px solid #F1F5F9; padding-bottom: 1rem; }

        /* AI recommendation box */
        .ai-rec-box { background-color: #F8FAFC; border-left: 5px solid #0EA5E9; padding: 25px; border-radius: 10px; color: #020617 !important; font-family: 'Inter', sans-serif; font-size: 1.1rem; line-height: 1.7; font-weight: 500; margin-top: 1rem; }
        .ai-rec-box strong { font-weight: 700; color: #0F172A !important; }

        /* Expander */
        [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important; }
        [data-testid="stExpander"] summary p { font-family: 'Inter', sans-serif; color: #0284C7 !important; font-size: 1.1rem !important; font-weight: 700 !important; }

        /* KPI dashboard */
        .kpi-title { font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 700; color: #1E293B !important; margin-bottom: 0.8rem; text-transform: uppercase; letter-spacing: 1px;}
        .kpi-val { font-family: 'Poppins', sans-serif; font-size: 3.5rem; font-weight: 900; color: #0F172A !important; line-height: 1.1; margin-bottom: 0.8rem; letter-spacing: -1.5px;}
        .kpi-sub-1 { font-family: 'Inter', sans-serif; font-size: 0.9rem; font-weight: 600; color: #64748B !important; margin-top: 0.8rem;}
        .kpi-sub-2 { font-family: 'Inter', sans-serif; font-size: 0.9rem; font-weight: 600; color: #10B981 !important; margin-top: 0.8rem;}
        .kpi-sub-3 { font-family: 'Inter', sans-serif; font-size: 0.9rem; font-weight: 600; color: #F59E0B !important; margin-top: 0.8rem;}

        /* Database section */
        .db-header-text { font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 2.5rem; color: #0F172A !important; letter-spacing: -1px; margin-bottom: 0.3rem !important;}
        .db-sub-text { font-family: 'Inter', sans-serif; font-weight: 500; color: #64748B !important; font-size: 1.1rem; margin-bottom: 1.5rem !important;}
        .showcase-title { font-family: 'Poppins', sans-serif; font-size: 1.6rem; font-weight: 800; color: #1E3A8A !important; margin-bottom: 1.8rem; letter-spacing: -0.5px;}
        .sc-filename { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 1.15rem; color: #1E3A8A !important; margin-top: 1rem; margin-bottom: 0.8rem;}
        .sc-desc { font-family: 'Inter', sans-serif; font-size: 1rem; color: #334155 !important; line-height: 1.6; font-weight: 500;}
        .badge-design { background-color: #E0F2FE; color: #0284C7; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 0.85rem;}
        .badge-biz { background-color: #DCFCE3; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 0.85rem;}
        .db-row strong { font-family: 'Poppins', sans-serif; font-size: 1.1rem; color: #1E3A8A !important; }
        .db-row p { font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #475569 !important; font-weight: 500; }

        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


# ==========================================
# GAUGE CHART COMPONENT
# ==========================================
def create_gauge_chart(score, title, color):
    """สร้างกราฟหน้าปัดแสดงคะแนน 0-10"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'color': '#0F172A', 'weight': 'bold', 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 10], 'tickwidth': 1.5, 'tickcolor': "#0F172A"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "#E2E8F0",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 4], 'color': '#FEE2E2'},
                {'range': [4, 7], 'color': '#FEF08A'},
                {'range': [7, 10], 'color': '#DCFCE3'}
            ],
        }
    ))
    fig.update_layout(
        height=230,
        margin=dict(l=15, r=15, t=45, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A")
    )
    return fig


# ==========================================
# HERO SECTION & UPLOAD
# ==========================================
st.markdown("""
    <div class='main-header'>
        <h1>AI Creative Auditor</h1>
        <p>Evaluate your marketing assets instantly. Upload an image to receive immediate feedback on design quality and business potential using Computer Vision &amp; Llama 3.3</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("<p class='upload-subtitle'>Curious how your poster performs? Let AI evaluate it for you.</p>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded_file:
    st.markdown("<br>", unsafe_allow_html=True)
    col_img, col_res = st.columns([1, 1.2], gap="large")

    with col_img:
        st.markdown("<div class='card-title'>Target Creative Asset</div>", unsafe_allow_html=True)
        st.image(Image.open(uploaded_file), width="stretch")
        st.markdown("<br>", unsafe_allow_html=True)
        run_button = st.button("Analyze Now", type="primary")

    with col_res:
        st.markdown("<div class='card-title'>Creative Performance Profile</div>", unsafe_allow_html=True)

        if run_button:
            with st.spinner("Analyzing creative architecture..."):
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    from vision_ops import analyze_image_vision
                    from run_pipeline import evaluate_with_groq
                    vision_data = analyze_image_vision(temp_path)
                    res = evaluate_with_groq(vision_data, uploaded_file.name)

                    if res:
                        gauge_col1, gauge_col2 = st.columns(2)
                        with gauge_col1:
                            st.plotly_chart(create_gauge_chart(res['design_score'], "Design Score", "#0EA5E9"), width="stretch", theme=None)
                        with gauge_col2:
                            st.plotly_chart(create_gauge_chart(res['business_score'], "Business Score", "#10B981"), width="stretch", theme=None)

                        st.markdown(f"""
                            <div class='ai-rec-box'>
                                <strong>AI Recommendations:</strong><br><br>
                                {res['actionable_feedback']}
                            </div>
                            <div style="height: 25px;"></div>
                        """, unsafe_allow_html=True)

                        with st.expander("AI Vision Insights"):
                            st.markdown(f"""
                            - **People:** {vision_data['person_count']}
                            - **Colors:** {vision_data['dominant_colors']}
                            - **Raw Text:** {vision_data['raw_ocr_text']}
                            - **Cleaned:** {res['corrected_text']}
                            """)

                except Exception as e:
                    st.error(f"Analysis Error: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        else:
            st.info("Click 'Analyze Now' to start the evaluation process.")


# ==========================================
# HISTORICAL DATABASE SECTION
# ==========================================
st.markdown("<hr style='margin-top: 2rem; margin-bottom: 1rem; border-color: #CBD5E1;'>", unsafe_allow_html=True)


@st.cache_data
def load_historical_data():
    """ดึงข้อมูลการวิเคราะห์ทั้งหมดจาก DuckDB"""
    try:
        conn = duckdb.connect('ad_database.duckdb', read_only=True)
        df = conn.execute("SELECT * FROM ad_evaluations").df()
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


df = load_historical_data()

if not df.empty:
    st.markdown("""
        <div style='text-align: center; margin-bottom: 1.5rem; margin-top: 0;'>
            <h2 class='db-header-text'>Historical Database</h2>
            <p class='db-sub-text'>Ad creatives that scored exceptionally well in both design aesthetics and business potential</p>
        </div>
    """, unsafe_allow_html=True)

    # ── KPI Cards ──
    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        st.markdown(f"<div style='text-align: center;'><div class='kpi-title'>Total Ads Analyzed</div><div class='kpi-val'>{len(df)}</div><div class='kpi-sub-1'>🗄️ DuckDB Connected</div></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div style='text-align: center;'><div class='kpi-title'>Average Design Score</div><div class='kpi-val'>{df['design_score'].mean():.1f}</div><div class='kpi-sub-2'>↗ Top Quartile: > 8.0</div></div>", unsafe_allow_html=True)
    with k3:
        needs_improvement = len(df[(df['design_score'] + df['business_score']) < 12])
        st.markdown(f"<div style='text-align: center;'><div class='kpi-title'>Average Business Score</div><div class='kpi-val'>{df['business_score'].mean():.1f}</div><div class='kpi-sub-3'>⚠️ {needs_improvement} ads need improvement</div></div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Top Performers ──
    st.markdown("<h3 class='showcase-title'>Top Performers Showcase</h3>", unsafe_allow_html=True)

    df['total_score'] = df['design_score'] + df['business_score']
    top_3 = df.nlargest(3, 'total_score')

    cols = st.columns(3, gap="large")
    for col, (_, data) in zip(cols, top_3.iterrows()):
        with col:
            try:
                st.image(Image.open(f"ads_dataset/{data['image_filename']}"), width="stretch")
            except Exception:
                st.info("Image missing")

            st.markdown(f"<div class='sc-filename'>{data['image_filename']}</div>", unsafe_allow_html=True)
            st.markdown(f"<span class='badge-design'>Design: {data['design_score']}</span> &nbsp; <span class='badge-biz'>Biz: {data['business_score']}</span>", unsafe_allow_html=True)
            st.markdown(f"<div class='sc-desc'>{data['actionable_feedback']}</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Full Database Expander ──
    with st.expander("View Full Database (All Analyzed Ads)"):
        st.markdown("<br>", unsafe_allow_html=True)
        for _, data in df.sort_values('total_score', ascending=False).iterrows():
            st.markdown("<div style='border-bottom: 1px solid #E2E8F0; padding-bottom: 1rem; margin-bottom: 1rem;'>", unsafe_allow_html=True)
            c1, c2 = st.columns([1, 4])
            with c1:
                try:
                    st.image(Image.open(f"ads_dataset/{data['image_filename']}"), width="stretch")
                except Exception:
                    st.caption("No Image")
            with c2:
                st.markdown(f"<strong style='font-family: Poppins, sans-serif; font-size: 1.1rem; color: #1E3A8A;'>{data['image_filename']}</strong>", unsafe_allow_html=True)
                st.markdown(f"<span class='badge-design'>Design: {data['design_score']}</span> &nbsp; <span class='badge-biz'>Biz: {data['business_score']}</span>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin-top: 0.5rem; font-family: Inter, sans-serif; font-size: 0.95rem; color: #475569;'>{data['actionable_feedback']}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("No historical data found. Please run the init_db.py pipeline first.")
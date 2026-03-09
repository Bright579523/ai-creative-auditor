# AI Creative Auditor

🔧 Tech Stack
Frontend UI: Streamlit, Plotly
Computer Vision: OpenCV, YOLOv8 (ultralytics), EasyOCR, scikit-learn
Generative AI: Groq API (Llama 3.3 70B Versatile)
Infrastructure: DuckDB, Docker, Hugging Face Spaces

> **Stop guessing if your ad works. Let AI analyze the visuals and give you data-driven marketing feedback in seconds.**

Upload any advertising poster or creative asset, and this system will instantly extract the visual elements (people, text, colors) and pass them to an AI Marketing Strategist for a comprehensive evaluation. 

🔗 **[Try it live on Hugging Face Spaces](https://huggingface.co/spaces/Bright87/ai-creative-auditor)**

---

## ✨ What makes this different?

Instead of relying on basic API wrappers, this project integrates standard Computer Vision pipelines with Generative AI:
* **True-to-Eye Color Analysis:** RGB often fails with lighting variations. We use **K-Means clustering on the HSV color space** to detect colors exactly as the human eye perceives them (e.g., distinguishing natural forest green from dark shadows).
* **Context-Aware OCR:** Extracts text using EasyOCR (English & Thai) and processes it with AI to fix misread words based on the image's context.
* **Serverless Analytics:** Uses DuckDB to locally store and serve historical analysis without the overhead of a traditional database.

---

## 🖥️ See it in Action

<img width="1801" height="544" alt="image" src="https://github.com/user-attachments/assets/c1d8260d-70be-4cb3-b81d-a8efbdf08cda" />

### 1. Upload & Analyze
<img width="1838" height="785" alt="image" src="https://github.com/user-attachments/assets/c90fdd3b-ade8-430b-a24b-59e69a989385" />

*Users get an instant breakdown of Design Score, Business Score, and one sharp, actionable AI recommendation.*

### 2. Historical Dashboard
<img width="1871" height="830" alt="image" src="https://github.com/user-attachments/assets/a3da34fc-cf39-4d66-8734-3e57c02caebb" />

*Browse previously analyzed campaigns, view KPI cards, and see the Top Performers showcase.*

---

## 🏗️ System Architecture

```text
[ User Upload ] ──→ [ Vision Pipeline ] ───────→ [ AI Evaluation ] ──→ [ Dashboard ]
                         │                              │
                         ├── YOLOv8 (People)            ├── Groq API 
                         ├── EasyOCR (Text)             ├── Llama 3.3 70B
                         └── K-Means + HSV (Colors)     └── JSON Output
```
## 🚀 Quick Start (Local Development)
Want to run this on your own machine? Follow these steps:

1. Clone the repository
```
git clone [https://github.com/Bright579523/ai-creative-auditor.git](https://github.com/Bright579523/ai-creative-auditor.git)
cd ai-creative-auditor
```
2. Install dependencies
```
pip install -r requirements.txt
```
3. Set up your API Key
You need a free API key from Groq. Do not hardcode it. Export it securely:
Windows: set GROQ_API_KEY=your_api_key_here
Mac/Linux: export GROQ_API_KEY=your_api_key_here

4. Fire it up
   ```
   streamlit run app.py

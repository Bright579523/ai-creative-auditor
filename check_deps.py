"""Verify runtime dependencies before running Streamlit or pipeline."""

import sys

REQUIRED = [
    ("streamlit", "streamlit"),
    ("duckdb", "duckdb"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("cv2", "opencv-python-headless"),
    ("easyocr", "easyocr"),
    ("ultralytics", "ultralytics"),
    ("groq", "groq"),
    ("pydantic", "pydantic"),
    ("sklearn", "scikit-learn"),
    ("plotly", "plotly"),
]


def main() -> int:
    missing = []
    for module, package in REQUIRED:
        try:
            __import__(module)
            print(f"OK  {package}")
        except ImportError:
            print(f"MISSING  {package}  (pip install {package})")
            missing.append(package)

    if missing:
        print("\nInstall all dependencies:")
        print("  pip install -r requirements.txt")
        return 1
    print("\nAll dependencies OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

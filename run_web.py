#!/usr/bin/env python3
"""Resume Assistant Web Application Runner."""

import subprocess
import sys
from pathlib import Path

def run_streamlit_app():
    """运行Streamlit应用"""
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.address", "0.0.0.0",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("🚀 启动Resume Assistant Web应用...")
    print(f"📱 访问地址: http://localhost:8501")
    print("⚠️  按 Ctrl+C 停止应用")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")

if __name__ == "__main__":
    run_streamlit_app()
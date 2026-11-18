import os
import subprocess
import sys


def print_banner():
    print("=" * 64)
    print("                🚗 SafeRouteAI System Hub")
    print("       AI-Powered Road Hazard Monitoring & Driver Safety")
    print("=" * 64)


def get_python_executable():
    venv_py = os.path.join(".venv", "Scripts", "python.exe")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable


def launch_streamlit():
    py = get_python_executable()
    print("\n🌐 Starting Streamlit Dashboard...")
    print("Your browser should automatically open at http://localhost:8501")
    subprocess.run([py, "-m", "streamlit", "run", "app.py"])


def launch_video_demo():
    py = get_python_executable()
    print("\n🎬 Starting Video Hazard Detection Demo...")
    print("Press 'Q' inside the video window to quit.")
    subprocess.run([py, "final_demo.py"])


def launch_live_webcam():
    py = get_python_executable()
    print("\n📹 Starting Live Webcam Road Safety Assistant...")
    print("Press 'Q' inside the camera window to quit.")
    subprocess.run([py, "road_safety.py"])


def launch_evaluation():
    py = get_python_executable()
    print("\n📊 Running Model Evaluation Benchmark...")
    subprocess.run([py, "evaluate.py"])


def main():
    while True:
        print_banner()
        print(" [1] 🌐 Launch Streamlit Web Dashboard")
        print(" [2] 🎬 Run Video Road Safety Demo (road_video.mp4)")
        print(" [3] 📹 Run Live Webcam Hazard Assistant")
        print(" [4] 📊 Evaluate Pothole Model Accuracy (mAP Metrics)")
        print(" [5] ❌ Exit")
        print("=" * 64)

        try:
            choice = input("Select an option (1-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if choice == "1":
            launch_streamlit()
        elif choice == "2":
            launch_video_demo()
        elif choice == "3":
            launch_live_webcam()
        elif choice == "4":
            launch_evaluation()
        elif choice == "5" or choice.lower() in ("q", "exit"):
            print("Goodbye! Drive safely.")
            break
        else:
            print("Invalid option. Please choose 1, 2, 3, 4, or 5.\n")


if __name__ == "__main__":
    main()

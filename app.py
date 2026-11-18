import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List

import cv2
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

from alert_manager import AlertManager
from detectors import MultiHazardDetector
from risk_analyzer import RiskAnalyzer, RiskAssessmentResult
from translations import (
    localization_service,
    SUPPORTED_LANGUAGES,
    get_translation,
    get_speed_advisory,
    get_risk_label
)

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SafeRouteAI • Autonomous In-Cab Safety Cockpit",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. APPLICATION STYLING ENCAPSULATION (OOP)
# ============================================================

class AppStyling:
    """Encapsulates cockpit CSS styling and custom font injection."""

    CSS_PAYLOAD = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800;900&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 0%, #111827 0%, #0b0f19 80%) !important;
    }

    .cockpit-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.90) 50%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 18px;
        padding: 24px 30px;
        margin-bottom: 22px;
        box-shadow: 0 12px 35px -8px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(16px);
        position: relative;
        overflow: hidden;
    }

    .cockpit-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #38bdf8, transparent);
        animation: scanline 4s infinite linear;
    }

    @keyframes scanline {
        0% { left: -100%; }
        100% { left: 100%; }
    }

    .cockpit-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0 0 6px 0;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }

    .cockpit-subtitle {
        font-family: 'Rajdhani', sans-serif;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.8px;
        color: #94a3b8;
        margin: 0;
        text-transform: uppercase;
    }

    .radar-box {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 30px;
        padding: 8px 16px;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
    }

    .radar-circle {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 2px solid rgba(56, 189, 248, 0.4);
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .radar-sweep {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border-top: 2px solid #38bdf8;
        animation: radarSpin 2s infinite linear;
    }

    @keyframes radarSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .radar-blip {
        width: 6px;
        height: 6px;
        background-color: #ef4444;
        border-radius: 50%;
        box-shadow: 0 0 8px #ef4444;
        animation: blipPulse 1.2s infinite ease-in-out;
    }

    @keyframes blipPulse {
        0%, 100% { opacity: 0.3; transform: scale(0.8); }
        50% { opacity: 1.0; transform: scale(1.3); }
    }

    .hud-card {
        border-radius: 16px;
        padding: 18px 24px;
        margin-bottom: 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        backdrop-filter: blur(12px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .hud-critical {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.22) 0%, rgba(153, 27, 27, 0.28) 100%);
        border: 1px solid rgba(239, 68, 68, 0.7);
        box-shadow: 0 0 35px rgba(239, 68, 68, 0.25), inset 0 0 15px rgba(239, 68, 68, 0.15);
    }

    .hud-warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.22) 0%, rgba(180, 83, 9, 0.28) 100%);
        border: 1px solid rgba(245, 158, 11, 0.7);
        box-shadow: 0 0 35px rgba(245, 158, 11, 0.25), inset 0 0 15px rgba(245, 158, 11, 0.15);
    }

    .hud-clear {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.22) 0%, rgba(5, 150, 105, 0.28) 100%);
        border: 1px solid rgba(16, 185, 129, 0.7);
        box-shadow: 0 0 35px rgba(16, 185, 129, 0.25), inset 0 0 15px rgba(16, 185, 129, 0.15);
    }

    .hud-msg {
        font-family: 'Orbitron', sans-serif;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #ffffff;
        margin-bottom: 4px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }

    .hud-desc {
        font-family: 'Rajdhani', sans-serif;
        font-size: 15px;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 8px;
        letter-spacing: 0.3px;
    }

    .speed-advisory-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 20px;
        font-family: 'Orbitron', sans-serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.6px;
    }

    .pulse-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }

    .dot-red {
        background-color: #ef4444;
        box-shadow: 0 0 14px #ef4444;
        animation: pulseRed 1.5s infinite;
    }

    .dot-orange {
        background-color: #f59e0b;
        box-shadow: 0 0 14px #f59e0b;
        animation: pulseOrange 1.5s infinite;
    }

    .dot-green {
        background-color: #10b981;
        box-shadow: 0 0 14px #10b981;
        animation: pulseGreen 1.5s infinite;
    }

    @keyframes pulseRed {
        0%, 100% { transform: scale(1); opacity: 0.9; }
        50% { transform: scale(1.35); opacity: 1; }
    }
    @keyframes pulseOrange {
        0%, 100% { transform: scale(1); opacity: 0.9; }
        50% { transform: scale(1.35); opacity: 1; }
    }
    @keyframes pulseGreen {
        0%, 100% { transform: scale(1); opacity: 0.9; }
        50% { transform: scale(1.35); opacity: 1; }
    }

    .hud-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 20px;
        padding: 4px 12px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 13px;
        color: #38bdf8;
        letter-spacing: 0.5px;
    }

    .hud-chip-live {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 20px;
        padding: 4px 12px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 13px;
        color: #f87171;
        letter-spacing: 0.5px;
    }

    .eq-container {
        display: flex;
        align-items: flex-end;
        gap: 3px;
        height: 16px;
        padding: 2px;
    }

    .eq-bar {
        width: 3px;
        background: #38bdf8;
        border-radius: 2px;
        animation: eqPulse 1.2s infinite ease-in-out;
    }

    .bar-1 { height: 35%; animation-delay: 0.0s; }
    .bar-2 { height: 75%; animation-delay: 0.2s; }
    .bar-3 { height: 100%; animation-delay: 0.4s; }
    .bar-4 { height: 50%; animation-delay: 0.1s; }
    .bar-5 { height: 80%; animation-delay: 0.3s; }

    @keyframes eqPulse {
        0%, 100% { transform: scaleY(0.4); }
        50% { transform: scaleY(1.0); }
    }
    </style>
    """

    @classmethod
    def inject(cls):
        st.html(cls.CSS_PAYLOAD)


# ============================================================
# 3. LADY VOICE JAVASCRIPT ENGINE (OOP REUSABLE SCRIPT)
# ============================================================

class LadyVoiceScriptFactory:
    """
    Generates female-only neural voice synthesis JavaScript blocks.

    KEY DESIGN: Chrome/Edge block speechSynthesis.speak() called from an
    auto-injected <script> (no direct user gesture in the iframe). The fix is
    to route auto-broadcast through window.parent.speechSynthesis, which
    carries the user-activation stamp from the user clicking Analyze.
    The Utterance object MUST be constructed with the same window's class
    (window.parent.SpeechSynthesisUtterance) to avoid cross-frame type errors.
    """

    # Helper JS: speakLadyVoice accepts (synth, UtteranceCtor, text, langCode)
    # so the caller can pass the correct window's SpeechSynthesisUtterance.
    HELPER_JS = """
    function findLadyVoice(synth, langCode) {
        if (!synth) return null;
        const voices = synth.getVoices() || [];
        if (!voices.length) return null;
        const prefix = (langCode || 'en').split('-')[0].toLowerCase();
        const maleNames = ['david', 'mark', 'george', 'richard', 'madhur', 'hemant', 'manohar', 'guy', 'male', 'man', 'boy', 'stefan', 'paul', 'claude'];
        const femaleNames = ['zira', 'swara', 'aarohi', 'kalpana', 'jenny', 'elvira', 'denise', 'katja', 'hedda', 'laura', 'hortense', 'celine', 'female', 'woman', 'girl', 'google', 'natural'];

        for (let i = 0; i < voices.length; i++) {
            const v = voices[i];
            const vLang = (v.lang || '').toLowerCase().replace('_', '-');
            const vName = (v.name || '').toLowerCase();
            if (vLang.startsWith(prefix) && femaleNames.some(f => vName.includes(f)) && !maleNames.some(m => vName.includes(m))) {
                return v;
            }
        }
        for (let i = 0; i < voices.length; i++) {
            const v = voices[i];
            const vLang = (v.lang || '').toLowerCase().replace('_', '-');
            const vName = (v.name || '').toLowerCase();
            if (vLang.startsWith(prefix) && !maleNames.some(m => vName.includes(m))) {
                return v;
            }
        }
        for (let i = 0; i < voices.length; i++) {
            const v = voices[i];
            const vLang = (v.lang || '').toLowerCase().replace('_', '-');
            if (vLang.startsWith(prefix)) {
                return v;
            }
        }
        return null;
    }

    // UtteranceCtor must come from the SAME window as synth to avoid
    // 'Failed to execute speak: parameter 1 is not of type SpeechSynthesisUtterance' errors.
    function speakLadyVoice(synth, UtteranceCtor, text, langCode) {
        if (!synth) return;
        try { synth.cancel(); } catch(e) {}
        function execSpeak() {
            try { synth.cancel(); } catch(e) {}
            const u = new UtteranceCtor(text);
            u.lang = langCode;
            u.rate = 1.0;
            u.pitch = 1.0;
            u.volume = 1.0;
            const lady = findLadyVoice(synth, langCode);
            if (lady) { u.voice = lady; }
            try { synth.speak(u); } catch(e) {}
        }
        const vs = synth.getVoices();
        if (!vs || vs.length === 0) {
            synth.onvoiceschanged = function() {
                synth.onvoiceschanged = null;
                execSpeak();
            };
        } else {
            execSpeak();
        }
    }
    """

    @classmethod
    def generate_auto_broadcast(cls, speech_text: str, locale_code: str, scene_token: str) -> str:
        """
        Auto-plays voice alert when analysis completes.
        Routes via window.parent.speechSynthesis to bypass iframe autoplay block.
        Falls back to local window.speechSynthesis if parent is unavailable.
        """
        safe_text = speech_text.replace('"', '\\"').replace("'", "\\'").replace("\n", " ")
        return f"""
        <script>
        (function() {{
            try {{
                const token = "{scene_token}";

                // --- Deduplicate: do not repeat the same instruction ---
                let topStorage = null;
                try {{
                    topStorage = (window.parent && window.parent.sessionStorage)
                        ? window.parent.sessionStorage
                        : window.sessionStorage;
                }} catch(e) {{ topStorage = window.sessionStorage; }}
                if (topStorage) {{
                    const lastSpoken = topStorage.getItem("saferoute_last_spoken_token");
                    if (lastSpoken === token) {{ return; }}
                    topStorage.setItem("saferoute_last_spoken_token", token);
                }}

                // --- 1. Synthetic ADAS warning chime (works in iframe context) ---
                try {{
                    const AudioCtx = window.AudioContext || window.webkitAudioContext;
                    if (AudioCtx) {{
                        const ctx = new AudioCtx();
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(880, ctx.currentTime);
                        osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.18);
                        gain.gain.setValueAtTime(0.20, ctx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.18);
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.start();
                        osc.stop(ctx.currentTime + 0.2);
                    }}
                }} catch(e) {{}}

                // --- 2. Neural Lady Voice via parent window (has user-activation) ---
                // Chrome blocks speechSynthesis in auto-injected iframes (no user gesture).
                // window.parent.speechSynthesis carries the user-activation from Analyze click.
                // CRITICAL: SpeechSynthesisUtterance must come from the SAME window as synth.
                {cls.HELPER_JS}
                let synth = null;
                let UtteranceCtor = null;
                try {{
                    if (window.parent && window.parent.speechSynthesis) {{
                        synth = window.parent.speechSynthesis;
                        UtteranceCtor = window.parent.SpeechSynthesisUtterance;
                    }}
                }} catch(e) {{}}
                if (!synth) {{
                    synth = window.speechSynthesis;
                    UtteranceCtor = window.SpeechSynthesisUtterance;
                }}
                if (synth && UtteranceCtor) {{
                    speakLadyVoice(synth, UtteranceCtor, "{safe_text}", "{locale_code}");
                }}
            }} catch(e) {{}}
        }})();
        </script>
        """

    @classmethod
    def generate_replay_button(cls, speech_text: str, locale_code: str, language_label: str) -> str:
        """
        Manual replay button. Uses local window.speechSynthesis because onclick
        IS a trusted user gesture — no parent routing needed.
        """
        safe_text = speech_text.replace('"', '\\"').replace("'", "\\'").replace("\n", " ")
        return f"""
        <script>
        {cls.HELPER_JS}
        function playSpeech() {{
            // onclick is a trusted gesture; use local synth directly.
            let synth = window.speechSynthesis;
            let UtteranceCtor = window.SpeechSynthesisUtterance;
            // Also cancel parent if it was speaking
            try {{
                if (window.parent && window.parent.speechSynthesis) {{
                    window.parent.speechSynthesis.cancel();
                }}
            }} catch(e) {{}}
            if (synth && UtteranceCtor) {{
                speakLadyVoice(synth, UtteranceCtor, "{safe_text}", "{locale_code}");
            }}
        }}
        </script>
        <button onclick="playSpeech()" style="
            margin-top: 6px;
            width: 100%;
            padding: 10px 14px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #ffffff;
            cursor: pointer;
            font-size: 14px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s ease;
        ">
            🔊 Play Lady Voice Alert ({language_label})
        </button>
        """


# ============================================================
# 4. SESSION STATE & CONFIGURATION ENCAPSULATION (OOP)
# ============================================================

class SessionStateManager:
    """Encapsulates Streamlit session state access."""

    @staticmethod
    def initialize():
        if "active_scene_path" not in st.session_state:
            st.session_state["active_scene_path"] = "test.jpg"
        if "last_scene_token" not in st.session_state:
            st.session_state["last_scene_token"] = ""
        if "scrub_val" not in st.session_state:
            st.session_state["scrub_val"] = 60

    @classmethod
    def get_active_scene(cls) -> str:
        return st.session_state.get("active_scene_path", "test.jpg")

    @classmethod
    def set_active_scene(cls, path: str):
        st.session_state["active_scene_path"] = path

    @classmethod
    def get_last_scene_token(cls) -> str:
        return st.session_state.get("last_scene_token", "")

    @classmethod
    def set_last_scene_token(cls, token: str):
        st.session_state["last_scene_token"] = token


@dataclass
class CockpitConfig:
    """Encapsulates active user perception thresholds and filters."""
    conf_pothole: float
    conf_objects: float
    detect_potholes: bool
    detect_people: bool
    detect_vehicles: bool
    detect_animals: bool
    enable_voice: bool
    selected_language: str
    locale_code: str
    enable_tta: bool


# ============================================================
# 5. INSPECTION STRATEGIES (STRATEGY PATTERN)
# ============================================================

class AbstractInspectionStrategy(ABC):
    """Abstract Strategy interface for road hazard inspection modes."""

    @abstractmethod
    def render(self, config: CockpitConfig, detector: MultiHazardDetector) -> Optional[Tuple[Image.Image, str]]:
        pass


class ScenarioGalleryStrategy(AbstractInspectionStrategy):
    """Presets gallery strategy."""

    def render(self, config: CockpitConfig, detector: MultiHazardDetector) -> Optional[Tuple[Image.Image, str]]:
        with st.container(border=True):
            st.markdown("**Select a Road Hazard Scenario Preset:**")
            sc_col1, sc_col2, sc_col3, sc_col4 = st.columns(4)

            with sc_col1:
                is_active = (SessionStateManager.get_active_scene() == "test.jpg")
                if st.button("🌾 Savanna Wildlife", key="btn_test", width="stretch", type="primary" if is_active else "secondary"):
                    SessionStateManager.set_active_scene("test.jpg")
                st.caption("Savanna grassland: Dry grass, Lion, Cobra snake & wildlife")

            val_dir = os.path.join("dataset", "images", "val")
            road46 = os.path.join(val_dir, "road46.jpg")
            road47 = os.path.join(val_dir, "road47.jpg")
            road48 = os.path.join(val_dir, "road48.jpg")

            with sc_col2:
                if os.path.exists(road46):
                    is_active = (SessionStateManager.get_active_scene() == road46)
                    if st.button("🕳️ Rural Pothole Street", key="btn_r46", width="stretch", type="primary" if is_active else "secondary"):
                        SessionStateManager.set_active_scene(road46)
                    st.caption("Paved asphalt: Deep road craters & ruts")

            with sc_col3:
                if os.path.exists(road47):
                    is_active = (SessionStateManager.get_active_scene() == road47)
                    if st.button("🛣️ Pavement Surface Ruts", key="btn_r47", width="stretch", type="primary" if is_active else "secondary"):
                        SessionStateManager.set_active_scene(road47)
                    st.caption("High-speed highway asphalt ruts")

            with sc_col4:
                if os.path.exists(road48):
                    is_active = (SessionStateManager.get_active_scene() == road48)
                    if st.button("⚠️ Asphalt Wear Cluster", key="btn_r48", width="stretch", type="primary" if is_active else "secondary"):
                        SessionStateManager.set_active_scene(road48)
                    st.caption("Multiple surface wear depressions")

            active_path = SessionStateManager.get_active_scene()
            if active_path and os.path.exists(active_path):
                img = Image.open(active_path).convert("RGB")
                return img, f"Scenario: {os.path.basename(active_path)}"
        return None


class UploadPhotoStrategy(AbstractInspectionStrategy):
    """User photo file uploader strategy."""

    def render(self, config: CockpitConfig, detector: MultiHazardDetector) -> Optional[Tuple[Image.Image, str]]:
        with st.container(border=True):
            uploaded_file = st.file_uploader(
                "Upload any road photograph (JPG or PNG)",
                type=["jpg", "jpeg", "png"],
                key="custom_uploader"
            )
            if uploaded_file is not None:
                img = Image.open(uploaded_file).convert("RGB")
                return img, f"Uploaded Photo: {uploaded_file.name}"
        return None


class LiveCameraStrategy(AbstractInspectionStrategy):
    """Webcam snapshot input strategy."""

    def render(self, config: CockpitConfig, detector: MultiHazardDetector) -> Optional[Tuple[Image.Image, str]]:
        with st.container(border=True):
            st.markdown("**Capture Current Driving View from Device Camera**")
            cam_pic = st.camera_input("Take driving view snapshot")
            if cam_pic is not None:
                img = Image.open(cam_pic).convert("RGB")
                return img, "Live Device Camera Snapshot"
        return None


class DashcamVideoStrategy(AbstractInspectionStrategy):
    """Live video streaming and timeline scrubber strategy."""

    def render(self, config: CockpitConfig, detector: MultiHazardDetector) -> Optional[Tuple[Image.Image, str]]:
        video_p = "road_video.mp4"
        if not os.path.exists(video_p):
            st.warning("`road_video.mp4` not found in project directory.")
            return None

        cap_meta = cv2.VideoCapture(video_p)
        total_video_frames = int(cap_meta.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap_meta.get(cv2.CAP_PROP_FPS) or 25.0
        cap_meta.release()

        with st.container(border=True):
            dashcam_submode = st.segmented_control(
                "Select inspection mode:",
                options=[
                    "▶️ Live video stream (side-by-side)",
                    "🔍 Interactive frame timeline",
                    "🎥 Original video player"
                ],
                default="▶️ Live video stream (side-by-side)"
            )

            if dashcam_submode == "▶️ Live video stream (side-by-side)":
                st.markdown("**Live Real-Time Dashcam Stream with Dual-Engine Hazard Perception**")
                c_start, c_step, c_len, c_btn = st.columns([1.2, 1.2, 1.2, 1])
                with c_start:
                    start_sec = st.selectbox(
                        "Start from checkpoint:",
                        [
                            "Road Entry (Frame 0)",
                            "First Craters (Frame 30)",
                            "Major Crater Cluster (Frame 60)",
                            "Deep Rut Stretch (Frame 120)",
                            "Rough Dirt Section (Frame 250)",
                            "Exit Stretch (Frame 600)"
                        ],
                        index=2
                    )
                    start_map = {
                        "Road Entry (Frame 0)": 0,
                        "First Craters (Frame 30)": 30,
                        "Major Crater Cluster (Frame 60)": 60,
                        "Deep Rut Stretch (Frame 120)": 120,
                        "Rough Dirt Section (Frame 250)": 250,
                        "Exit Stretch (Frame 600)": 600
                    }
                    start_frame_idx = start_map.get(start_sec, 60)

                with c_step:
                    speed_opt = st.selectbox(
                        "Stream playback pacing:",
                        ["⚡ Fast Paced (Step 4 frames, ~20 FPS)", "🎯 Smooth (Step 2 frames, ~12 FPS)", "🔬 Precision (Every frame, ~4 FPS)"],
                        index=0
                    )
                    step_map = {
                        "⚡ Fast Paced (Step 4 frames, ~20 FPS)": 4,
                        "🎯 Smooth (Step 2 frames, ~12 FPS)": 2,
                        "🔬 Precision (Every frame, ~4 FPS)": 1
                    }
                    frame_step = step_map.get(speed_opt, 4)

                with c_len:
                    duration_opt = st.selectbox(
                        "Stream frame count:",
                        ["100 Frames (~4s)", "200 Frames (~8s)", "350 Frames (~14s)", "Full Drive (692 Frames)"],
                        index=1
                    )
                    duration_map = {
                        "100 Frames (~4s)": 100,
                        "200 Frames (~8s)": 200,
                        "350 Frames (~14s)": 350,
                        "Full Drive (692 Frames)": total_video_frames
                    }
                    max_stream_frames = duration_map.get(duration_opt, 200)

                with c_btn:
                    st.write("")
                    st.write("")
                    run_stream = st.button("▶️ Start Live Stream", type="primary", width="stretch")

                stream_hud = st.empty()
                stream_voice = st.empty()
                stream_prog = st.empty()
                stream_col1, stream_col2 = st.columns(2)
                feed_left = stream_col1.empty()
                feed_right = stream_col2.empty()
                stream_metrics = st.empty()

                if run_stream:
                    cap = cv2.VideoCapture(video_p)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_idx)
                    frames_processed = 0
                    curr_idx = start_frame_idx
                    last_voice_time = 0.0
                    last_hazard_state = None

                    while curr_idx < total_video_frames and frames_processed < max_stream_frames:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, curr_idx)
                        ret, v_frame = cap.read()
                        if not ret:
                            break

                        f_res = detector.detect_all(
                            v_frame,
                            conf_pothole=config.conf_pothole,
                            conf_objects=config.conf_objects,
                            detect_potholes=config.detect_potholes,
                            detect_people=config.detect_people,
                            detect_vehicles=config.detect_vehicles,
                            detect_animals=config.detect_animals,
                            augment_potholes=config.enable_tta
                        )

                        p_cnt = len(f_res["potholes"])
                        o_cnt = len(f_res["people"]) + len(f_res["animals"])
                        score = f_res["danger_score"]
                        t_status = f_res["terrain"]["surface_status"]

                        if score >= 80 or p_cnt >= 4 or (p_cnt >= 2 and o_cnt >= 1):
                            curr_state = "CRITICAL"
                            color_code = "#ef4444"
                            badge_cls = "hud-critical"
                            trans = localization_service.translate("CRITICAL_BRAKE_SLOW", language=config.selected_language)
                        elif p_cnt >= 1 or score >= 50 or o_cnt >= 1:
                            curr_state = "POTHOLE"
                            color_code = "#f59e0b"
                            badge_cls = "hud-warning"
                            trans = localization_service.translate("POTHOLE_NEARBY", language=config.selected_language)
                        else:
                            curr_state = "CLEAR"
                            color_code = "#10b981"
                            badge_cls = "hud-clear"
                            trans = localization_service.translate("PATH_CLEAR", language=config.selected_language)

                        now_ts = time.time()
                        elapsed_voice = now_ts - last_voice_time

                        # Announce only when hazard state changes (do not repeat repeatedly)
                        should_speak = False
                        if config.enable_voice:
                            if last_hazard_state is None:
                                should_speak = True
                            elif curr_state != last_hazard_state and elapsed_voice >= 3.5:
                                should_speak = True

                        if should_speak:
                            last_voice_time = now_ts
                            last_hazard_state = curr_state
                            safe_v_msg = trans.speech_browser.replace('"', '\\"').replace("'", "\\'")
                            browser_speech_script = f"""
                            <script>
                            (function() {{
                                try {{
                                    {LadyVoiceScriptFactory.HELPER_JS}
                                    let _synth = null;
                                    let _UCtor = null;
                                    try {{
                                        if (window.parent && window.parent.speechSynthesis) {{
                                            _synth = window.parent.speechSynthesis;
                                            _UCtor = window.parent.SpeechSynthesisUtterance;
                                        }}
                                    }} catch(e) {{}}
                                    if (!_synth) {{
                                        _synth = window.speechSynthesis;
                                        _UCtor = window.SpeechSynthesisUtterance;
                                    }}
                                    if (_synth && _UCtor) {{
                                        speakLadyVoice(_synth, _UCtor, "{safe_v_msg}", "{config.locale_code}");
                                    }}
                                }} catch(e) {{}}
                            }})();
                            </script>
                            """

                            stream_voice.html(
                                f"""
                                <div style="background: rgba(15, 23, 42, 0.90); border: 1px solid rgba(56, 189, 248, 0.45); border-radius: 10px; padding: 8px 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);">
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <span style="font-size: 18px;">🔊</span>
                                        <span style="font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 14px; color: #38bdf8; letter-spacing: 0.5px;">IN-CAB VOICE ADVISORY ({config.selected_language.upper()}):</span>
                                        <span style="font-weight: 600; font-size: 14px; color: #ffffff;">"{trans.text}"</span>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span class="hud-chip-live">● BROADCASTING</span>
                                    </div>
                                </div>
                                {browser_speech_script}
                                """,
                                unsafe_allow_javascript=True
                            )

                        orig_rgb = cv2.cvtColor(v_frame, cv2.COLOR_BGR2RGB)
                        ann_rgb = f_res["annotated_image"]

                        progress_val = min(1.0, (frames_processed + 1) / max_stream_frames)
                        stream_prog.progress(progress_val, text=f"Streaming Drive: Frame {curr_idx} of {total_video_frames} ({curr_idx/video_fps:.1f}s)")

                        stream_hud.html(
                            f"""
                            <div class="hud-card {badge_cls}" style="padding: 12px 20px; margin-bottom: 12px;">
                                <div style="display: flex; align-items: center; gap: 14px;">
                                    <span class="pulse-dot {'dot-red' if curr_state == 'CRITICAL' else ('dot-orange' if curr_state == 'POTHOLE' else 'dot-green')}"></span>
                                    <div>
                                        <div style="font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 16px; color: #ffffff;">
                                            LIVE ADAS STREAMING • {curr_state} HAZARD STATE
                                        </div>
                                        <div style="font-family: 'Rajdhani', sans-serif; font-weight: 600; font-size: 13px; color: #cbd5e1;">
                                            SURFACE: {t_status.upper()} • DETECTED CRATERS: {p_cnt} • THREAT INDEX: {score}/100
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <span class="hud-chip">LIVE FPS: {video_fps:.1f}</span>
                                </div>
                            </div>
                            """
                        )

                        feed_left.image(orig_rgb, caption=f"Original Dashcam Feed (Frame {curr_idx})", width="stretch")
                        feed_right.image(ann_rgb, caption=f"Dual-Engine Perception Overlay (Frame {curr_idx})", width="stretch")

                        curr_idx += frame_step
                        frames_processed += 1
                        time.sleep(0.02)

                    cap.release()
                    st.success("✅ Live stream playback completed.")

            elif dashcam_submode == "🔍 Interactive frame timeline":
                st.markdown("**Quick Jump to Road Sections:**")
                qb1, qb2, qb3, qb4, qb5, qb6 = st.columns(6)
                if qb1.button("🏁 Entry (0)", key="q0"): st.session_state["scrub_val"] = 0
                if qb2.button("🛣️ Ruts (30)", key="q30"): st.session_state["scrub_val"] = 30
                if qb3.button("🕳️ Crater (60)", key="q60"): st.session_state["scrub_val"] = 60
                if qb4.button("⚠️ Cluster (120)", key="q120"): st.session_state["scrub_val"] = 120
                if qb5.button("🚜 Rough (250)", key="q250"): st.session_state["scrub_val"] = 250
                if qb6.button("🌲 Exit (600)", key="q600"): st.session_state["scrub_val"] = 600

                scrub_frame = st.slider(
                    "Timeline Scrubber (Frame 0 to 692):",
                    min_value=0,
                    max_value=total_video_frames - 1,
                    value=st.session_state.get("scrub_val", 60),
                    step=5,
                    help="Drag slider to inspect detection at any point in the video."
                )
                st.session_state["scrub_val"] = scrub_frame

                cap = cv2.VideoCapture(video_p)
                cap.set(cv2.CAP_PROP_POS_FRAMES, scrub_frame)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    selected_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    return selected_image, f"Dashcam Timeline: Frame {scrub_frame} ({scrub_frame/video_fps:.1f}s)"
            else:
                st.video(video_p)
                st.info("💡 **Standalone Real-Time Mode**: For native 30+ FPS hardware acceleration run: `python final_demo.py`")

        return None


class InspectionStrategyFactory:
    """Factory Pattern for instantiating the selected inspection strategy."""

    @staticmethod
    def get_strategy(input_mode: str) -> AbstractInspectionStrategy:
        if input_mode == "🖼️ Scenario gallery":
            return ScenarioGalleryStrategy()
        elif input_mode == "📷 Upload road photo":
            return UploadPhotoStrategy()
        elif input_mode == "📹 Live camera snapshot":
            return LiveCameraStrategy()
        elif input_mode == "🎬 Dashcam video stream":
            return DashcamVideoStrategy()
        return ScenarioGalleryStrategy()


# ============================================================
# 6. APPLICATION CONTROLLER (OOP MAIN COCKPIT CONTROLLER)
# ============================================================

class SafeRouteCockpitApp:
    """
    Main Application Controller Class for SafeRouteAI.
    Coordinates models, services, views, and session states.
    """

    def __init__(self):
        AppStyling.inject()
        SessionStateManager.initialize()
        self.detector = self._load_detector()
        self.analyzer = self._load_analyzer()
        self.alert_manager = self._load_alert_manager()

    @st.cache_resource
    def _load_detector(_self):
        return MultiHazardDetector()

    @st.cache_resource
    def _load_analyzer(_self):
        return RiskAnalyzer()

    @st.cache_resource
    def _load_alert_manager(_self):
        return AlertManager(muted=True)

    def render_sidebar(self) -> CockpitConfig:
        with st.sidebar:
            st.image(
                "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=800&q=80",
                caption="SafeRouteAI Connected In-Cab ADAS",
                width="stretch"
            )

            st.html(
                """
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 12px; padding: 10px 14px; margin-bottom: 16px;">
                    <span style="font-family: 'Rajdhani', sans-serif; font-weight: 700; color: #38bdf8; font-size: 13px;">COCKPIT TELEMETRY</span>
                    <div style="font-size: 11px; color: #94a3b8;">DUAL CRATER NN • SPATIAL BARRIER • LIVE HUD</div>
                </div>
                """
            )

            st.markdown("##### ⚙️ Perception Sensitivity")
            conf_pothole = st.slider("Pothole detector confidence", 0.05, 0.85, 0.20, 0.05)
            conf_objects = st.slider("Obstacle detector confidence", 0.10, 0.65, 0.25, 0.05)

            st.markdown("##### 🛡️ Active Hazard Filters")
            selected_hazards = st.pills(
                "Hazard filters",
                ["Potholes", "Pedestrians", "Vehicles", "Livestock / Animals"],
                default=["Potholes", "Pedestrians", "Vehicles", "Livestock / Animals"],
                selection_mode="multi",
                label_visibility="collapsed"
            )

            st.markdown("##### 🔊 In-Cab Voice Announcer")
            enable_voice = st.toggle("Voice warnings enabled", value=True)

            selected_language = st.selectbox(
                "🌐 Preferred warning language",
                options=list(SUPPORTED_LANGUAGES.keys()),
                format_func=lambda lang: SUPPORTED_LANGUAGES[lang]["label"],
                index=0,
                help="Select language for in-cab voice warnings, driver advisories, and telemetry."
            )
            locale_code = localization_service.get_locale(selected_language)
            st.info(f"🎙️ **Active Voice:** Neural Lady ({selected_language})  \n🔇 **Desktop Man:** Permanently Muted")

            enable_tta = st.toggle("Enhanced multi-scale TTA inference", value=True)

            with st.container(border=True):
                st.markdown("**Core Specifications**")
                st.caption("• Primary Pothole NN: Fine-Grained Crater Head")
                st.caption("• Obstacle NN: YOLO11 Ultra-Light")
                st.caption("• Ground Reptile Scanner: ResNet-18 ImageNet")
                st.caption("• Spatial Barrier: Multi-Obstacle Protection")
                st.caption("• Processing Latency: ~180ms CPU / <25ms GPU")

            return CockpitConfig(
                conf_pothole=conf_pothole,
                conf_objects=conf_objects,
                detect_potholes="Potholes" in (selected_hazards or []),
                detect_people="Pedestrians" in (selected_hazards or []),
                detect_vehicles="Vehicles" in (selected_hazards or []),
                detect_animals="Livestock / Animals" in (selected_hazards or []),
                enable_voice=enable_voice,
                selected_language=selected_language,
                locale_code=locale_code,
                enable_tta=enable_tta
            )

    def render_hero(self):
        st.html(
            """
            <div class="cockpit-header">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                    <div>
                        <div class="cockpit-title">
                            <span>🚗 SafeRouteAI</span>
                            <span class="hud-chip">Cockpit HUD v3.0</span>
                            <span class="hud-chip-live">● SYSTEM ACTIVE</span>
                        </div>
                        <p class="cockpit-subtitle">
                            Real-Time Autonomous Road Hazard Perception • Spatial Threat Analysis • Intelligent Driver Assistance
                        </p>
                    </div>
                    <div class="radar-box">
                        <div class="radar-circle">
                            <div class="radar-sweep"></div>
                            <div class="radar-blip"></div>
                        </div>
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-family: 'Rajdhani', sans-serif; font-size: 13px; font-weight: 700; color: #38bdf8; letter-spacing: 0.6px;">
                                360° AI VISION SCANNER
                            </span>
                            <span style="font-size: 11px; color: #94a3b8;">
                                SURFACE & OBSTACLE FUSION
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            """
        )
        st.markdown(
            ":green-badge[AI Vision: Online] "
            ":blue-badge[Fine-Grained Crater NN] "
            ":purple-badge[Ground Reptile Scanner] "
            ":orange-badge[In-Cab Neural Lady Voice]"
        )
        st.space("small")

    def run(self):
        config = self.render_sidebar()
        self.render_hero()

        input_mode = st.segmented_control(
            "Select inspection feed:",
            options=[
                "🖼️ Scenario gallery",
                "📷 Upload road photo",
                "📹 Live camera snapshot",
                "🎬 Dashcam video stream"
            ],
            default="🖼️ Scenario gallery"
        )

        strategy = InspectionStrategyFactory.get_strategy(input_mode)
        feed_result = strategy.render(config, self.detector)

        if feed_result is None:
            return

        selected_image, image_source_label = feed_result
        if selected_image is None:
            return

        with st.spinner("Executing multi-hazard perception inference..."):
            results = self.detector.detect_all(
                selected_image,
                conf_pothole=config.conf_pothole,
                conf_objects=config.conf_objects,
                detect_potholes=config.detect_potholes,
                detect_people=config.detect_people,
                detect_vehicles=config.detect_vehicles,
                detect_animals=config.detect_animals,
                augment_potholes=config.enable_tta
            )

        potholes = results["potholes"]
        people = results["people"]
        vehicles = results["vehicles"]
        animals = results["animals"]
        terrain = results["terrain"]
        danger_score = results["danger_score"]

        assessment: RiskAssessmentResult = self.analyzer.analyze(
            pothole_count=len(potholes),
            confidences=[p["confidence"] for p in potholes],
            person_count=len(people),
            vehicle_count=len(vehicles),
            animal_count=len(animals),
            danger_score=danger_score,
            terrain=terrain,
            animals=animals,
            language=config.selected_language
        )

        risk_level = assessment.risk_level
        instruction = assessment.instruction
        alert_color = assessment.alert_color
        speech_browser = assessment.translation.speech_browser

        scene_token = f"{image_source_label}_{risk_level}_{instruction}_{config.selected_language}"
        scene_changed = (SessionStateManager.get_last_scene_token() != scene_token)

        if scene_changed and config.enable_voice:
            SessionStateManager.set_last_scene_token(scene_token)

        # 1. Dynamic HUD Banner
        hud_class = "hud-critical" if alert_color == "red" else ("hud-warning" if alert_color == "orange" else "hud-clear")
        dot_class = "dot-red" if alert_color == "red" else ("dot-orange" if alert_color == "orange" else "dot-green")
        hud_icon = "🚨" if alert_color == "red" else ("⚠️" if alert_color == "orange" else "🛡️")

        score = results['danger_score']
        circumference = 226.2
        dash_offset = circumference * (1 - (score / 100))
        meter_color = "#ef4444" if alert_color == "red" else ("#f59e0b" if alert_color == "orange" else "#10b981")

        speed_text = localization_service.get_speed_advisory(alert_color, language=config.selected_language)
        risk_label_text = localization_service.get_risk_label(risk_level, language=config.selected_language)

        if alert_color == "red":
            speed_bg = "rgba(239, 68, 68, 0.22)"
            speed_border = "1px solid #ef4444"
            speed_color = "#fca5a5"
        elif alert_color == "orange":
            speed_bg = "rgba(245, 158, 11, 0.22)"
            speed_border = "1px solid #f59e0b"
            speed_color = "#fcd34d"
        else:
            speed_bg = "rgba(16, 185, 129, 0.22)"
            speed_border = "1px solid #10b981"
            speed_color = "#6ee7b7"

        st.html(
            f"""
            <div class="hud-card {hud_class}">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <span class="pulse-dot {dot_class}"></span>
                    <div>
                        <div class="hud-msg">{hud_icon} {risk_label_text}</div>
                        <div class="hud-desc">{instruction}</div>
                        <div class="speed-advisory-pill" style="background: {speed_bg}; border: {speed_border}; color: {speed_color};">
                            {speed_text}
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px; flex-shrink: 0;">
                    <svg width="86" height="86" viewBox="0 0 86 86">
                        <circle cx="43" cy="43" r="36" stroke="rgba(255,255,255,0.12)" stroke-width="7" fill="none" />
                        <circle cx="43" cy="43" r="36" stroke="{meter_color}" stroke-width="7" fill="none"
                                stroke-dasharray="226.2" stroke-dashoffset="{dash_offset:.1f}"
                                stroke-linecap="round" transform="rotate(-90 43 43)"
                                style="transition: stroke-dashoffset 0.8s ease-in-out;" />
                        <text x="43" y="41" text-anchor="middle" font-family="'Orbitron', sans-serif" font-size="20" font-weight="800" fill="#ffffff">{score}</text>
                        <text x="43" y="55" text-anchor="middle" font-family="'Rajdhani', sans-serif" font-size="9" font-weight="700" fill="rgba(255,255,255,0.7)">THREAT</text>
                    </svg>
                </div>
            </div>
            """
        )

        # 2. In-Cab Neural Lady Audio Broadcast
        if scene_changed and config.enable_voice:
            auto_js = LadyVoiceScriptFactory.generate_auto_broadcast(
                speech_text=speech_browser,
                locale_code=config.locale_code,
                scene_token=scene_token
            )
            st.html(auto_js, unsafe_allow_javascript=True)

        # 3. Telemetry Metric Cards
        with st.container(horizontal=True):
            st.metric("Terrain surface", f"{terrain['icon']} {terrain['surface_status']}")
            st.metric("Potholes / ruts", len(potholes))
            st.metric("Pedestrians", len(people))
            st.metric("Vehicles", len(vehicles))
            st.metric("Livestock / Wildlife", len(animals))

        st.space("small")

        # 4. Visual Canvas & Audio Controls
        tab_visual, tab_data = st.tabs(["👁️ Visual Perception Feed", "📊 Hazard Diagnostics & Telemetry"])

        with tab_visual:
            v_col1, v_col2 = st.columns([2, 1])
            with v_col1:
                view_style = st.segmented_control(
                    "Display mode:",
                    options=["Side-by-side comparison", "AI detection overlay only", "Original photo only"],
                    default="Side-by-side comparison",
                    label_visibility="collapsed"
                )

            if view_style == "Side-by-side comparison":
                c1, c2 = st.columns(2)
                with c1:
                    with st.container(border=True):
                        st.markdown(f"**Original Road Scene** (`{image_source_label}`)")
                        st.image(selected_image, width="stretch")
                with c2:
                    with st.container(border=True):
                        st.markdown("**AI Hazard Detection Overlay**")
                        st.image(results["annotated_image"], width="stretch")
            elif view_style == "AI detection overlay only":
                with st.container(border=True):
                    st.markdown(f"**AI Hazard Detection Overlay** (`{image_source_label}`)")
                    st.image(results["annotated_image"], width="stretch")
            else:
                with st.container(border=True):
                    st.markdown(f"**Original Road Scene** (`{image_source_label}`)")
                    st.image(selected_image, width="stretch")

            # Audio Player Bar
            with st.container(border=True):
                col_audio, col_desc = st.columns([1, 2])
                with col_audio:
                    st.html(
                        """
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-weight: 700; font-size: 14px;">🔊 In-Cab Voice Announcer</span>
                            <div class="eq-container">
                                <span class="eq-bar bar-1"></span>
                                <span class="eq-bar bar-2"></span>
                                <span class="eq-bar bar-3"></span>
                                <span class="eq-bar bar-4"></span>
                                <span class="eq-bar bar-5"></span>
                            </div>
                        </div>
                        """
                    )

                    replay_btn_html = LadyVoiceScriptFactory.generate_replay_button(
                        speech_text=speech_browser,
                        locale_code=config.locale_code,
                        language_label=config.selected_language
                    )
                    st.html(replay_btn_html, unsafe_allow_javascript=True)

                with col_desc:
                    st.markdown("**Active Spoken Voice Guidance**")
                    st.info(f"\"{instruction}\"")

        with tab_data:
            chart_col, table_col = st.columns([1, 2])
            with chart_col:
                with st.container(border=True):
                    st.markdown("**Hazard Distribution Breakdown**")
                    counts_dict = {
                        "Potholes": len(potholes),
                        "Pedestrians": len(people),
                        "Vehicles": len(vehicles),
                        "Animals": len(animals)
                    }
                    st.bar_chart(counts_dict)

            with table_col:
                with st.container(border=True):
                    st.markdown("**Detected Hazards Coordinate Ledger**")
                    rows = []
                    for p in potholes:
                        rows.append({"Hazard": "Pothole", "Confidence": f"{p['confidence']:.1%}", "Area": f"{p.get('area_ratio', 0.0):.2%}", "Severity": p.get("severity", "N/A"), "Coordinates (x1, y1, x2, y2)": str(p['bbox'])})
                    for pe in people:
                        rows.append({"Hazard": "Pedestrian", "Confidence": f"{pe['confidence']:.1%}", "Area": f"{pe.get('area_ratio', 0.0):.2%}", "Severity": "High", "Coordinates (x1, y1, x2, y2)": str(pe['bbox'])})
                    for v in vehicles:
                        rows.append({"Hazard": f"Vehicle ({v['label']})", "Confidence": f"{v['confidence']:.1%}", "Area": f"{v.get('area_ratio', 0.0):.2%}", "Severity": "Low/Med", "Coordinates (x1, y1, x2, y2)": str(v['bbox'])})
                    for a in animals:
                        rows.append({"Hazard": a.get("display_name", a.get("label", "Animal")), "Confidence": f"{a['confidence']:.1%}", "Area": f"{a.get('area_ratio', 0.0):.2%}", "Severity": "Wildlife", "Coordinates (x1, y1, x2, y2)": str(a['bbox'])})

                    if rows:
                        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                    else:
                        st.write("No roadway hazards detected in current feed.")


# ============================================================
# MAIN APPLICATION ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    app = SafeRouteCockpitApp()
    app.run()
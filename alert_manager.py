import threading
import queue
import time
import os
import subprocess


class AlertManager:
    """
    Thread-safe ADAS Voice Alert Engine for SafeRouteAI.
    Uses dedicated background thread with Windows native SAPI.SpVoice
    for zero-latency, non-blocking, deadlock-free in-cab audio announcements.
    Includes PowerShell System.Speech fallback.
    """

    def __init__(self, muted=True):
        self.muted = muted
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def mute(self):
        """Mutes all desktop system audio output."""
        self.muted = True

    def unmute(self):
        """Unmutes desktop audio output."""
        self.muted = False

    def _worker_loop(self):
        sapi_voice = None
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            sapi_voice.Rate = 1  # Brisk, natural ADAS prompt speed
            sapi_voice.Volume = 100
            # Explicitly select a female voice (lady) if available, avoid male David voice
            try:
                for v in sapi_voice.GetVoices():
                    desc = v.GetDescription().lower()
                    if any(f in desc for f in ["zira", "female", "woman", "swara", "aarohi", "kalpana", "heera", "eva", "jenny"]):
                        sapi_voice.Voice = v
                        break
            except Exception:
                pass
        except Exception as e:
            print(f"AlertManager: SAPI initialization note: {e}. Will use PowerShell fallback if needed.")

        while True:
            item = self.queue.get()
            if item is None:
                break
            text, interrupt = item
            spoken = False

            if not self.muted and sapi_voice is not None:
                try:
                    # 2 = SVSFPurgeBeforeSpeak, 0 = Synchronous on this background worker thread
                    sapi_voice.Speak(text, 2 if interrupt else 0)
                    spoken = True
                except Exception as e:
                    print(f"AlertManager SAPI Speak error: {e}")

            if not self.muted and not spoken:
                try:
                    safe_msg = text.replace("'", "''").replace('"', '')
                    ps_cmd = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; try {{ $s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female) }} catch {{}}; $s.Speak('{safe_msg}')"
                    subprocess.run(
                        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                        capture_output=True,
                        timeout=8
                    )
                except Exception as ps_err:
                    print(f"AlertManager PowerShell fallback error: {ps_err}")

            self.queue.task_done()

    def speak(self, message, interrupt=True):
        if not message or not isinstance(message, str):
            return
        message = message.strip()
        if not message:
            return

        if self.muted:
            print("VOICE (MUTED DESKTOP MAN):", message)
            return

        print("VOICE:", message)

        if interrupt:
            # Purge pending stale queue messages so urgent driving warning plays immediately
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except Exception:
                    break

        self.queue.put((message, interrupt))


    # -------------------------------
    # ROAD CONDITIONS
    # -------------------------------

    def road_clear(self):
        self.speak("Path is clear. Keep moving.")

    def rough_road(self):
        self.speak("Uneven road. Reduce speed.")

    # -------------------------------
    # POTHOLES
    # -------------------------------

    def pothole_ahead(self):
        self.speak("Pothole nearby. Slow down and steer around it.")

    def large_pothole(self):
        self.speak("Deep pothole detected. Brake gently and avoid it.")

    def multiple_potholes(self):
        self.speak("Rough road section. Ride slowly and carefully.")

    # -------------------------------
    # PEOPLE
    # -------------------------------

    def person_ahead(self):
        self.speak("Person in your path. Slow down and use the horn.")

    def person_too_close(self):
        self.speak("Person very close. Brake and stop.")

    # -------------------------------
    # VEHICLES
    # -------------------------------

    def vehicle_ahead(self):
        self.speak("Vehicle in front. Keep a safe gap.")

    def vehicle_too_close(self):
        self.speak("Too close to the vehicle ahead. Reduce speed.")

    # -------------------------------
    # ANIMALS
    # -------------------------------

    def animal_ahead(self):
        self.speak("Animal on the road. Slow down and use the horn.")

    # -------------------------------
    # OBSTACLES
    # -------------------------------

    def obstacle_ahead(self):
        self.speak("Object blocking your path. Slow down and move around it.")

    def road_blocked(self):
        self.speak("Your path is blocked. Stop and choose another route.")

    # -------------------------------
    # DANGER
    # -------------------------------

    def multiple_hazards(self):
        self.speak("Multiple hazards detected. Reduce speed and stay alert.")

    def approaching_hazard(self):
        self.speak("Hazard approaching. Reduce speed now.")

    def immediate_danger(self):
        self.speak("Danger in your path. Brake and stop.")

    # -------------------------------
    # SAFE AGAIN
    # -------------------------------

    def hazard_cleared(self):
        self.speak("Hazard cleared. You may continue.")
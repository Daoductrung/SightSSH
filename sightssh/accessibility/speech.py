try:
    from accessible_output2.outputs import auto
    _HAS_AO2 = True
except ImportError:
    _HAS_AO2 = False

class SpeechManager:
    def __init__(self):
        self.speaker = None
        if _HAS_AO2:
            try:
                self.speaker = auto.Auto()
            except Exception:
                # Fallback or just ignore if initialization fails
                self.speaker = None

    def speak(self, text, interrupt=True):
        """
        Speaks the given text using the active screen reader or SAPI.
        interrupt: If True, stops previous speech before speaking.
        """
        if self.speaker:
            try:
                self.speaker.output(text, interrupt=interrupt)
            except Exception:
                pass # Silently fail if speech fails
        else:
            # Fallback for debugging if needed, or just do nothing
            # print(f"Speech: {text}") 
            pass

import wx
from sightssh.ui.main_frame import MainFrame
from sightssh.core.config_manager import ConfigManager
from sightssh.core.logger import setup_logging
from sightssh.core.i18n import set_language

class SightSSHApp(wx.App):
    def OnInit(self):
        # Setup logging early
        config = ConfigManager()
        setup_logging(config.get_log_dir())
        
        # Setup Language
        lang = config.get_settings().get("language", "en")
        set_language(lang)
        
        frame = MainFrame()
        frame.Show()
        self.SetTopWindow(frame)
        return True

def main():
    app = SightSSHApp()
    app.MainLoop()

if __name__ == "__main__":
    main()

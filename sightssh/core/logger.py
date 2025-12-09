import sys
import os
import logging
import traceback
from datetime import datetime

def setup_logging(log_dir):
    """
    Configures global application logging.
    Logs are written to 'app_error.log' in the specified directory.
    also sets up sys.excepthook to catch unhandled exceptions.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    log_file = os.path.join(log_dir, "app_error.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("SightSSH Application Started")
    logging.info(f"Log directory: {log_dir}")
    
    # Hook unhandled exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Optional: Last ditch effort to show error UI
        try:
            import wx
            err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            wx.MessageBox(f"Critical Error:\n{err_msg}", "Application Error", wx.ICON_ERROR)
        except:
            pass

    sys.excepthook = handle_exception

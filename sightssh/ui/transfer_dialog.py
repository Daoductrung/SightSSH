import wx
import threading
import os
from sightssh.core.i18n import tr

class TransferProgressDialog(wx.Dialog):
    def __init__(self, parent, title=None):
        if title is None: title = tr("dlg_transfer_title")
        super().__init__(parent, title=title, size=(400, 200))
        self.is_cancelled = False
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.lbl_file = wx.StaticText(self, label=tr("msg_transfer_preparing"))
        self.gauge = wx.Gauge(self, range=100)
        self.btn_cancel = wx.Button(self, label=tr("btn_cancel"))
        
        self.sizer.Add(self.lbl_file, 0, wx.ALL | wx.EXPAND, 10)
        self.sizer.Add(self.gauge, 0, wx.ALL | wx.EXPAND, 10)
        self.sizer.Add(self.btn_cancel, 0, wx.ALL | wx.CENTER, 10)
        
        self.SetSizer(self.sizer)
        
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.Bind(wx.EVT_CLOSE, self.on_cancel)
        self.btn_cancel.SetFocus()
        self.CenterOnParent()
        
    def on_cancel(self, event):
        self.is_cancelled = True
        self.lbl_file.SetLabel(tr("msg_transfer_cancelling"))
        self.btn_cancel.Disable()

    def update_progress(self, transferred, total):
        if total > 0:
            percent = int((transferred / total) * 100)
            wx.CallAfter(self.gauge.SetValue, percent)
    
    def set_filename(self, name):
        wx.CallAfter(self.lbl_file.SetLabel, tr("msg_transferring").format(name=name))

    def check_cancel(self):
        if self.is_cancelled:
            raise Exception(tr("err_transfer_cancelled"))

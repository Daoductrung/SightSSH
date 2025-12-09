import wx

class PasswordDialog(wx.Dialog):
    def __init__(self, parent, title="Enter Password", message="Please enter password:"):
        super().__init__(parent, title=title)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self, label=message)
        sizer.Add(label, 0, wx.ALL, 10)
        
        self.password_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        sizer.Add(self.password_ctrl, 0, wx.EXPAND | wx.ALL, 10)
        
        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btns, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizerAndFit(sizer)
        self.CentreOnParent()
        
        # Explicitly focus the password field for screen readers
        # wx.CallAfter ensures it happens after dialog creation/layout
        wx.CallAfter(self.password_ctrl.SetFocus)

    def get_password(self):
        return self.password_ctrl.GetValue()

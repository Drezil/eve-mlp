import wx

from eve_mlp.gui.common import resource, icon_bundle


class TrayIcon(wx.TaskBarIcon):
    def __init__(self, parent):
        wx.TaskBarIcon.__init__(self)
        self.parent = parent
        self.config = parent.config
        self.SetIcon(wx.Icon(resource("icon.ico"), wx.BITMAP_TYPE_ICO, desiredWidth=16, desiredHeight=16), "Mobile Launcher Platform")
        #self.SetIcons(icon_bundle(resource("icon.ico")), "Mobile Launcher Platform")
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnLeftDClick)
        self.CreateMenu()

    def CreateMenu(self):
        self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.OnPopup)
        self.menu = wx.Menu()

        for n, username in enumerate(self.config["usernames"]):
            m_launch = self.menu.Append(3000 + n, 'Launch '+username)
            self.Bind(wx.EVT_MENU, self.OnLaunch, m_launch)

        self.menu.AppendSeparator()
        m_launch_all = self.menu.Append(3200, 'Launch All')
        self.Bind(wx.EVT_MENU, self.OnLaunch, m_launch_all)

        self.menu.AppendSeparator()
        m_exit = self.menu.Append(wx.ID_EXIT, 'E&xit')
        self.Bind(wx.EVT_MENU, self.parent.OnClose, m_exit)

    def OnPopup(self, event):
        self.CreateMenu()  # refresh with latest usernames
        self.PopupMenu(self.menu)

    def OnLeftDClick(self, evt):
        if self.parent.IsShown():
            self.parent.Hide()
        else:
            self.parent.Show()

    def OnLaunch(self, evt):
        uid = evt.GetId() - 3000
        if uid == 200:
            for username in self.config["usernames"]:
                self.parent.launch(username)
        else:
            self.parent.launch(self.config["usernames"][uid])

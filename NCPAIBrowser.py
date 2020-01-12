import wx
from cefpython3 import cefpython as cef
import platform
import sys
import os
from configparser import ConfigParser

# Platforms
# V0.1版本适配Windows

# Globals
g_count_windows = 0

# Configuration 读取config.ini中的配置
conf = ConfigParser()
conf.read("config.ini", 'utf-8')
homeUrl = conf.get("main", "homeUrl");
specUrl = conf.get("main", "specUrl");
title = conf.get("main", "title");
remoteDebugingPort = conf.get("main", "remoteDebugingPort");
scaleHeight = conf.get("scale", "scaleHeight");
scaleWidth = conf.get("scale", "scaleWidth");


def main():
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    settings = {
        "context_menu": {
            # Disable context menu, popup widgets not supported
            "enabled": True,
            "print": False,
            "view_source": False,
            "external_browser": False,
        },
    }
    settings["remote_debugging_port"] = int(remoteDebugingPort)  # 设置参数：禁用远程debug
    cef.Initialize(settings=settings)
    app = NCPAIBrowser(False)
    app.MainLoop()
    del app  # Must destroy before calling Shutdown


def check_versions():
    print("[wxpython.py] CEF Python {ver}".format(ver=cef.__version__))
    print("[wxpython.py] Python {ver} {arch}".format(
        ver=platform.python_version(), arch=platform.architecture()[0]))
    print("[wxpython.py] wxPython {ver}".format(ver=wx.version()))
    # CEF Python version requirement
    assert cef.__version__ >= "66.0", "CEF Python v66.0+ required to run this"


def scale_window_size_for_high_dpi():
    """Scale window size for high DPI devices. This func can be
    called on all operating systems, but scales only for Windows.
    If scaled value is bigger than the work area on the display
    then it will be reduced."""
    (_, _, max_width, max_height) = wx.GetClientDisplayRect().Get()
    width = max_width * float(scaleWidth)
    height = max_height * float(scaleHeight)
    if width > max_width:
        width = max_width
    if height > max_height:
        height = max_height
    return width, height


class MainFrame(wx.Frame):

    def __init__(self):
        self.browser = None

        # Must ignore X11 errors like 'BadWindow' and others by
        # installing X11 error handlers. This must be done after
        # wx was intialized.
        global g_count_windows
        g_count_windows += 1

        print("[wxpython.py] System DPI settings: %s"
              % str(cef.DpiAware.GetSystemDpi()))
        if hasattr(wx, "GetDisplayPPI"):
            print("[wxpython.py] wx.GetDisplayPPI = %s" % wx.GetDisplayPPI())
        print("[wxpython.py] wx.GetDisplaySize = %s" % wx.GetDisplaySize())

        size = scale_window_size_for_high_dpi()
        print("[wxpython.py] MainFrame DPI scaled size: %s" % str(size))

        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title=title, size=size)
        # wxPython will set a smaller size when it is bigger
        # than desktop size.
        print("[wxpython.py] MainFrame actual size: %s" % self.GetSize())

        self.setup_icon()
        self.create_menu()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.browser_panel = wx.Panel(self, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.browser_panel.Bind(wx.EVT_SIZE, self.OnSize)

        self.embed_browser()
        self.Show()

    def setup_icon(self):
        icon_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 "resources", "wxpython.png")
        # wx.IconFromBitmap is not available on Linux in wxPython 3.0/4.0
        if os.path.exists(icon_file) and hasattr(wx, "IconFromBitmap"):
            icon = wx.IconFromBitmap(wx.Bitmap(icon_file, wx.BITMAP_TYPE_PNG))
            self.SetIcon(icon)

    def OnQuit(self, event):
        self.Close()

    def OnOpen(self, event):
        self.statusbar.SetStatusText('Open a File!')

    def onGoHome(self, event):
        self.browser.LoadUrl(homeUrl)

    def onGoSpec(self, event):
        self.browser.LoadUrl(specUrl)

    def create_menu(self):
        filemenu = wx.Menu()
        fitem = filemenu.Append(wx.ID_EXIT, "Quit", "Quit Applications")
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&Option")
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.OnQuit, fitem)
        toolBar = self.CreateToolBar()
        toolBar.AddSimpleTool(1, wx.Image('close.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), '关闭', '')
        toolBar.AddSeparator()
        toolBar.AddSimpleTool(2, wx.Image('home.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), '回到首页', '')
        toolBar.AddSeparator()
        toolBar.AddSimpleTool(3, wx.Image('spec.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), '打开定制页', '')
        toolBar.Realize()
        wx.EVT_TOOL(self, 1, self.OnQuit)
        wx.EVT_TOOL(self, 2, self.onGoHome)
        wx.EVT_TOOL(self, 3, self.onGoSpec)

    def embed_browser(self):
        window_info = cef.WindowInfo()
        (width, height) = self.browser_panel.GetClientSize().Get()
        assert self.browser_panel.GetHandle(), "Window handle not available"
        window_info.SetAsChild(self.browser_panel.GetHandle(),
                               [0, 0, width, height])
        self.browser = cef.CreateBrowserSync(window_info,
                                             url=homeUrl)
        # self.browser.SetClientHandler()

    def OnSetFocus(self, _):
        if not self.browser:
            return
        cef.WindowUtils.OnSetFocus(self.browser_panel.GetHandle(),
                                   0, 0, 0)
        self.browser.SetFocus(True)

    def OnSize(self, _):
        if not self.browser:
            return
        cef.WindowUtils.OnSize(self.browser_panel.GetHandle(),
                               0, 0, 0)
        self.browser.NotifyMoveOrResizeStarted()

    def OnClose(self, event):
        print("[wxpython.py] OnClose called")
        if not self.browser:
            # May already be closing, may be called multiple times on Mac
            return
        # Calling browser.CloseBrowser() and/or self.Destroy()
        # in OnClose may cause app crash on some paltforms in
        # some use cases, details in Issue #107.
        self.browser.ParentWindowWillClose()
        event.Skip()
        self.clear_browser_references()

    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None


class NCPAIBrowser(wx.App):

    def __init__(self, redirect):
        self.timer = None
        self.timer_id = 1
        self.is_initialized = False
        super(NCPAIBrowser, self).__init__(redirect=redirect)

    def OnPreInit(self):
        super(NCPAIBrowser, self).OnPreInit()

    def OnInit(self):
        self.initialize()
        return True

    def initialize(self):
        if self.is_initialized:
            return
        self.is_initialized = True
        self.create_timer()
        frame = MainFrame()
        self.SetTopWindow(frame)
        frame.Show()

    def create_timer(self):
        # See also "Making a render loop":
        # http://wiki.wxwidgets.org/Making_a_render_loop
        # Another way would be to use EVT_IDLE in MainFrame.
        self.timer = wx.Timer(self, self.timer_id)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(10)  # 10ms timer

    def on_timer(self, _):
        cef.MessageLoopWork()

    def OnExit(self):
        self.timer.Stop()
        return 0


if __name__ == '__main__':
    main()

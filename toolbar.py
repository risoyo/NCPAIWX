import wx


class ToolBarFrame(wx.Frame):

    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, 'ToolBar', size=(300, 200))

        panel = wx.Panel(self)

        panel.SetBackgroundColour('white')

        statusBar = self.CreateStatusBar()

        toolBar = self.CreateToolBar()

        toolBar.AddSimpleTool(wx.NewId(), wx.Bitmap('new.bmp'), "New", "long help for 'New'")

        toolBar.Realize()

        menuBar = wx.MenuBar()

        menu1 = wx.Menu()

        menuBar.Append(menu1, "&File")

        menu2 = wx.Menu()

        menu2.Append(wx.NewId(), "&Copy", "Copy in status bar")

        menu2.Append(wx.NewId(), "&Cut", "")

        menu2.Append(wx.NewId(), "Paste", "")

        menu2.AppendSeparator()

        menu2.Append(wx.NewId(), "&Options...", "Display Option")

        menuBar.Append(menu2, "&Edit")

        self.SetMenuBar(menuBar)


if __name__ == '__main__':
    app = wx.PySimpleApp()

    frame = ToolBarFrame(parent=None, id=-1)

    frame.Show()

    app.MainLoop()

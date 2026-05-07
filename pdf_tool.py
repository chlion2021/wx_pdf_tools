import wx
import wx.lib.mixins.listctrl as listmix
import PyPDF2
import os
from typing import List, Tuple
import threading

class PDFFileListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """PDF文件列表控件"""
    def __init__(self, parent, ID):
        wx.ListCtrl.__init__(self, parent, ID, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        # 设置列
        self.InsertColumn(0, '文件名', width=300)
        self.InsertColumn(1, '页数', width=80)
        self.InsertColumn(2, '文件路径', width=400)
        
    def add_file(self, file_path: str, page_count: int):
        """添加文件到列表"""
        index = self.GetItemCount()
        filename = os.path.basename(file_path)
        self.InsertItem(index, filename)
        self.SetItem(index, 1, str(page_count))
        self.SetItem(index, 2, file_path)
        
    def remove_selected(self):
        """删除选中的项目"""
        selected = self.GetFirstSelected()
        while selected != -1:
            self.DeleteItem(selected)
            selected = self.GetFirstSelected()
            
    def get_all_files(self) -> List[str]:
        """获取所有文件路径"""
        files = []
        for i in range(self.GetItemCount()):
            file_path = self.GetItem(i, 2).GetText()
            files.append(file_path)
        return files

class AboutDialog(wx.Dialog):
    """关于对话框，显示图片"""
    def __init__(self, parent):
        # 设置窗口大小：宽度比高度大1.5倍，高度设为600，宽度为900
        super().__init__(parent, title="关于", size=(900, 600))
        
        # 获取图片路径（假设about.png在程序同目录下）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "about.png")
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 创建可滚动的窗口来显示图片
        scrolled_window = wx.ScrolledWindow(panel, style=wx.SUNKEN_BORDER)
        scrolled_window.SetScrollRate(5, 5)
        
        # 尝试加载图片
        try:
            if os.path.exists(image_path):
                # 加载图片
                image = wx.Image(image_path, wx.BITMAP_TYPE_PNG)
                
                # 获取图片原始尺寸
                img_width = image.GetWidth()
                img_height = image.GetHeight()
                
                # 如果图片宽度超过窗口宽度（减去一些边距），按比例缩放
                max_width = 850  # 窗口宽度900减去边距
                if img_width > max_width:
                    scale = max_width / img_width
                    new_width = max_width
                    new_height = int(img_height * scale)
                    image = image.Scale(new_width, new_height, wx.IMAGE_QUALITY_HIGH)
                
                # 创建静态位图
                bitmap = wx.StaticBitmap(scrolled_window, bitmap=wx.Bitmap(image))
                
                # 设置滚动窗口大小以适应图片
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(bitmap, 0, wx.ALL, 10)
                scrolled_window.SetSizer(sizer)
                
                # 设置滚动窗口的虚拟大小
                scrolled_window.SetVirtualSize(image.GetWidth() + 20, image.GetHeight() + 20)
            else:
                # 如果图片不存在，显示提示
                error_text = wx.StaticText(scrolled_window, label=f"找不到图片文件: about.png\n请确保图片文件在程序目录下。\n\n程序目录: {script_dir}")
                error_text.SetForegroundColour(wx.Colour(255, 0, 0))
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(error_text, 0, wx.ALL | wx.EXPAND, 20)
                scrolled_window.SetSizer(sizer)
                scrolled_window.SetVirtualSize(850, 200)
                
        except Exception as e:
            error_text = wx.StaticText(scrolled_window, label=f"加载图片失败: {str(e)}")
            error_text.SetForegroundColour(wx.Colour(255, 0, 0))
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(error_text, 0, wx.ALL | wx.EXPAND, 20)
            scrolled_window.SetSizer(sizer)
            scrolled_window.SetVirtualSize(850, 200)
        
        vbox.Add(scrolled_window, 1, wx.EXPAND | wx.ALL, 10)
        
        # 添加关闭按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        close_btn = wx.Button(panel, label="关闭", size=(100, 35))
        close_btn.Bind(wx.EVT_BUTTON, lambda event: self.Close())
        btn_sizer.Add(close_btn, 0, wx.ALIGN_CENTER)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        panel.SetSizer(vbox)
        
        # 设置窗口位置居中
        self.Centre()

class PDFSplitDialog(wx.Dialog):
    """PDF分割对话框"""
    def __init__(self, parent, pdf_path: str, total_pages: int):
        # 调整窗口大小为原来的1.5倍 (600*1.5=900, 500*1.5=750)
        super().__init__(parent, title="分割PDF - 输入页码后，分割前务必先按[添加范围]按钮", size=(900, 750))
        self.pdf_path = pdf_path
        self.total_pages = total_pages
        self.split_ranges = []
        
        self.init_ui()
        self.Centre()
        
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 文件信息
        info_text = f"文件: {os.path.basename(self.pdf_path)}\n总页数: {self.total_pages}"
        info_label = wx.StaticText(panel, label=info_text)
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        info_label.SetFont(font)
        vbox.Add(info_label, flag=wx.ALL | wx.EXPAND, border=15)
        
        # 快速分割按钮
        quick_btn_panel = wx.Panel(panel)
        quick_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        quick_label = wx.StaticText(quick_btn_panel, label="快速分割:")
        self.every_page_btn = wx.Button(quick_btn_panel, label="逐页分割", size=(120, 35))
        self.every_page_btn.Bind(wx.EVT_BUTTON, self.on_every_page_split)
        
        quick_btn_sizer.Add(quick_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=15)
        quick_btn_sizer.Add(self.every_page_btn)
        
        quick_btn_panel.SetSizer(quick_btn_sizer)
        vbox.Add(quick_btn_panel, flag=wx.ALL | wx.EXPAND, border=15)
        
        # 分割线
        line = wx.StaticLine(panel)
        vbox.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        
        # 分割范围输入
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label="自定义分割范围 (例如: 1-5,8,10-15):")
        self.range_text = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER, size=(300, -1))
        self.add_btn = wx.Button(panel, label="添加范围", size=(100, 35))
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_range)
        
        hbox1.Add(label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        hbox1.Add(self.range_text, proportion=1, flag=wx.RIGHT, border=10)
        hbox1.Add(self.add_btn)
        vbox.Add(hbox1, flag=wx.ALL | wx.EXPAND, border=15)
        
        # 分割范围列表 - 增加列宽以适应更大的窗口
        self.range_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.range_list.InsertColumn(0, '页码范围', width=300)
        self.range_list.InsertColumn(1, '页数', width=150)
        self.range_list.InsertColumn(2, '输出文件名', width=380)
        vbox.Add(self.range_list, proportion=1, flag=wx.ALL | wx.EXPAND, border=15)
        
        # 按钮
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.remove_btn = wx.Button(panel, label="删除选中", size=(100, 35))
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_range)
        self.clear_btn = wx.Button(panel, label="清空所有", size=(100, 35))
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_all)
        
        hbox2.Add(self.remove_btn, flag=wx.RIGHT, border=10)
        hbox2.Add(self.clear_btn, flag=wx.RIGHT, border=10)
        hbox2.AddStretchSpacer()
        
        self.ok_btn = wx.Button(panel, label="开始分割", size=(120, 40))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_split)
        self.cancel_btn = wx.Button(panel, label="取消", size=(100, 40))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        
        hbox2.Add(self.ok_btn, flag=wx.RIGHT, border=10)
        hbox2.Add(self.cancel_btn)
        vbox.Add(hbox2, flag=wx.ALL | wx.EXPAND, border=15)
        
        # 添加提示
        tip_text = "提示：\n• 单个页码: 5\n• 页码范围: 1-10\n• 多个范围: 1-5,8,10-15\n• 页码从1开始"
        tip_label = wx.StaticText(panel, label=tip_text)
        tip_label.SetForegroundColour(wx.Colour(100, 100, 100))
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        tip_label.SetFont(font)
        vbox.Add(tip_label, flag=wx.ALL | wx.EXPAND, border=15)
        
        panel.SetSizer(vbox)
        
    def parse_range(self, range_str: str) -> List[int]:
        """解析页码范围"""
        pages = set()
        parts = range_str.replace(' ', '').split(',')
        
        for part in parts:
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start < 1 or end > self.total_pages or start > end:
                        raise ValueError(f"无效范围: {part}")
                    pages.update(range(start, end + 1))
                except ValueError:
                    raise ValueError(f"无效范围格式: {part}")
            else:
                try:
                    page = int(part)
                    if page < 1 or page > self.total_pages:
                        raise ValueError(f"无效页码: {page}")
                    pages.add(page)
                except ValueError:
                    raise ValueError(f"无效页码格式: {part}")
        
        if not pages:
            raise ValueError("未指定有效的页码范围")
        
        return sorted(pages)
    
    def on_every_page_split(self, event):
        """逐页分割"""
        # 清空现有范围
        self.range_list.DeleteAllItems()
        self.split_ranges.clear()
        
        # 为每一页创建一个范围
        for i in range(1, self.total_pages + 1):
            range_str = str(i)
            pages = [i]
            output_name = f"page_{i:03d}.pdf"
            
            # 添加到列表
            index = self.range_list.GetItemCount()
            self.range_list.InsertItem(index, range_str)
            self.range_list.SetItem(index, 1, "1")
            self.range_list.SetItem(index, 2, output_name)
            
            # 存储范围数据
            self.split_ranges.append((pages, range_str, output_name))
        
        wx.MessageBox(f"已添加 {self.total_pages} 个分割范围，每页一个文件", 
                     "提示", wx.OK | wx.ICON_INFORMATION)
        
    def on_add_range(self, event):
        """添加分割范围"""
        range_str = self.range_text.GetValue().strip()
        if not range_str:
            wx.MessageBox("请输入分割范围", "提示", wx.OK | wx.ICON_WARNING)
            return
            
        try:
            pages = self.parse_range(range_str)
            
            # 生成默认文件名
            output_name = f"split_{len(self.split_ranges) + 1}.pdf"
            
            # 添加到列表
            index = self.range_list.GetItemCount()
            self.range_list.InsertItem(index, range_str)
            self.range_list.SetItem(index, 1, str(len(pages)))
            self.range_list.SetItem(index, 2, output_name)
            
            # 存储范围数据
            self.split_ranges.append((pages, range_str, output_name))
            
            # 清空输入框
            self.range_text.SetValue("")
            
        except ValueError as e:
            wx.MessageBox(str(e), "错误", wx.OK | wx.ICON_ERROR)
            
    def on_remove_range(self, event):
        """删除选中的分割范围"""
        selected = self.range_list.GetFirstSelected()
        if selected != -1:
            self.range_list.DeleteItem(selected)
            self.split_ranges.pop(selected)
            # 重新编号
            for i, (pages, range_str, _) in enumerate(self.split_ranges):
                self.range_list.SetItem(i, 2, f"split_{i + 1}.pdf")
                
    def on_clear_all(self, event):
        """清空所有分割范围"""
        if self.split_ranges:
            if wx.MessageBox("确定要清空所有分割范围吗？", "确认", 
                           wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                self.range_list.DeleteAllItems()
                self.split_ranges.clear()
            
    def on_split(self, event):
        """执行分割"""
        if not self.split_ranges:
            wx.MessageBox("请至少添加一个分割范围", "提示", wx.OK | wx.ICON_WARNING)
            return
            
        self.EndModal(wx.ID_OK)
        
    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def get_split_info(self):
        """获取分割信息"""
        return self.split_ranges

class PDFMergerSplitter(wx.Frame):
    """PDF合并分割主窗口"""
    def __init__(self):
        super().__init__(None, title="PDF合并分割工具 作者:陈宏宇 微信：chenhongyusnow 20260119 赠人玫瑰，手有余香", size=(1000, 700))
        self.init_ui()
        self.Centre()
        
    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建标签页
        notebook = wx.Notebook(panel)
        
        # 合并标签页
        merge_panel = self.create_merge_panel(notebook)
        notebook.AddPage(merge_panel, "PDF合并")
        
        # 分割标签页
        split_panel = self.create_split_panel(notebook)
        notebook.AddPage(split_panel, "PDF分割")
        
        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(main_sizer)
        
        # 创建状态栏
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("就绪")
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = wx.MenuBar()
        
        # 文件菜单
        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "退出\tCtrl+Q", "退出程序")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        menu_bar.Append(file_menu, "文件")
        
        # 帮助菜单
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "关于", "关于本程序")
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        menu_bar.Append(help_menu, "帮助")
        
        self.SetMenuBar(menu_bar)
        
    def create_merge_panel(self, parent):
        """创建合并面板"""
        panel = wx.Panel(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 文件列表
        self.merge_list = PDFFileListCtrl(panel, -1)
        vbox.Add(self.merge_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # 按钮面板
        btn_panel = wx.Panel(panel)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_btn = wx.Button(btn_panel, label="添加PDF文件")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_files)
        
        remove_btn = wx.Button(btn_panel, label="删除选中")
        remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_files)
        
        clear_btn = wx.Button(btn_panel, label="清空列表")
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_files)
        
        move_up_btn = wx.Button(btn_panel, label="上移")
        move_up_btn.Bind(wx.EVT_BUTTON, self.on_move_up)
        
        move_down_btn = wx.Button(btn_panel, label="下移")
        move_down_btn.Bind(wx.EVT_BUTTON, self.on_move_down)
        
        btn_sizer.Add(add_btn, flag=wx.RIGHT, border=5)
        btn_sizer.Add(remove_btn, flag=wx.RIGHT, border=5)
        btn_sizer.Add(clear_btn, flag=wx.RIGHT, border=5)
        btn_sizer.Add(move_up_btn, flag=wx.RIGHT, border=5)
        btn_sizer.Add(move_down_btn, flag=wx.RIGHT, border=5)
        btn_sizer.AddStretchSpacer()
        
        merge_btn = wx.Button(btn_panel, label="合并PDF", size=(100, -1))
        merge_btn.Bind(wx.EVT_BUTTON, self.on_merge_pdfs)
        btn_sizer.Add(merge_btn)
        
        btn_panel.SetSizer(btn_sizer)
        vbox.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(vbox)
        return panel
        
    def create_split_panel(self, parent):
        """创建分割面板"""
        panel = wx.Panel(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 文件选择
        file_panel = wx.Panel(panel)
        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.split_file_path = wx.TextCtrl(file_panel, style=wx.TE_READONLY)
        browse_btn = wx.Button(file_panel, label="选择PDF文件")
        browse_btn.Bind(wx.EVT_BUTTON, self.on_select_split_file)
        
        file_sizer.Add(wx.StaticText(file_panel, label="PDF文件:"), 
                      flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5)
        file_sizer.Add(self.split_file_path, 1, flag=wx.RIGHT, border=5)
        file_sizer.Add(browse_btn)
        
        file_panel.SetSizer(file_sizer)
        vbox.Add(file_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # 文件信息显示
        self.split_info = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 100))
        vbox.Add(self.split_info, 0, wx.EXPAND | wx.ALL, 5)
        
        # 分割按钮面板
        split_btn_panel = wx.Panel(panel)
        split_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        custom_split_btn = wx.Button(split_btn_panel, label="自定义分割", size=(150, 40))
        custom_split_btn.Bind(wx.EVT_BUTTON, self.on_custom_split)
        
        every_page_btn = wx.Button(split_btn_panel, label="逐页分割", size=(150, 40))
        every_page_btn.Bind(wx.EVT_BUTTON, self.on_every_page_split)
        
        split_btn_sizer.Add(custom_split_btn, flag=wx.RIGHT, border=20)
        split_btn_sizer.Add(every_page_btn)
        
        split_btn_panel.SetSizer(split_btn_sizer)
        vbox.Add(split_btn_panel, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(vbox)
        return panel
        
    def get_pdf_page_count(self, file_path: str) -> int:
        """获取PDF页数"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            wx.MessageBox(f"读取文件失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            return 0
            
    def on_add_files(self, event):
        """添加PDF文件"""
        with wx.FileDialog(self, "选择PDF文件", wildcard="PDF files (*.pdf)|*.pdf",
                          style=wx.FD_OPEN | wx.FD_MULTIPLE) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                paths = dialog.GetPaths()
                added_count = 0
                for path in paths:
                    if path.lower().endswith('.pdf'):
                        # 检查是否已存在
                        existing_files = self.merge_list.get_all_files()
                        if path not in existing_files:
                            page_count = self.get_pdf_page_count(path)
                            if page_count > 0:
                                self.merge_list.add_file(path, page_count)
                                added_count += 1
                if added_count > 0:
                    self.statusbar.SetStatusText(f"已添加 {added_count} 个文件")
                
    def on_remove_files(self, event):
        """删除选中的文件"""
        count = len(self.merge_list.get_all_files())
        self.merge_list.remove_selected()
        new_count = len(self.merge_list.get_all_files())
        self.statusbar.SetStatusText(f"已删除 {count - new_count} 个文件")
        
    def on_clear_files(self, event):
        """清空所有文件"""
        if self.merge_list.GetItemCount() > 0:
            if wx.MessageBox("确定要清空所有文件吗？", "确认", 
                           wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                self.merge_list.DeleteAllItems()
                self.statusbar.SetStatusText("已清空列表")
        
    def on_move_up(self, event):
        """上移文件"""
        selected = self.merge_list.GetFirstSelected()
        if selected > 0:
            # 交换数据
            for col in range(3):
                text1 = self.merge_list.GetItem(selected, col).GetText()
                text2 = self.merge_list.GetItem(selected-1, col).GetText()
                self.merge_list.SetItem(selected, col, text2)
                self.merge_list.SetItem(selected-1, col, text1)
            self.merge_list.Select(selected-1)
            self.statusbar.SetStatusText("已上移文件")
            
    def on_move_down(self, event):
        """下移文件"""
        selected = self.merge_list.GetFirstSelected()
        count = self.merge_list.GetItemCount()
        if selected >= 0 and selected < count - 1:
            # 交换数据
            for col in range(3):
                text1 = self.merge_list.GetItem(selected, col).GetText()
                text2 = self.merge_list.GetItem(selected+1, col).GetText()
                self.merge_list.SetItem(selected, col, text2)
                self.merge_list.SetItem(selected+1, col, text1)
            self.merge_list.Select(selected+1)
            self.statusbar.SetStatusText("已下移文件")
            
    def on_merge_pdfs(self, event):
        """合并PDF文件"""
        files = self.merge_list.get_all_files()
        if len(files) < 2:
            wx.MessageBox("请至少添加2个PDF文件进行合并", "提示", wx.OK | wx.ICON_WARNING)
            return
            
        # 选择保存路径
        with wx.FileDialog(self, "保存合并后的PDF", wildcard="PDF files (*.pdf)|*.pdf",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                output_path = dialog.GetPath()
                if not output_path.lower().endswith('.pdf'):
                    output_path += '.pdf'
                    
                self.statusbar.SetStatusText("正在合并PDF文件...")
                # 在后台线程中执行合并
                self.merge_pdfs_thread(files, output_path)
                
    def merge_pdfs_thread(self, files: List[str], output_path: str):
        """在线程中合并PDF"""
        def merge():
            try:
                pdf_merger = PyPDF2.PdfMerger()
                for file_path in files:
                    pdf_merger.append(file_path)
                    
                pdf_merger.write(output_path)
                pdf_merger.close()
                
                wx.CallAfter(self.show_merge_result, True, output_path)
            except Exception as e:
                wx.CallAfter(self.show_merge_result, False, str(e))
                
        thread = threading.Thread(target=merge)
        thread.daemon = True
        thread.start()
        
        # 显示进度对话框
        progress = wx.ProgressDialog("合并PDF", "正在合并PDF文件，请稍候...", 
                                    parent=self, style=wx.PD_APP_MODAL)
        progress.Pulse()
        
        # 等待线程完成
        thread.join()
        progress.Destroy()
        
    def show_merge_result(self, success: bool, message: str):
        """显示合并结果"""
        if success:
            self.statusbar.SetStatusText("合并完成")
            wx.MessageBox(f"PDF合并成功！\n保存位置: {message}", "成功", wx.OK | wx.ICON_INFORMATION)
        else:
            self.statusbar.SetStatusText("合并失败")
            wx.MessageBox(f"合并失败: {message}", "错误", wx.OK | wx.ICON_ERROR)
            
    def on_select_split_file(self, event):
        """选择要分割的PDF文件"""
        with wx.FileDialog(self, "选择要分割的PDF文件", wildcard="PDF files (*.pdf)|*.pdf",
                          style=wx.FD_OPEN) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                file_path = dialog.GetPath()
                self.split_file_path.SetValue(file_path)
                
                # 显示文件信息
                page_count = self.get_pdf_page_count(file_path)
                if page_count > 0:
                    file_size = os.path.getsize(file_path)
                    if file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.2f} KB"
                    else:
                        size_str = f"{file_size / (1024 * 1024):.2f} MB"
                        
                    self.split_info.SetValue(f"文件名: {os.path.basename(file_path)}\n"
                                            f"文件路径: {file_path}\n"
                                            f"总页数: {page_count} 页\n"
                                            f"文件大小: {size_str}")
                    self.statusbar.SetStatusText(f"已选择文件: {os.path.basename(file_path)}")
                    
    def on_custom_split(self, event):
        """自定义分割"""
        file_path = self.split_file_path.GetValue().strip()
        if not file_path:
            wx.MessageBox("请先选择要分割的PDF文件", "提示", wx.OK | wx.ICON_WARNING)
            return
            
        if not os.path.exists(file_path):
            wx.MessageBox("文件不存在，请重新选择", "错误", wx.OK | wx.ICON_ERROR)
            return
            
        page_count = self.get_pdf_page_count(file_path)
        if page_count == 0:
            return
            
        # 显示分割对话框
        dialog = PDFSplitDialog(self, file_path, page_count)
        if dialog.ShowModal() == wx.ID_OK:
            split_ranges = dialog.get_split_info()
            if split_ranges:
                # 选择输出目录
                with wx.DirDialog(self, "选择保存目录", 
                                 style=wx.DD_DEFAULT_STYLE) as dir_dialog:
                    if dir_dialog.ShowModal() == wx.ID_OK:
                        output_dir = dir_dialog.GetPath()
                        self.statusbar.SetStatusText("正在分割PDF文件...")
                        self.split_pdf_thread(file_path, split_ranges, output_dir)
                        
        dialog.Destroy()
        
    def on_every_page_split(self, event):
        """逐页分割"""
        file_path = self.split_file_path.GetValue().strip()
        if not file_path:
            wx.MessageBox("请先选择要分割的PDF文件", "提示", wx.OK | wx.ICON_WARNING)
            return
            
        if not os.path.exists(file_path):
            wx.MessageBox("文件不存在，请重新选择", "错误", wx.OK | wx.ICON_ERROR)
            return
            
        page_count = self.get_pdf_page_count(file_path)
        if page_count == 0:
            return
            
        # 确认逐页分割
        result = wx.MessageBox(f"确定要将PDF的 {page_count} 页逐页分割吗？\n将生成 {page_count} 个单独的PDF文件。",
                              "确认逐页分割", wx.YES_NO | wx.ICON_QUESTION)
        
        if result == wx.YES:
            # 选择输出目录
            with wx.DirDialog(self, "选择保存目录", 
                             style=wx.DD_DEFAULT_STYLE) as dir_dialog:
                if dir_dialog.ShowModal() == wx.ID_OK:
                    output_dir = dir_dialog.GetPath()
                    self.statusbar.SetStatusText("正在逐页分割PDF文件...")
                    
                    # 创建分割范围列表
                    split_ranges = []
                    for i in range(1, page_count + 1):
                        pages = [i]
                        range_str = str(i)
                        output_name = f"page_{i:03d}.pdf"
                        split_ranges.append((pages, range_str, output_name))
                    
                    self.split_pdf_thread(file_path, split_ranges, output_dir)
        
    def split_pdf_thread(self, file_path: str, split_ranges: List, output_dir: str):
        """在线程中分割PDF"""
        def split():
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    for i, (pages, range_str, output_name) in enumerate(split_ranges):
                        pdf_writer = PyPDF2.PdfWriter()
                        
                        for page_num in pages:
                            pdf_writer.add_page(pdf_reader.pages[page_num - 1])
                            
                        output_path = os.path.join(output_dir, output_name)
                        with open(output_path, 'wb') as output_file:
                            pdf_writer.write(output_file)
                            
                wx.CallAfter(self.show_split_result, True, output_dir, len(split_ranges))
            except Exception as e:
                wx.CallAfter(self.show_split_result, False, str(e), 0)
                
        thread = threading.Thread(target=split)
        thread.daemon = True
        thread.start()
        
        # 显示进度对话框
        progress = wx.ProgressDialog("分割PDF", "正在分割PDF文件，请稍候...", 
                                    parent=self, style=wx.PD_APP_MODAL)
        progress.Pulse()
        
        thread.join()
        progress.Destroy()
        
    def show_split_result(self, success: bool, message: str, count: int):
        """显示分割结果"""
        if success:
            self.statusbar.SetStatusText("分割完成")
            wx.MessageBox(f"PDF分割成功！\n共生成 {count} 个文件\n保存位置: {message}", 
                         "成功", wx.OK | wx.ICON_INFORMATION)
        else:
            self.statusbar.SetStatusText("分割失败")
            wx.MessageBox(f"分割失败: {message}", "错误", wx.OK | wx.ICON_ERROR)
            
    def on_exit(self, event):
        """退出程序"""
        self.Close()
        
    def on_about(self, event):
        """关于对话框"""
        about_dialog = AboutDialog(self)
        about_dialog.ShowModal()
        about_dialog.Destroy()

class PDFApp(wx.App):
    """PDF应用程序"""
    def OnInit(self):
        self.SetAppName("PDF合并分割工具")
        frame = PDFMergerSplitter()
        frame.Show()
        return True

def main():
    app = PDFApp()
    app.MainLoop()

if __name__ == "__main__":
    main()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import time
import requests
import os
import json
import random
import math
from urllib.parse import urlparse
import configparser
import getpass
import winreg
import shutil
import http.server
import socketserver
import sys

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多线程下载器")
        self.root.geometry("1050x700")
        self.root.resizable(True, True)
        # 居中显示窗口
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # 设置现代主题
        self.style = ttk.Style()
        
        # 检查是否支持ttk主题
        if sys.platform == 'win32':
            # Windows系统
            try:
                self.style.theme_use('vista')
            except:
                pass
        else:
            # 其他系统
            try:
                self.style.theme_use('clam')
            except:
                pass
        
        # 配置现代样式 - 使用更现代的色彩方案
        # 主色调：深蓝色系
        self.primary_color = '#1976D2'
        self.secondary_color = '#1565C0'
        self.background_color = '#f5f7fa'
        self.card_color = '#ffffff'
        self.text_color = '#263238'
        self.light_text = '#607D8B'
        self.success_color = '#43A047'
        self.warning_color = '#FB8C00'
        self.error_color = '#E53935'
        self.border_color = '#ECEFF1'
        self.hover_color = '#E3F2FD'
        
        # 配置基础样式
        self.style.configure('TFrame', background=self.background_color)
        self.style.configure('TLabel', background=self.background_color, foreground=self.text_color, font=('Segoe UI', 10))
        
        # 现代按钮样式 - 确保文本可见
        self.style.configure('TButton', font=('Segoe UI', 10, 'medium'), padding=8, foreground=self.text_color, background=self.card_color, relief='flat', borderwidth=1, bordercolor=self.border_color)
        self.style.map('TButton', 
            background=[('active', self.primary_color), ('!active', self.card_color), ('hover', self.hover_color)], 
            foreground=[('active', 'white'), ('!active', self.text_color), ('hover', self.text_color)],
            bordercolor=[('focus', self.primary_color), ('!focus', self.border_color)]
        )
        
        # 为侧边栏按钮创建特殊样式 - 确保文本可见
        self.style.configure('Sidebar.TButton', font=('Segoe UI', 10, 'medium'), padding=10, foreground='#333333', background='#ffffff', relief='flat', borderwidth=1, bordercolor='#ECEFF1')
        self.style.map('Sidebar.TButton', 
            background=[('active', '#1976D2'), ('!active', '#ffffff'), ('hover', '#E3F2FD')], 
            foreground=[('active', 'white'), ('!active', '#333333'), ('hover', '#333333')],
            bordercolor=[('focus', '#1976D2'), ('!focus', '#ECEFF1')]
        )
        
        # 现代输入框样式
        self.style.configure('TEntry', font=('Segoe UI', 10), padding=8, background=self.card_color, foreground=self.text_color, relief='flat', borderwidth=1, bordercolor=self.border_color)
        self.style.map('TEntry', 
            fieldbackground=[('focus', self.card_color), ('!focus', self.card_color)], 
            bordercolor=[('focus', self.primary_color), ('!focus', self.border_color)],
            lightcolor=[('focus', self.primary_color), ('!focus', self.border_color)]
        )
        
        # 其他控件样式
        self.style.configure('TScale', background=self.background_color)
        self.style.configure('TCheckbutton', background=self.background_color, foreground=self.text_color, font=('Segoe UI', 10))
        
        # 现代标签框样式
        self.style.configure('TLabelframe', background=self.background_color, font=('Segoe UI', 10, 'bold'), foreground=self.text_color, borderwidth=1, bordercolor=self.border_color)
        self.style.configure('TLabelframe.Label', background=self.background_color, font=('Segoe UI', 10, 'bold'), foreground=self.text_color, padding=5)
        
        # 现代树形视图样式
        self.style.configure('Treeview', font=('Segoe UI', 10), rowheight=32, background=self.card_color, foreground=self.text_color, fieldbackground=self.card_color, borderwidth=1, bordercolor=self.border_color)
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background=self.background_color, foreground=self.text_color, padding=8)
        self.style.map('Treeview', 
            background=[('selected', self.primary_color), ('!selected', self.card_color), ('hover', self.hover_color)], 
            foreground=[('selected', 'white'), ('!selected', self.text_color)]
        )
        
        # 滚动条样式
        self.style.configure('Vertical.TScrollbar', background=self.background_color, borderwidth=0, troughcolor=self.background_color, arrowcolor=self.light_text)
        self.style.map('Vertical.TScrollbar', 
            background=[('active', self.primary_color), ('!active', self.background_color)],
            arrowcolor=[('active', 'white'), ('!active', self.light_text)]
        )
        

        
        # 配置变量
        self.download_dir = os.getcwd()
        self.thread_count = 4
        self.auto_thread_threshold = 0
        self.ssl_verify = False
        self.allow_insecure_tls = False
        self.proxy_type = "不使用"
        self.proxy_config = {
            "address": "",
            "port": "",
            "use_ssl": False,
            "username": "",
            "password": ""
        }
        self.auto_start = False
        
        # 创建全局Session对象，用于连接池管理
        self.session = requests.Session()
        # 配置Session
        self.session.verify = not self.ssl_verify
        # 设置连接池大小
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=3)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 尝试读取设置文件
        self.read_settings()
        
        # 下载任务队列
        self.tasks = []
        self.task_id_counter = 0
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 启动HTTP服务器，用于接收浏览器扩展的请求
        self.start_http_server()
        
        # 创建左侧侧边栏 - 现代卡片式设计
        self.sidebar = ttk.Frame(self.main_frame, width=240, style='TFrame')
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 15), pady=15)
        
        # 侧边栏卡片
        sidebar_card = ttk.Frame(self.sidebar, style='TFrame')
        sidebar_card.pack(fill=tk.Y, padx=5, pady=5)
        
        # 侧边栏标题
        sidebar_title = ttk.Label(sidebar_card, text="多线程下载器", font=('Segoe UI', 14, 'bold'), foreground=self.primary_color)
        sidebar_title.pack(fill=tk.X, pady=20, padx=15)
        
        # 侧边栏按钮 - 使用标准tk按钮确保文本可见
        self.list_button = tk.Button(sidebar_card, text="📋 下载列表", command=self.show_main_page, 
                                    bg='#ffffff', fg='#333333', font=('Segoe UI', 10), 
                                    relief='flat', borderwidth=1, highlightbackground='#ECEFF1')
        self.list_button.pack(fill=tk.X, pady=6, padx=15)
        
        self.settings_button = tk.Button(sidebar_card, text="⚙️ 系统设置", command=self.show_settings_page, 
                                       bg='#ffffff', fg='#333333', font=('Segoe UI', 10), 
                                       relief='flat', borderwidth=1, highlightbackground='#ECEFF1')
        self.settings_button.pack(fill=tk.X, pady=6, padx=15)
        
        # 侧边栏底部间距
        sidebar_bottom = ttk.Frame(sidebar_card, height=50, style='TFrame')
        sidebar_bottom.pack(fill=tk.X, expand=True)
        
        # 版本信息
        version_label = ttk.Label(sidebar_card, text="版本 1.0.0", font=('Segoe UI', 9), foreground=self.light_text)
        version_label.pack(fill=tk.X, pady=15, padx=15)
        
        # 创建右侧主内容区
        self.content_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 主页面
        self.create_main_page()
        
        # 设置页面
        self.create_settings_page()
        
        # 默认显示主页面
        self.show_main_page()
    
    def create_main_page(self):
        # 主页面框架
        self.main_page = ttk.Frame(self.content_frame, style='TFrame')
        
        # 创建滚动容器
        self.main_canvas = tk.Canvas(self.main_page, bg=self.background_color)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建垂直滚动条
        self.main_scrollbar = ttk.Scrollbar(self.main_page, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 关联滚动条和画布
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        
        # 创建内部框架，放置所有内容
        self.main_inner_frame = ttk.Frame(self.main_canvas, style='TFrame')
        self.main_canvas.create_window((0, 0), window=self.main_inner_frame, anchor=tk.NW)
        
        # 当内部框架大小改变时，更新画布的滚动区域
        def on_main_frame_configure(event):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        
        self.main_inner_frame.bind("<Configure>", on_main_frame_configure)
        
        # 添加鼠标滚轮事件监听
        def on_main_scroll(event):
            # Windows平台的鼠标滚轮事件处理
            print(f"Main page mouse wheel event: delta={event.delta}")
            # 计算滚动量，根据delta值调整
            scroll_amount = -int(event.delta / 120) * 2
            # 使用scroll方法，可能更可靠
            self.main_canvas.yview_scroll(scroll_amount, "units")
        
        # 绑定鼠标滚轮事件到根窗口，这样无论鼠标悬停在哪里都能响应
        # 但我们会在处理函数中检查鼠标是否在主页面区域
        def on_root_scroll(event):
            # 检查鼠标是否在主页面区域
            if self.main_page.winfo_ismapped():
                on_main_scroll(event)
        
        # 绑定到根窗口
        self.root.bind("<MouseWheel>", on_root_scroll)
        
        # 标题栏
        self.title_frame = ttk.Frame(self.main_inner_frame, style='TFrame')
        self.title_frame.pack(fill=tk.X, pady=25, padx=20)
        
        self.title_label = ttk.Label(self.title_frame, text="多线程下载器", font=('Segoe UI', 20, 'bold'), foreground=self.primary_color)
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        # 下载链接输入区 - 现代卡片式设计
        self.url_frame = ttk.Frame(self.main_inner_frame, style='TFrame')
        self.url_frame.pack(fill=tk.X, pady=15, padx=20)
        
        # 输入框和按钮容器
        url_input_container = ttk.Frame(self.url_frame, style='TFrame')
        url_input_container.pack(fill=tk.X, padx=5, pady=5)
        
        self.url_entry = ttk.Entry(url_input_container, width=70)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.add_task_button = ttk.Button(url_input_container, text="添加任务", command=self.add_download_task)
        self.add_task_button.pack(side=tk.LEFT, padx=5, ipadx=15)
        
        # 下载任务列表 - 现代卡片式设计
        self.tasks_frame = ttk.Frame(self.main_inner_frame, style='TFrame')
        self.tasks_frame.pack(fill=tk.BOTH, expand=True, pady=15, padx=20)
        
        # 任务列表标题
        self.tasks_title_frame = ttk.Frame(self.tasks_frame, style='TFrame')
        self.tasks_title_frame.pack(fill=tk.X, pady=15)
        
        self.tasks_title_label = ttk.Label(self.tasks_title_frame, text="下载任务", font=('Segoe UI', 16, 'bold'), foreground=self.text_color)
        self.tasks_title_label.pack(side=tk.LEFT, padx=5)
        
        # 任务列表统计信息
        self.tasks_count_label = ttk.Label(self.tasks_title_frame, text="", font=('Segoe UI', 10), foreground=self.light_text)
        self.tasks_count_label.pack(side=tk.RIGHT, padx=5)
        
        # 任务列表树
        columns = ("id", "filename", "speed", "threads", "progress")
        self.tasks_tree = ttk.Treeview(self.tasks_frame, columns=columns, show="headings", height=18)
        
        # 配置列标题
        self.tasks_tree.heading("id", text="ID", anchor=tk.CENTER)
        self.tasks_tree.heading("filename", text="文件名", anchor=tk.W)
        self.tasks_tree.heading("speed", text="速度", anchor=tk.CENTER)
        self.tasks_tree.heading("threads", text="线程数", anchor=tk.CENTER)
        self.tasks_tree.heading("progress", text="进度", anchor=tk.CENTER)
        
        # 配置列宽和对齐方式
        self.tasks_tree.column("id", width=60, anchor=tk.CENTER)
        self.tasks_tree.column("filename", width=300, anchor=tk.W)
        self.tasks_tree.column("speed", width=120, anchor=tk.CENTER)
        self.tasks_tree.column("threads", width=80, anchor=tk.CENTER)
        self.tasks_tree.column("progress", width=200, anchor=tk.CENTER)
        
        # 存储进度条
        self.progress_bars = {}
        
        # 配置状态标签样式
        self.tasks_tree.tag_configure("downloading", foreground="#2196F3")
        self.tasks_tree.tag_configure("completed", foreground="#4CAF50")
        self.tasks_tree.tag_configure("cancelled", foreground="#FFC107")
        self.tasks_tree.tag_configure("error", foreground="#F44336")
        
        # 配置树形视图样式
        self.style.configure('Treeview', font=('Segoe UI', 10), rowheight=28)
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#f8f9fa')
        
        self.tasks_tree.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        self.tasks_scrollbar = ttk.Scrollbar(self.tasks_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscroll=self.tasks_scrollbar.set)
        self.tasks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态栏
        self.status_frame = ttk.Frame(self.main_inner_frame, style='TFrame')
        self.status_frame.pack(fill=tk.X, pady=15, padx=15)
        
        self.status_label = ttk.Label(self.status_frame, text="就绪", font=('Segoe UI', 9), foreground='#666666')
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 任务统计信息
        self.task_stats_label = ttk.Label(self.status_frame, text="任务数: 0", font=('Segoe UI', 9), foreground='#666666')
        self.task_stats_label.pack(side=tk.RIGHT, padx=10)
    
    def create_settings_page(self):
        # 设置页面框架
        self.settings_page = ttk.Frame(self.content_frame, style='TFrame')
        
        # 创建滚动容器
        self.settings_canvas = tk.Canvas(self.settings_page, bg=self.background_color)
        self.settings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建垂直滚动条
        self.settings_scrollbar = ttk.Scrollbar(self.settings_page, orient=tk.VERTICAL, command=self.settings_canvas.yview)
        self.settings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 关联滚动条和画布
        self.settings_canvas.configure(yscrollcommand=self.settings_scrollbar.set)
        
        # 创建内部框架，放置所有内容
        self.settings_inner_frame = ttk.Frame(self.settings_canvas, style='TFrame')
        self.settings_canvas.create_window((0, 0), window=self.settings_inner_frame, anchor=tk.NW)
        
        # 当内部框架大小改变时，更新画布的滚动区域
        def on_settings_frame_configure(event):
            self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))
        
        self.settings_inner_frame.bind("<Configure>", on_settings_frame_configure)
        
        # 添加鼠标滚轮事件监听
        def on_settings_scroll(event):
            # Windows平台的鼠标滚轮事件处理
            print(f"Settings page mouse wheel event: delta={event.delta}")
            # 计算滚动量，根据delta值调整
            scroll_amount = -int(event.delta / 120) * 2
            # 使用scroll方法，可能更可靠
            self.settings_canvas.yview_scroll(scroll_amount, "units")
        
        # 更新根窗口的滚动事件处理函数，添加对设置页面的支持
        def on_root_scroll(event):
            # 检查当前显示的是哪个页面
            if self.main_page.winfo_ismapped():
                # 主页面显示中
                # 计算滚动量，根据delta值调整
                scroll_amount = -int(event.delta / 120) * 2
                # 使用scroll方法，可能更可靠
                self.main_canvas.yview_scroll(scroll_amount, "units")
            elif self.settings_page.winfo_ismapped():
                # 设置页面显示中
                # 计算滚动量，根据delta值调整
                scroll_amount = -int(event.delta / 120) * 2
                # 使用scroll方法，可能更可靠
                self.settings_canvas.yview_scroll(scroll_amount, "units")
        
        # 重新绑定到根窗口
        self.root.bind("<MouseWheel>", on_root_scroll)
        
        # 标题栏
        self.settings_title_frame = ttk.Frame(self.settings_inner_frame, style='TFrame')
        self.settings_title_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.settings_title_label = ttk.Label(self.settings_title_frame, text="设置", font=('Segoe UI', 16, 'bold'))
        self.settings_title_label.pack(side=tk.LEFT, padx=5)
        
        # 线程数设置
        self.thread_frame = ttk.LabelFrame(self.settings_inner_frame, text="线程设置")
        self.thread_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.thread_row = ttk.Frame(self.thread_frame, style='TFrame')
        self.thread_row.pack(fill=tk.X, pady=10, padx=10)
        
        self.thread_label = ttk.Label(self.thread_row, text="线程数:")
        self.thread_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.thread_var = tk.IntVar(value=self.thread_count)
        self.thread_scale = ttk.Scale(self.thread_row, from_=1, to=1024, orient=tk.HORIZONTAL, variable=self.thread_var, length=400)
        self.thread_scale.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.thread_value_label = ttk.Label(self.thread_row, text=str(self.thread_count), width=6)
        self.thread_value_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        def update_thread_value(*args):
            self.thread_value_label.config(text=str(self.thread_var.get()))
        
        self.thread_var.trace_add("write", update_thread_value)
        
        # 为线程数滑块添加点击事件和键盘事件监听
        def on_thread_scale_click(event):
            # 开始监听键盘事件
            self.root.bind('<Left>', lambda e: self.adjust_scale_value(self.thread_var, -1, 1, 1024))
            self.root.bind('<Right>', lambda e: self.adjust_scale_value(self.thread_var, 1, 1, 1024))
            # 开始监听点击事件，检测是否点击了滑块以外的区域
            self.root.bind('<Button-1>', self.on_root_click)
        
        self.thread_scale.bind('<Button-1>', on_thread_scale_click)
        
        # 下载位置设置
        self.download_dir_frame = ttk.LabelFrame(self.settings_inner_frame, text="下载设置")
        self.download_dir_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.download_dir_row = ttk.Frame(self.download_dir_frame, style='TFrame')
        self.download_dir_row.pack(fill=tk.X, pady=10, padx=10)
        
        self.download_dir_entry = ttk.Entry(self.download_dir_row, width=60)
        self.download_dir_entry.insert(0, self.download_dir)
        self.download_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        self.browse_button = ttk.Button(self.download_dir_row, text="浏览", command=self.browse_download_dir)
        self.browse_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 自动添加线程设置
        self.auto_thread_frame = ttk.LabelFrame(self.settings_inner_frame, text="自动线程设置")
        self.auto_thread_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.auto_thread_row = ttk.Frame(self.auto_thread_frame, style='TFrame')
        self.auto_thread_row.pack(fill=tk.X, pady=10, padx=10)
        
        self.auto_thread_label = ttk.Label(self.auto_thread_row, text="自动添加线程阈值 (MB, 0禁用):")
        self.auto_thread_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.auto_thread_var = tk.IntVar(value=self.auto_thread_threshold)
        self.auto_thread_scale = ttk.Scale(self.auto_thread_row, from_=0, to=1000, orient=tk.HORIZONTAL, variable=self.auto_thread_var, length=350)
        self.auto_thread_scale.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.auto_thread_value_label = ttk.Label(self.auto_thread_row, text=str(self.auto_thread_threshold), width=6)
        self.auto_thread_value_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        def update_auto_thread_value(*args):
            self.auto_thread_value_label.config(text=str(self.auto_thread_var.get()))
        
        self.auto_thread_var.trace_add("write", update_auto_thread_value)
        
        # 为自动添加线程阈值滑块添加点击事件和键盘事件监听
        def on_auto_thread_scale_click(event):
            # 开始监听键盘事件
            self.root.bind('<Left>', lambda e: self.adjust_scale_value(self.auto_thread_var, -1, 0, 1000))
            self.root.bind('<Right>', lambda e: self.adjust_scale_value(self.auto_thread_var, 1, 0, 1000))
            # 开始监听点击事件，检测是否点击了滑块以外的区域
            self.root.bind('<Button-1>', self.on_root_click)
        
        self.auto_thread_scale.bind('<Button-1>', on_auto_thread_scale_click)
        
        # SSL设置
        self.ssl_frame = ttk.LabelFrame(self.settings_inner_frame, text="SSL设置")
        self.ssl_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.ssl_row = ttk.Frame(self.ssl_frame, style='TFrame')
        self.ssl_row.pack(fill=tk.X, pady=10, padx=10)
        
        self.ssl_var = tk.BooleanVar(value=self.ssl_verify)
        self.ssl_checkbutton = ttk.Checkbutton(self.ssl_row, text="检查服务器SSL", variable=self.ssl_var)
        self.ssl_checkbutton.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.allow_insecure_tls_var = tk.BooleanVar(value=False)
        self.allow_insecure_tls_checkbutton = ttk.Checkbutton(self.ssl_row, text="允许使用不安全的加密方法 (如 TLS 1.0)", variable=self.allow_insecure_tls_var)
        self.allow_insecure_tls_checkbutton.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 代理设置
        self.proxy_frame = ttk.LabelFrame(self.settings_inner_frame, text="代理设置")
        self.proxy_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.proxy_row1 = ttk.Frame(self.proxy_frame, style='TFrame')
        self.proxy_row1.pack(fill=tk.X, pady=10, padx=10)
        
        self.proxy_type_var = tk.StringVar(value=self.proxy_type)
        self.proxy_type_combobox = ttk.Combobox(self.proxy_row1, textvariable=self.proxy_type_var, values=["不使用", "跟随系统", "自定义"])
        self.proxy_type_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.proxy_type_combobox.bind("<<ComboboxSelected>>", self.on_proxy_type_change)
        
        # 自定义代理配置
        self.custom_proxy_frame = ttk.Frame(self.proxy_frame, style='TFrame')
        self.custom_proxy_frame.pack(fill=tk.X, expand=True, padx=10, pady=10)
        
        self.proxy_address_label = ttk.Label(self.custom_proxy_frame, text="地址:")
        self.proxy_address_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.proxy_address_entry = ttk.Entry(self.custom_proxy_frame, width=25)
        self.proxy_address_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.proxy_port_label = ttk.Label(self.custom_proxy_frame, text="端口:")
        self.proxy_port_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.proxy_port_entry = ttk.Entry(self.custom_proxy_frame, width=10)
        self.proxy_port_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.proxy_ssl_var = tk.BooleanVar(value=self.proxy_config["use_ssl"])
        self.proxy_ssl_checkbutton = ttk.Checkbutton(self.custom_proxy_frame, text="使用SSL", variable=self.proxy_ssl_var)
        self.proxy_ssl_checkbutton.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 自启动设置
        self.auto_start_frame = ttk.LabelFrame(self.settings_inner_frame, text="自启动设置")
        self.auto_start_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.auto_start_row = ttk.Frame(self.auto_start_frame, style='TFrame')
        self.auto_start_row.pack(fill=tk.X, pady=10, padx=10)
        
        self.auto_start_var = tk.BooleanVar(value=self.auto_start)
        self.auto_start_checkbutton = ttk.Checkbutton(self.auto_start_row, text="开机自启动", variable=self.auto_start_var)
        self.auto_start_checkbutton.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 浏览器扩展设置
        self.extension_frame = ttk.LabelFrame(self.settings_inner_frame, text="浏览器扩展")
        self.extension_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.extension_row = ttk.Frame(self.extension_frame, style='TFrame')
        self.extension_row.pack(fill=tk.X, pady=10, padx=10)
        
        # 为浏览器扩展按钮创建特殊样式，确保文本可见
        self.style.configure('Extension.TButton', font=('Segoe UI', 10), padding=8, foreground='#333333', background='#ffffff', relief='flat', borderwidth=1, bordercolor='#ECEFF1')
        self.style.map('Extension.TButton', 
            background=[('active', '#1976D2'), ('!active', '#ffffff'), ('hover', '#E3F2FD')], 
            foreground=[('active', 'white'), ('!active', '#333333'), ('hover', '#333333')],
            bordercolor=[('focus', '#1976D2'), ('!focus', '#ECEFF1')]
        )
        
        self.install_extension_button = ttk.Button(self.extension_row, text="生成扩展", command=self.install_extension, style='Extension.TButton')
        self.install_extension_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 添加底部间距
        self.bottom_spacer = ttk.Frame(self.settings_inner_frame, height=50, style='TFrame')
        self.bottom_spacer.pack(fill=tk.X, pady=10)
        
        # 初始禁用自定义代理输入
        self.update_proxy_ui()
        
        # 添加实时保存功能
        self.add_real_time_save()
    
    def browse_download_dir(self):
        directory = filedialog.askdirectory(initialdir=self.download_dir)
        if directory:
            self.download_dir_entry.delete(0, tk.END)
            self.download_dir_entry.insert(0, directory)
    
    def on_proxy_type_change(self, event):
        self.update_proxy_ui()
    
    def update_proxy_ui(self):
        proxy_type = self.proxy_type_var.get()
        state = tk.NORMAL if proxy_type == "自定义" else tk.DISABLED
        
        self.proxy_address_label.config(state=state)
        self.proxy_address_entry.config(state=state)
        self.proxy_port_label.config(state=state)
        self.proxy_port_entry.config(state=state)
        self.proxy_ssl_checkbutton.config(state=state)
    
    def install_extension(self):
        # 模拟生成浏览器扩展
        # 使用与程序同目录的browser_extension目录
        extension_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_extension")
        if not os.path.exists(extension_dir):
            os.makedirs(extension_dir)
        
        # 创建扩展文件
        manifest = {
            "name": "多线程下载器扩展",
            "version": "1.0",
            "description": "浏览器下载扩展",
            "manifest_version": 3,
            "permissions": ["downloads", "tabs"],
            "background": {
                "service_worker": "background.js"
            }
        }
        
        with open(os.path.join(extension_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        
        # 创建background.js文件，实现下载拦截和与下载器通信的逻辑
        background_js = '''
// 浏览器扩展背景脚本

// 直接指定下载器的端口号
const DOWNLOADER_PORT = 8089;

// 检测下载器是否运行的函数
async function isDownloaderRunning() {
  try {
    // 尝试与下载器通信
    const response = await fetch(`http://localhost:${DOWNLOADER_PORT}/ping`, {
      method: 'GET',
      timeout: 1000
    });
    return response.ok;
  } catch (error) {
    // 通信失败，下载器未运行
    return false;
  }
}

// 向下载器发送下载请求
async function sendDownloadToDownloader(url, filename, referrer) {
  try {
    await fetch(`http://localhost:${DOWNLOADER_PORT}/addDownload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: url,
        filename: filename,
        referrer: referrer
      })
    });
    return true;
  } catch (error) {
    console.error('Failed to send download to downloader:', error);
    return false;
  }
}

// 拦截下载事件
chrome.downloads.onDeterminingFilename.addListener(async (item, suggest) => {
  // 检测下载器是否运行
  const downloaderRunning = await isDownloaderRunning();
  
  if (downloaderRunning) {
    // 下载器运行，拦截下载并传递链接给下载器
    const success = await sendDownloadToDownloader(item.url, item.filename, item.referrer);
    
    if (success) {
      // 取消浏览器默认下载
      suggest({
        filename: item.filename,
        conflictAction: 'cancel'
      });
      
      console.log('Download intercepted and sent to downloader:', item.url);
    } else {
      // 通信失败，允许浏览器默认下载
      suggest();
    }
  } else {
    // 下载器未运行，允许浏览器默认下载
    suggest();
  }
});

// 监听来自内容脚本的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'download') {
    // 处理来自页面的下载请求
    handleDownloadRequest(message.url, message.filename);
    sendResponse({ success: true });
  }
});

// 处理下载请求
async function handleDownloadRequest(url, filename) {
  // 检测下载器是否运行
  const downloaderRunning = await isDownloaderRunning();
  
  if (downloaderRunning) {
    // 下载器运行，传递链接给下载器
    const success = await sendDownloadToDownloader(url, filename || url.split('/').pop());
    
    if (success) {
      console.log('Download request sent to downloader:', url);
    } else {
      // 下载器通信失败，使用浏览器默认下载
      chrome.downloads.download({ url: url, filename: filename });
    }
  } else {
    // 下载器未运行，使用浏览器默认下载
    chrome.downloads.download({ url: url, filename: filename });
  }
}
'''
        
        with open(os.path.join(extension_dir, "background.js"), "w", encoding="utf-8") as f:
            f.write(background_js)
        
        messagebox.showinfo("安装成功", f"浏览器扩展已生成至: {extension_dir}")
    
    def read_settings(self):
        # 尝试读取设置文件
        settings_file = "settings.ini"
        if os.path.exists(settings_file):
            config = configparser.ConfigParser()
            config.read(settings_file, encoding="utf-8")
            
            # 读取线程设置
            if "Settings" in config:
                if "thread_count" in config["Settings"]:
                    try:
                        thread_count = int(config["Settings"]["thread_count"])
                        if 1 <= thread_count <= 1024:
                            self.thread_count = thread_count
                    except ValueError:
                        pass
                
                if "download_dir" in config["Settings"]:
                    download_dir = config["Settings"]["download_dir"]
                    if os.path.exists(download_dir):
                        self.download_dir = download_dir
                
                if "auto_thread_threshold" in config["Settings"]:
                    try:
                        threshold = int(config["Settings"]["auto_thread_threshold"])
                        if threshold >= 0:
                            self.auto_thread_threshold = threshold
                    except ValueError:
                        pass
                
                if "ssl_verify" in config["Settings"]:
                    self.ssl_verify = config["Settings"]["ssl_verify"].lower() == "true"
                
                if "allow_insecure_tls" in config["Settings"]:
                    self.allow_insecure_tls = config["Settings"]["allow_insecure_tls"].lower() == "true"
                
                if "proxy_type" in config["Settings"]:
                    self.proxy_type = config["Settings"]["proxy_type"]
                
                if "auto_start" in config["Settings"]:
                    self.auto_start = config["Settings"]["auto_start"].lower() == "true"
            
            # 读取代理设置
            if "Proxy" in config:
                if "address" in config["Proxy"]:
                    self.proxy_config["address"] = config["Proxy"]["address"]
                if "port" in config["Proxy"]:
                    self.proxy_config["port"] = config["Proxy"]["port"]
                if "use_ssl" in config["Proxy"]:
                    self.proxy_config["use_ssl"] = config["Proxy"]["use_ssl"].lower() == "true"
    
    def set_auto_start(self, enable):
        # 设置自启动
        try:
            # 获取当前脚本路径
            script_path = os.path.abspath(__file__)
            script_name = os.path.basename(script_path)
            
            # 注册表路径
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            
            # 打开注册表
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if enable:
                # 设置自启动
                winreg.SetValueEx(key, "多线程下载器", 0, winreg.REG_SZ, f"pythonw.exe \"{script_path}\"")
            else:
                # 取消自启动
                try:
                    winreg.DeleteValue(key, "多线程下载器")
                except FileNotFoundError:
                    pass
            
            # 关闭注册表
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"设置自启动失败: {e}")
            return False
    
    def add_real_time_save(self):
        # 添加实时保存功能
        
        # 为线程数添加实时保存
        def on_thread_change(*args):
            self.save_settings()
        self.thread_var.trace_add("write", on_thread_change)
        
        # 为下载位置添加实时保存
        def on_download_dir_change(event):
            self.save_settings()
        self.download_dir_entry.bind("<FocusOut>", on_download_dir_change)
        
        # 为自动线程阈值添加实时保存
        def on_auto_thread_change(*args):
            self.save_settings()
        self.auto_thread_var.trace_add("write", on_auto_thread_change)
        
        # 为SSL设置添加实时保存
        def on_ssl_change(*args):
            self.save_settings()
        self.ssl_var.trace_add("write", on_ssl_change)
        self.allow_insecure_tls_var.trace_add("write", on_ssl_change)
        
        # 为代理设置添加实时保存
        def on_proxy_change(*args):
            self.save_settings()
        self.proxy_type_var.trace_add("write", on_proxy_change)
        self.proxy_address_entry.bind("<FocusOut>", on_proxy_change)
        self.proxy_port_entry.bind("<FocusOut>", on_proxy_change)
        self.proxy_ssl_var.trace_add("write", on_proxy_change)
        
        # 为自启动设置添加实时保存
        def on_auto_start_change(*args):
            self.save_settings()
        self.auto_start_var.trace_add("write", on_auto_start_change)
        
        # 为浏览按钮添加实时保存
        def browse_and_save():
            directory = filedialog.askdirectory(initialdir=self.download_dir)
            if directory:
                self.download_dir_entry.delete(0, tk.END)
                self.download_dir_entry.insert(0, directory)
                self.save_settings()
        
        # 替换浏览按钮的回调函数
        self.browse_button.config(command=browse_and_save)
    
    def start_http_server(self):
        # 创建HTTP服务器，用于接收浏览器扩展的请求
        class DownloadHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.downloader_app = kwargs.pop('downloader_app')
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                # 处理GET请求
                if self.path == '/ping':
                    # 检测下载器是否运行
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'pong')
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_POST(self):
                # 处理POST请求
                if self.path == '/addDownload':
                    # 接收下载链接
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        # 解析JSON数据
                        data = json.loads(post_data)
                        url = data.get('url')
                        filename = data.get('filename')
                        
                        if url:
                            # 添加下载任务
                            self.downloader_app.add_download_task_from_extension(url, filename)
                            
                            # 返回成功响应
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'success': True}).encode())
                        else:
                            # 缺少URL参数
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'success': False, 'error': 'Missing URL'}).encode())
                    except json.JSONDecodeError:
                        # JSON解析失败
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': False, 'error': 'Invalid JSON'}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # 禁用日志输出
                pass
        
        # 直接指定端口
        PORT = 8089
        Handler = lambda *args, **kwargs: DownloadHandler(*args, downloader_app=self, **kwargs)
        
        # 启动服务器线程
        def run_server():
            try:
                with socketserver.TCPServer(('', PORT), Handler) as httpd:
                    print(f"HTTP server started at http://localhost:{PORT}")
                    # 保存端口号到设置中
                    self.http_server_port = PORT
                    httpd.serve_forever()
            except Exception as e:
                print(f"HTTP server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
    
    def add_download_task_from_extension(self, url, filename=None):
        # 从浏览器扩展添加下载任务
        if not url:
            return
        
        # 创建下载任务
        task_id = self.task_id_counter
        self.task_id_counter += 1
        
        # 使用提供的文件名或从URL解析
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"download_{task_id}"
        
        # 创建任务对象
        task = {
            "id": task_id,
            "url": url,
            "filename": filename,
            "status": "等待中",
            "speed": "0 B/s",
            "threads": 0,
            "progress": 0,
            "total_size": 0,
            "downloaded_size": 0,
            "start_time": time.time(),
            "threads_list": [],
            "queue": queue.Queue(),
            "lock": threading.Lock()
        }
        
        self.tasks.append(task)
        
        # 添加到任务树
        # 初始进度条
        bar_length = 20
        initial_bar = "░" * bar_length
        self.tasks_tree.insert("", tk.END, iid=str(task_id), values=(
            task_id, filename, "0 B/s", "0", f"{initial_bar} 0%"
        ))
        
        # 更新任务统计信息
        self.update_task_stats()
        
        # 启动下载
        threading.Thread(target=self.start_download, args=(task,), daemon=True).start()
    
    def save_settings(self):
        # 保存线程数
        thread_count = self.thread_var.get()
        if 1 <= thread_count <= 1024:
            self.thread_count = thread_count
        else:
            messagebox.showerror("错误", "线程数必须在1-1024之间")
            return
        
        # 保存下载位置
        self.download_dir = self.download_dir_entry.get()
        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建下载目录: {e}")
                return
        
        # 保存自动线程阈值
        auto_thread_threshold = self.auto_thread_var.get()
        if auto_thread_threshold >= 0:
            self.auto_thread_threshold = auto_thread_threshold
        else:
            messagebox.showerror("错误", "自动添加线程阈值必须是非负数")
            return
        
        # 保存SSL设置
        self.ssl_verify = self.ssl_var.get()
        self.allow_insecure_tls = self.allow_insecure_tls_var.get()
        
        # 保存代理设置
        self.proxy_type = self.proxy_type_var.get()
        if self.proxy_type == "自定义":
            self.proxy_config["address"] = self.proxy_address_entry.get()
            self.proxy_config["port"] = self.proxy_port_entry.get()
            self.proxy_config["use_ssl"] = self.proxy_ssl_var.get()
        
        # 保存自启动设置
        new_auto_start = self.auto_start_var.get()
        if new_auto_start != self.auto_start:
            self.set_auto_start(new_auto_start)
            self.auto_start = new_auto_start
        
        # 写入设置文件
        settings_file = "settings.ini"
        config = configparser.ConfigParser()
        config["Settings"] = {
            "thread_count": str(self.thread_count),
            "download_dir": self.download_dir,
            "auto_thread_threshold": str(self.auto_thread_threshold),
            "ssl_verify": str(self.ssl_verify),
            "allow_insecure_tls": str(self.allow_insecure_tls),
            "proxy_type": self.proxy_type,
            "auto_start": str(self.auto_start)
        }
        config["Proxy"] = {
            "address": self.proxy_config["address"],
            "port": self.proxy_config["port"],
            "use_ssl": str(self.proxy_config["use_ssl"])
        }
        
        with open(settings_file, "w", encoding="utf-8") as f:
            config.write(f)
    
    def show_main_page(self):
        # 隐藏所有页面
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()
        
        # 显示主页面
        self.main_page.pack(fill=tk.BOTH, expand=True)
    
    def adjust_scale_value(self, var, delta, min_val, max_val):
        # 调整滑块的值
        current_value = var.get()
        new_value = current_value + delta
        # 确保值在范围内
        new_value = max(min_val, min(new_value, max_val))
        var.set(new_value)
    
    def on_root_click(self, event):
        # 检查点击是否在滑块以外的区域
        if not (event.widget == self.thread_scale or event.widget == self.auto_thread_scale):
            # 取消键盘事件监听
            self.root.unbind('<Left>')
            self.root.unbind('<Right>')
            # 取消点击事件监听
            self.root.unbind('<Button-1>')
    
    def show_settings_page(self):
        # 隐藏所有页面
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()
        
        # 显示设置页面
        self.settings_page.pack(fill=tk.BOTH, expand=True)
    
    def add_download_task(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入下载链接")
            return
        
        # 创建下载任务
        task_id = self.task_id_counter
        self.task_id_counter += 1
        
        # 解析文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = f"download_{task_id}"
        
        # 创建任务对象
        task = {
            "id": task_id,
            "url": url,
            "filename": filename,
            "status": "等待中",
            "speed": "0 B/s",
            "threads": 0,
            "progress": 0,
            "total_size": 0,
            "downloaded_size": 0,
            "start_time": time.time(),
            "threads_list": [],
            "queue": queue.Queue(),
            "lock": threading.Lock()
        }
        
        self.tasks.append(task)
        
        # 添加到任务树
        # 初始进度条
        bar_length = 20
        initial_bar = "░" * bar_length
        self.tasks_tree.insert("", tk.END, iid=str(task_id), values=(
            task_id, filename, "0 B/s", "0", f"{initial_bar} 0%"
        ))
        
        # 更新任务统计信息
        self.update_task_stats()
        
        # 启动下载
        threading.Thread(target=self.start_download, args=(task,), daemon=True).start()
    
    def start_download(self, task):
        try:
            # 检查链接是否有效
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            # 简化SSL处理，直接使用requests库发起GET请求
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # 更新session的SSL验证设置
            self.session.verify = not self.ssl_verify
            
            # 发送请求，允许重定向
            print(f"[信息] {task['filename']}: 发起GET请求...")
            try:
                response = self.session.get(task["url"], headers=headers, allow_redirects=True, timeout=10, stream=True)
                print(f"[信息] {task['filename']}: 请求成功，状态码: {response.status_code}")
            except requests.exceptions.SSLError as ssl_error:
                # 如果遇到SSL错误，尝试使用更宽松的配置
                print(f"[警告] {task['filename']}: SSL错误，尝试使用更宽松的SSL配置: {ssl_error}")
                # 禁用SSL验证
                self.session.verify = False
                # 再次尝试请求
                response = self.session.get(task["url"], headers=headers, allow_redirects=True, timeout=10, stream=True)
                print(f"[信息] {task['filename']}: 禁用SSL验证后请求成功，状态码: {response.status_code}")
            
            # 检查HTTP状态码
            status_code = response.status_code
            
            if status_code == 200:
                # 200 成功，开始下载
                pass
            elif status_code == 404:
                # 404 资源不存在，提示用户重新输入链接
                error_msg = "404 Not Found: 资源不存在"
                print(f"[错误] {task['filename']}: {error_msg}")
                self.root.after(0, lambda: self.show_link_error_dialog(task, error_msg))
                return
            elif status_code == 403:
                # 403 禁止访问，红字提醒并自动取消
                error_msg = "403 Forbidden: 禁止访问"
                print(f"[错误] {task['filename']}: {error_msg}")
                self.root.after(0, lambda: self.cancel_task_with_error(task, error_msg))
                return
            elif status_code >= 500:
                # 500+ 服务器错误，红字取消
                error_msg = f"服务器错误: {status_code}"
                print(f"[错误] {task['filename']}: {error_msg}")
                self.root.after(0, lambda: self.cancel_task_with_error(task, error_msg))
                return
            elif status_code >= 400:
                # 其他400+ 客户端错误，提示用户重新输入链接
                error_msg = f"请求错误: {status_code}"
                print(f"[错误] {task['filename']}: {error_msg}")
                self.root.after(0, lambda: self.show_link_error_dialog(task, error_msg))
                return
            
            # 检查是否有重定向
            if len(response.history) > 0:
                # 有重定向，更新任务的URL为最终的重定向目标
                task["url"] = response.url
                # 重新解析文件名
                from urllib.parse import urlparse
                parsed_url = urlparse(response.url)
                filename = os.path.basename(parsed_url.path)
                if filename:
                    task["filename"] = filename
                    # 更新任务树中的文件名
                    self.root.after(0, lambda: self.tasks_tree.set(str(task["id"]), "filename", filename))
            
            # 检查是否支持断点续传
            accept_ranges = response.headers.get("Accept-Ranges", "")
            supports_resume = accept_ranges == "bytes"
            
            # 获取文件大小
            total_size = 0
            if "Content-Length" in response.headers:
                try:
                    total_size = int(response.headers["Content-Length"])
                except ValueError:
                    pass
            task["total_size"] = total_size
            
            # 准备下载文件，处理文件名冲突
            file_path = os.path.join(self.download_dir, task["filename"])
            
            # 处理文件名冲突
            base, ext = os.path.splitext(task["filename"])
            counter = 1
            while os.path.exists(file_path):
                # 文件名已存在，添加(n)后缀
                new_filename = f"{base}({counter}){ext}"
                file_path = os.path.join(self.download_dir, new_filename)
                counter += 1
            
            # 更新任务的文件名
            task["filename"] = os.path.basename(file_path)
            # 更新任务树中的文件名
            self.root.after(0, lambda: self.tasks_tree.set(str(task["id"]), "filename", task["filename"]))
            
            if supports_resume and self.thread_count > 1 and total_size > 0:
                # 多线程下载
                task["threads"] = self.thread_count
                self.tasks_tree.set(str(task["id"]), "threads", str(self.thread_count))
                
                # 计算每个线程的下载范围
                chunk_size = total_size // self.thread_count
                ranges = []
                for i in range(self.thread_count):
                    start = i * chunk_size
                    end = (i + 1) * chunk_size - 1 if i < self.thread_count - 1 else total_size - 1
                    ranges.append((start, end))
                
                # 创建文件并设置大小
                with open(file_path, "wb") as f:
                    f.seek(total_size - 1)
                    f.write(b"\0")
                
                # 启动线程
                for i, (start, end) in enumerate(ranges):
                    thread = threading.Thread(
                        target=self.download_chunk,
                        args=(task, file_path, start, end, i)
                    )
                    thread.daemon = True
                    thread.start()
                    task["threads_list"].append(thread)
            else:
                # 单线程下载
                task["threads"] = 1
                self.tasks_tree.set(str(task["id"]), "threads", "1")
                
                thread = threading.Thread(
                    target=self.download_single,
                    args=(task, file_path)
                )
                thread.daemon = True
                thread.start()
                task["threads_list"].append(thread)
            
            # 更新任务状态
            task["status"] = "下载中"
            # 应用下载中标签
            self.root.after(0, lambda: self.tasks_tree.item(str(task["id"]), tags=("downloading",)))
            
            # 启动监控线程
            threading.Thread(target=self.monitor_download, args=(task,), daemon=True).start()
            
        except requests.exceptions.RequestException as e:
            # 网络错误，提示用户重新输入链接
            error_msg = str(e)
            print(f"[错误] {task['filename']}: {error_msg}")
            self.root.after(0, lambda msg=error_msg: self.show_link_error_dialog(task, msg))
    
    def show_link_error_dialog(self, task, error_msg):
        dialog = tk.Toplevel(self.root)
        dialog.title("链接错误")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 错误标题
        label = ttk.Label(dialog, text=f"{task['filename']} 文件链接失效，请重新指定")
        label.pack(pady=10, padx=10)
        
        # 具体错误信息
        error_label = ttk.Label(dialog, text=f"错误信息: {error_msg}", foreground="red")
        error_label.pack(pady=5, padx=10)
        
        # 新链接输入框
        new_url_entry = ttk.Entry(dialog, width=50)
        new_url_entry.pack(pady=10, padx=10)
        
        def on_ok():
            new_url = new_url_entry.get().strip()
            if new_url:
                task["url"] = new_url
                dialog.destroy()
                # 重新启动下载
                threading.Thread(target=self.start_download, args=(task,), daemon=True).start()
            else:
                messagebox.showerror("错误", "请输入新链接")
        
        def on_cancel():
            dialog.destroy()
            # 取消下载
            task["status"] = "已取消"
            self.tasks_tree.set(str(task["id"]), "progress", "取消")
            self.tasks_tree.item(str(task["id"]), tags=("cancelled",))
            self.tasks_tree.tag_configure("cancelled", foreground="red")
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ok_button = ttk.Button(button_frame, text="确定", command=on_ok)
        ok_button.pack(side=tk.LEFT, padx=20)
        
        cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=20)
    
    def cancel_task_with_error(self, task, error_msg):
        # 取消下载并显示红字错误信息
        task["status"] = "已取消"
        self.tasks_tree.set(str(task["id"]), "progress", error_msg)
        self.tasks_tree.item(str(task["id"]), tags=("error",))
        self.tasks_tree.tag_configure("error", foreground="red")
    
    def download_chunk(self, task, file_path, start, end, thread_id):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Range": f"bytes={start}-{end}"
            }
            
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"[信息] {task['filename']}: 创建目录: {directory}")
            
            # 发起请求
            print(f"[信息] {task['filename']}: 线程 {thread_id} 发起Range请求: bytes={start}-{end}")
            response = self.session.get(task["url"], headers=headers, stream=True)
            response.raise_for_status()
            print(f"[信息] {task['filename']}: 线程 {thread_id} 请求成功")
            
            # 计算该线程的大小
            chunk_size = end - start + 1
            downloaded = 0
            
            # 打开文件进行写入
            print(f"[信息] {task['filename']}: 线程 {thread_id} 开始写入文件: {file_path}")
            # 增大分块大小，提高下载速度
            chunk_size = 1024 * 1024  # 1MB
            # 使用缓冲区减少磁盘I/O
            buffer_size = 4 * 1024 * 1024  # 4MB缓冲区
            buffer = bytearray()
            
            with open(file_path, "rb+") as f:
                f.seek(start)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        buffer.extend(chunk)
                        downloaded_chunk = len(chunk)
                        downloaded += downloaded_chunk
                        
                        # 当缓冲区达到一定大小时写入磁盘
                        if len(buffer) >= buffer_size:
                            f.write(buffer)
                            buffer = bytearray()
                        
                        # 批量更新下载进度，减少锁的争用
                        if downloaded % (10 * 1024 * 1024) == 0:  # 每10MB更新一次
                            with task["lock"]:
                                task["downloaded_size"] += downloaded_chunk
                        else:
                            # 临时存储，最后一次性更新
                            if not hasattr(task, "temp_downloaded"):
                                task["temp_downloaded"] = 0
                            task["temp_downloaded"] += downloaded_chunk
                
                # 写入剩余的缓冲区内容
                if buffer:
                    f.write(buffer)
            
            # 下载完成后，更新临时存储的下载大小
            if hasattr(task, "temp_downloaded"):
                with task["lock"]:
                    task["downloaded_size"] += task["temp_downloaded"]
                delattr(task, "temp_downloaded")
            print(f"[信息] {task['filename']}: 线程 {thread_id} 下载完成，下载了 {downloaded} 字节")
        except Exception as e:
            print(f"[错误] 线程 {thread_id} 错误: {e}")
            # 通知主线程下载失败
            task["status"] = "失败"
            self.root.after(0, lambda: self.tasks_tree.set(str(task["id"]), "progress", f"错误: {e}"))
            self.root.after(0, lambda: self.tasks_tree.item(str(task["id"]), tags=("error",)))
    
    def download_single(self, task, file_path):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"[信息] {task['filename']}: 创建目录: {directory}")
            
            # 发起请求
            print(f"[信息] {task['filename']}: 发起GET请求...")
            response = self.session.get(task["url"], headers=headers, stream=True)
            response.raise_for_status()
            print(f"[信息] {task['filename']}: 请求成功")
            
            # 写入文件
            print(f"[信息] {task['filename']}: 开始写入文件: {file_path}")
            # 增大分块大小，提高下载速度
            chunk_size = 1024 * 1024  # 1MB
            # 使用缓冲区减少磁盘I/O
            buffer_size = 4 * 1024 * 1024  # 4MB缓冲区
            buffer = bytearray()
            
            # 累积下载大小
            total_downloaded = 0
            
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        buffer.extend(chunk)
                        downloaded_chunk = len(chunk)
                        total_downloaded += downloaded_chunk
                        
                        # 当缓冲区达到一定大小时写入磁盘
                        if len(buffer) >= buffer_size:
                            f.write(buffer)
                            buffer = bytearray()
                        
                        # 批量更新下载进度，减少锁的争用
                        if total_downloaded % (10 * 1024 * 1024) == 0:  # 每10MB更新一次
                            with task["lock"]:
                                task["downloaded_size"] += downloaded_chunk
                        else:
                            # 临时存储，最后一次性更新
                            if not hasattr(task, "temp_downloaded"):
                                task["temp_downloaded"] = 0
                            task["temp_downloaded"] += downloaded_chunk
                
                # 写入剩余的缓冲区内容
                if buffer:
                    f.write(buffer)
            
            # 下载完成后，更新临时存储的下载大小
            if hasattr(task, "temp_downloaded"):
                with task["lock"]:
                    task["downloaded_size"] += task["temp_downloaded"]
                delattr(task, "temp_downloaded")
            print(f"[信息] {task['filename']}: 下载完成，下载了 {task['downloaded_size']} 字节")
        except Exception as e:
            print(f"[错误] 下载错误: {e}")
            # 通知主线程下载失败
            task["status"] = "失败"
            self.root.after(0, lambda: self.tasks_tree.set(str(task["id"]), "progress", f"错误: {e}"))
            self.root.after(0, lambda: self.tasks_tree.item(str(task["id"]), tags=("error",)))
    
    def monitor_download(self, task):
        last_downloaded = 0
        last_time = time.time()
        
        # 记录已结束的线程
        completed_threads = []
        
        while task["status"] == "下载中":
            time.sleep(1)
            
            # 计算下载速度
            current_downloaded = task["downloaded_size"]
            current_time = time.time()
            elapsed = current_time - last_time
            
            if elapsed > 0:
                speed = (current_downloaded - last_downloaded) / elapsed
                task["speed"] = self.format_speed(speed)
                
                # 更新UI
                self.root.after(0, lambda: self.update_task_ui(task))
                
                # 检查是否需要自动添加线程
                if self.auto_thread_threshold > 0 and task["total_size"] > 0:
                    # 检查已结束的线程
                    for i, thread in enumerate(task["threads_list"]):
                        if not thread.is_alive() and i not in completed_threads:
                            completed_threads.append(i)
                            print(f"[信息] {task['filename']}: 线程 {i} 已完成")
                    
                    # 检查是否有剩余部分大于阈值
                    remaining_size = task["total_size"] - task["downloaded_size"]
                    if remaining_size > self.auto_thread_threshold * 1024 * 1024 and len(completed_threads) > 0:
                        # 有剩余部分大于阈值且有已结束的线程
                        print(f"[信息] {task['filename']}: 剩余部分 {remaining_size} 字节大于阈值 {self.auto_thread_threshold} MB，尝试分配已结束的线程")
                        
                        # 对剩余部分进行平分
                        # 第一部分由原线程继续下载
                        # 第二部分由已结束的线程继续下载
                        
                        # 获取一个已结束的线程索引
                        completed_thread_idx = completed_threads.pop(0)
                        print(f"[信息] {task['filename']}: 分配已结束的线程 {completed_thread_idx} 继续下载")
                        
                        # 计算平分点
                        split_point = task["downloaded_size"] + (remaining_size // 2)
                        
                        # 创建新的下载任务给已结束的线程
                        # 这里简化处理，直接启动一个新线程下载剩余部分
                        file_path = os.path.join(self.download_dir, task["filename"])
                        new_thread = threading.Thread(
                            target=self.download_chunk,
                            args=(task, file_path, split_point, task["total_size"] - 1, completed_thread_idx)
                        )
                        new_thread.daemon = True
                        new_thread.start()
                        
                        # 更新线程列表
                        task["threads_list"][completed_thread_idx] = new_thread
                        print(f"[信息] {task['filename']}: 已启动线程 {completed_thread_idx} 下载剩余部分")
                
                last_downloaded = current_downloaded
                last_time = current_time
            
            # 检查下载是否完成
            if task["total_size"] > 0 and task["downloaded_size"] >= task["total_size"]:
                task["status"] = "已完成"
                task["progress"] = 100
                # 应用已完成标签
                self.root.after(0, lambda: self.tasks_tree.item(str(task["id"]), tags=("completed",)))
                self.root.after(0, lambda: self.update_task_ui(task))
                break
    
    def update_task_ui(self, task):
        # 计算进度
        if task["total_size"] > 0:
            progress = int((task["downloaded_size"] / task["total_size"]) * 100)
            task["progress"] = progress
            # 创建文本进度条
            bar_length = 20
            filled_length = int(bar_length * progress / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            progress_text = f"{bar} {progress}%"
        else:
            progress_text = "下载中"
        
        # 更新任务树
        self.tasks_tree.set(str(task["id"]), "speed", task["speed"])
        self.tasks_tree.set(str(task["id"]), "progress", progress_text)
    
    def format_speed(self, speed):
        units = ["B", "KB", "MB", "GB"]
        unit_index = 0
        
        while speed >= 1024 and unit_index < len(units) - 1:
            speed /= 1024
            unit_index += 1
        
        return f"{speed:.2f} {units[unit_index]}/s"
    
    def update_task_stats(self):
        # 更新任务统计信息
        task_count = len(self.tasks)
        if hasattr(self, 'task_stats_label'):
            self.task_stats_label.config(text=f"任务数: {task_count}")
        
        # 更新任务列表统计信息
        if hasattr(self, 'tasks_count_label'):
            # 计算不同状态的任务数
            downloading_count = sum(1 for task in self.tasks if task.get('status') == '下载中')
            completed_count = sum(1 for task in self.tasks if task.get('status') == '已完成')
            self.tasks_count_label.config(text=f"{task_count} 任务 ({downloading_count} 下载中, {completed_count} 已完成)")

if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
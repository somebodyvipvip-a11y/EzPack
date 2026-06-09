import os
import shutil
import subprocess
import sys
import time

# 优雅捕获 PIL 导入，防止宿主环境未安装导致程序直接崩溃
try:
    from PIL import Image
except ImportError:
    Image = None

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPalette, QColor, QTextCursor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTextEdit, QVBoxLayout, QWidget
)

# ==========================================
# 🎨 macOS 经典现代化暗黑主题色调
# ==========================================
BG_MAIN = "#1E1E1E"
BG_PANEL = "#252526"
BG_INPUT = "#111111"
FG_TEXT = "#E3E3E3"
FG_MUTED = "#8E8E93"
COLOR_ACCENT = "#0A84FF"
COLOR_BORDER = "#3A3A3C"
FG_LOG = "#34D399"

# 🎯【核心黑科技】Windows 静默执行标记，彻底干掉子进程弹出的 CMD 黑框
IS_WIN = sys.platform == "win32"
HIDE_SUBPROCESS_FLAG = subprocess.CREATE_NO_WINDOW if IS_WIN else 0


# ==========================================
# 🛠️ 核心工具函数
# ==========================================
def get_resource_path(relative_path):
    """
    获取静态资源的绝对路径（用于单文件内置 Logo 图标）。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.normpath(os.path.join(sys._MEIPASS, relative_path))
    
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(app_dir, relative_path))


def get_tool_bin(python_executable, tool_name):
    """
    根据给定的 python 解释器路径，强力锁定对应的 pip 或 pyinstaller 可执行文件的绝对物理路径。
    """
    py_dir = os.path.dirname(python_executable)
    
    # 1. 尝试在同级目录下寻找 (虚拟环境 venv 常用布局)
    exe_same = os.path.normpath(os.path.join(py_dir, f"{tool_name}.exe"))
    if os.path.exists(exe_same):
        return exe_same
        
    # 2. 尝试在 Scripts 子目录下寻找 (标准全局 Python 常用布局)
    exe_scripts = os.path.normpath(os.path.join(py_dir, "Scripts", f"{tool_name}.exe"))
    if os.path.exists(exe_scripts):
        return exe_scripts
        
    # 3. 兜底方案：直接从系统环境变量中检索
    exe_env = shutil.which(tool_name)
    if exe_env:
        return os.path.normpath(exe_env)
        
    return exe_scripts


# ==========================================
# 🧵 异步打包工作线程（无黑框纯静默版）
# ==========================================
class PackWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, py_path, img_path, data_path, hide_console, auto_req, use_upx, use_venv, exclude_webengine):
        super().__init__()
        self.py_path = py_path
        self.img_path = img_path
        self.data_path = data_path
        self.hide_console = hide_console
        self.auto_req = auto_req
        self.use_upx = use_upx
        self.use_venv = use_venv
        self.exclude_webengine = exclude_webengine

    def run(self):
        start_time = time.time()
        current_dir = os.path.dirname(os.path.abspath(self.py_path))
        base_name = os.path.splitext(os.path.basename(self.py_path))[0]
        venv_dir = os.path.join(current_dir, "ezpack_venv")
        
        try:
            self.log_signal.emit("==================== 开始执行打包任务 ====================")
            
            # 1. 动态锁定当前底层的基础 Python 解释器
            if getattr(sys, 'frozen', False):
                python_bin = shutil.which("python")
                if not python_bin:
                    self.log_signal.emit("\n❌ 错误：未在系统环境变量 (PATH) 中检测到 'python' 命令！")
                    self.finished_signal.emit(False, "未找到系统 Python 解释器。")
                    return
            else:
                python_bin = sys.executable

            self.log_signal.emit(f"[1/5] 已成功锁定环境解释器: {python_bin}")

            # 2. 虚拟环境沙盒机制调度
            if self.use_venv:
                self.log_signal.emit("-> 检测到开启了沙盒模式，正在创建独立的隔离虚拟环境 (Venv)...")
                if os.path.exists(venv_dir):
                    try: shutil.rmtree(venv_dir)
                    except Exception: pass
                
                # 💥 注入 HIDE_SUBPROCESS_FLAG 隐藏黑框
                subprocess.run(
                    [python_bin, "-m", "venv", "ezpack_venv"], 
                    check=True, cwd=current_dir, creationflags=HIDE_SUBPROCESS_FLAG
                )
                python_bin = os.path.join(venv_dir, "Scripts", "python.exe")
                self.log_signal.emit(f"-> 虚拟环境构建成功。沙盒路径: {venv_dir}")

            # 3. 强力锁定当前环境下的 pip 和 pyinstaller 物理绝对路径
            pip_bin = get_tool_bin(python_bin, "pip")
            pyinstaller_bin = get_tool_bin(python_bin, "pyinstaller")

            upx_bin = shutil.which("upx")
            if not upx_bin:
                py_dir = os.path.dirname(python_bin)
                test_upx = os.path.join(py_dir, "Scripts", "upx.exe")
                if os.path.exists(test_upx):
                    upx_bin = test_upx

            # 4. 依赖项分析与安装
            if self.auto_req:
                req_path = os.path.join(current_dir, "requirements.txt")
                if os.path.exists(req_path):
                    self.log_signal.emit("[2/5] 检测到 requirements.txt，正在配置依赖项目...")
                    # 💥 注入 HIDE_SUBPROCESS_FLAG 隐藏黑框
                    sub = subprocess.run(
                        [pip_bin, "install", "-r", "requirements.txt"], 
                        capture_output=True, text=True, cwd=current_dir, creationflags=HIDE_SUBPROCESS_FLAG
                    )
                    if sub.returncode != 0:
                        self.log_signal.emit(f"-> 提示：部分依赖项在安装时产生非致命异常: {sub.stderr.strip()}")
                    else:
                        self.log_signal.emit("-> 依赖项目安装及完整性验证通过。")
                    
                    if self.use_venv:
                        subprocess.run(
                            [pip_bin, "install", "pillow"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=current_dir, creationflags=HIDE_SUBPROCESS_FLAG
                        )
                else:
                    self.log_signal.emit("[2/5] 未检测到 requirements.txt 文件。")
                    if self.use_venv:
                        self.log_signal.emit("-> 提示：隔离环境下未检测到依赖描述，正在为您预装 PySide6 核心组件与 Pillow...")
                        subprocess.run(
                            [pip_bin, "install", "PySide6", "pillow"], 
                            check=True, cwd=current_dir, creationflags=HIDE_SUBPROCESS_FLAG
                        )
            else:
                self.log_signal.emit("[2/5] 用户已指定跳过依赖项配置阶段。")
                if self.use_venv:
                    self.log_signal.emit("-> 正在隔离环境中配置 PySide6 核心组件与 Pillow...")
                    subprocess.run(
                        [pip_bin, "install", "PySide6", "pillow"], 
                        check=True, cwd=current_dir, creationflags=HIDE_SUBPROCESS_FLAG
                    )

            # 5. 应用程序图标预处理 (仅用于修改 EXE 本身的系统图标)
            final_ico_path = None
            is_temp_ico = False

            if self.img_path:
                if self.img_path.lower().endswith(".ico"):
                    self.log_signal.emit("[3/5] 检测到原生 ICO 格式图标，已启用路径直通模式。")
                    final_ico_path = self.img_path
                else:
                    if Image is None:
                        self.log_signal.emit("[3/5] ⚠️ 宿主环境未安装 Pillow，无法自动转换 PNG/JPG。本次将忽略自定义图标。")
                    else:
                        self.log_signal.emit("[3/5] 检测到通用图像格式，正在将其转换为标准多尺寸 ICO 图标文件...")
                        try:
                            img = Image.open(self.img_path)
                            img_rgba = img.convert("RGBA")
                            temp_ico = os.path.join(current_dir, "temp_program_icon.ico")
                            sizes = [(256,256), (128,128), (64,64), (48,48), (32,32), (24,24), (16,16)]
                            img_rgba.save(temp_ico, format="ICO", sizes=sizes)
                            final_ico_path = temp_ico
                            is_temp_ico = True
                            self.log_signal.emit("-> 图标文件色彩空间标准化 (RGBA) 并转换成功。")
                        except Exception as img_err:
                            self.log_signal.emit(f"-> 错误：图标文件转换失败: {str(img_err)}")
                            final_ico_path = None
            else:
                self.log_signal.emit("[3/5] 未指定应用程序图标，将使用 PyInstaller 默认图标。")

            # 6. 核心打包工具完整性物理校验
            if not os.path.exists(pyinstaller_bin):
                self.log_signal.emit("ℹ️ 当前环境未检索到 PyInstaller 核心可执行程序，正在为您自动下载安装...")
                subprocess.run(
                    [pip_bin, "install", "pyinstaller"], 
                    check=True, cwd=current_dir, creationflags=HIDE_SUBPROCESS_FLAG
                )
                pyinstaller_bin = get_tool_bin(python_bin, "pyinstaller")

            # 7. 配置 PyInstaller 编译参数
            self.log_signal.emit("[4/5] 正在配置 PyInstaller 编译参数...")
            
            cmd = [pyinstaller_bin, "--onefile", "--noconfirm", "--clean"]

            # ✨ 新增：注入附加数据资源 (--add-data) 核心黑科技
            if self.data_path and os.path.exists(self.data_path):
                path_sep = ";" if IS_WIN else ":"
                if os.path.isdir(self.data_path):
                    # 如果是文件夹，保持原有文件夹名称结构压入
                    folder_name = os.path.basename(self.data_path.rstrip(r"\/"))
                    cmd.extend(["--add-data", f"{self.data_path}{path_sep}{folder_name}"])
                    self.log_signal.emit(f"-> [资源封装] 已挂载文件夹：{folder_name}")
                else:
                    # 如果是单文件，直接释放到运行时的根目录级
                    cmd.extend(["--add-data", f"{self.data_path}{path_sep}."])
                    self.log_signal.emit(f"-> [资源封装] 已挂载单资源文件：{os.path.basename(self.data_path)}")

            if self.exclude_webengine:
                cmd.extend(["--exclude-module", "PySide6.QtWebEngineCore"])
                cmd.extend(["--exclude-module", "PySide6.QtWebEngineWidgets"])
                self.log_signal.emit("-> 已为您屏蔽巨型 QtWebEngine 网页内核，预计缩减体积 ~100MB+。")

            if self.use_upx and upx_bin:
                cmd.extend(["--upx-dir", os.path.dirname(upx_bin)])
                self.log_signal.emit(f"-> 检测到可用 UPX 压缩器，已启用壳压缩策略。")
            else:
                cmd.append("--noupx")

            if self.hide_console:
                cmd.append("--noconsole")

            if final_ico_path:
                cmd.append(f"--icon={final_ico_path}")

            cmd.append(self.py_path)

            # 拉起打包进程 💥 注入 HIDE_SUBPROCESS_FLAG 隐藏核心编译黑框
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, stdin=subprocess.DEVNULL, bufsize=1, cwd=current_dir,
                creationflags=HIDE_SUBPROCESS_FLAG
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log_signal.emit(line.strip())

            if process.returncode == 0:
                self.log_signal.emit("[5/5] 编译流程执行完毕。正在清理构建过程中产生的临时缓存文件...")
                time.sleep(1.2)

                elapsed_time = time.time() - start_time
                duration_str = f"{int(elapsed_time // 60)} 分 {int(elapsed_time % 60)} 秒" if elapsed_time >= 60 else f"{elapsed_time:.1f} 秒"
                
                exe_path = os.path.join(current_dir, "dist", f"{base_name}.exe")
                exe_size_str = "未知"
                if os.path.exists(exe_path):
                    size_bytes = os.path.getsize(exe_path)
                    exe_size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

                build_root_dir = os.path.join(current_dir, "build")
                if os.path.exists(build_root_dir):
                    try: shutil.rmtree(build_root_dir)
                    except Exception: pass

                if os.path.exists(venv_dir):
                    try: shutil.rmtree(venv_dir)
                    except Exception: pass

                spec_file = os.path.join(current_dir, f"{base_name}.spec")
                if os.path.exists(spec_file):
                    os.remove(spec_file)

                if is_temp_ico and final_ico_path and os.path.exists(final_ico_path):
                    os.remove(final_ico_path)

                self.log_signal.emit(f"\n==================== 📊 编译数据分析统计 ====================")
                self.log_signal.emit(f"⏱️ 编译打包总耗时:  {duration_str}")
                self.log_signal.emit(f"💾 最终软件体积大小: {exe_size_str}")
                self.log_signal.emit(f"============================================================")

                os.startfile(os.path.join(current_dir, "dist"))
                popup_msg = f"打包任务已顺利完成！\n\n⏱️ 编译总耗时：{duration_str}\n💾 软件体积：{exe_size_str}"
                self.finished_signal.emit(True, popup_msg)
            else:
                if os.path.exists(venv_dir):
                    try: shutil.rmtree(venv_dir) 
                    except Exception: pass
                self.log_signal.emit("\n❌ 错误：PyInstaller 编译过程异常终止，请检查上方的系统日志。")
                self.finished_signal.emit(False, "打包失败，请检查控制台输出。")

        except Exception as e:
            if os.path.exists(venv_dir):
                try: shutil.rmtree(venv_dir)
                except Exception: pass
            self.log_signal.emit(f"\n❌ 系统异常: {str(e)}")
            self.finished_signal.emit(False, f"程序运行时产生未捕获的异常: {str(e)}")


# ==========================================
# 🖼️ 主应用窗口
# ==========================================
class EzPackApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("EzPack - Python 应用程序打包配置实用工具")
        self.resize(1000, 760)
        self.setMinimumSize(750, 680)
        self.setAcceptDrops(True)

        self.app_icon = QIcon()
        possible_logos = ["logo.png", "logo.jpg", "logo.jpeg", "logo.bmp", "logo.ico"]
        for logo_name in possible_logos:
            resolved_path = get_resource_path(logo_name)
            if os.path.exists(resolved_path):
                self.app_icon = QIcon(QPixmap(resolved_path))
                self.setWindowIcon(self.app_icon)
                break

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_MAIN};
                color: {FG_TEXT};
                font-family: 'Microsoft YaHei', 'Segoe UI';
                font-size: 13px;
            }}
            QFrame#MainPanel {{
                background-color: {BG_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QLineEdit {{
                background-color: {BG_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 7px;
                color: {FG_TEXT};
                font-family: 'Consolas', 'Microsoft YaHei';
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_ACCENT};
            }}
            QPushButton#BrowseBtn {{
                background-color: {COLOR_BORDER};
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
                color: {FG_TEXT};
                font-weight: bold;
                min-height: 20px;
            }}
            QPushButton#BrowseBtn:hover {{
                background-color: #48484A;
            }}
            QPushButton#ActionBtn {{
                background-color: {COLOR_ACCENT};
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#ActionBtn:hover {{
                background-color: #0071E3;
            }}
            QPushButton#ActionBtn:disabled {{
                background-color: {COLOR_BORDER};
                color: {FG_MUTED};
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                background-color: {BG_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLOR_ACCENT};
                border: 1px solid {COLOR_ACCENT};
            }}
            QTextEdit {{
                background-color: {BG_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                color: {FG_LOG};
                font-family: 'Consolas', 'Courier New';
                font-size: 12px;
                padding: 8px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("EzPack 编译向导")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        main_layout.addWidget(title_label)

        panel_frame = QFrame()
        panel_frame.setObjectName("MainPanel")
        
        grid_layout = QGridLayout(panel_frame)
        grid_layout.setContentsMargins(20, 18, 20, 18)
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(15)

        # 1. 源脚本
        py_title = QLabel("源脚本路径 (*.py)")
        py_title.setStyleSheet("font-weight: bold; color: white;")
        self.py_path_edit = QLineEdit()
        self.py_path_edit.setPlaceholderText("将脚本文件直接拖入此窗口任意位置...")
        self.py_path_edit.setAcceptDrops(False)
        
        btn_browse_py = QPushButton("选择文件...")
        btn_browse_py.setObjectName("BrowseBtn")
        btn_browse_py.setCursor(Qt.PointingHandCursor)
        btn_browse_py.clicked.connect(self.browse_py)

        grid_layout.addWidget(py_title, 0, 0, 1, 2)
        grid_layout.addWidget(self.py_path_edit, 1, 0)
        grid_layout.addWidget(btn_browse_py, 1, 1)

        # 2. EXE 主图标
        img_title = QLabel("EXE 外壳图标 (支持原生 ICO 直通，或自动转换 PNG/JPG/BMP，可选)")
        img_title.setStyleSheet("font-weight: bold; color: white;")
        self.img_path_edit = QLineEdit()
        self.img_path_edit.setPlaceholderText("仅用于给生成的 .exe 外壳换图标...")
        self.img_path_edit.setAcceptDrops(False)
        
        btn_browse_img = QPushButton("选择文件...")
        btn_browse_img.setObjectName("BrowseBtn")
        btn_browse_img.setCursor(Qt.PointingHandCursor)
        btn_browse_img.clicked.connect(self.browse_img)

        grid_layout.addWidget(img_title, 2, 0, 1, 2)
        grid_layout.addWidget(self.img_path_edit, 3, 0)
        grid_layout.addWidget(btn_browse_img, 3, 1)

        # ✨ 3. 新增：附加资源数据挂载路径框 (--add-data)
        data_title = QLabel("代码内部引用的附加资源/图标 (支持单文件或整个文件夹，可选)")
        data_title.setStyleSheet("font-weight: bold; color: white;")
        self.data_path_edit = QLineEdit()
        self.data_path_edit.setPlaceholderText("支持拖入内含 ico/图片/配置的文件夹，或点击右侧选择单文件...")
        self.data_path_edit.setAcceptDrops(False)

        btn_browse_data = QPushButton("选择文件...")
        btn_browse_data.setObjectName("BrowseBtn")
        btn_browse_data.setCursor(Qt.PointingHandCursor)
        btn_browse_data.clicked.connect(self.browse_data)

        grid_layout.addWidget(data_title, 4, 0, 1, 2)
        grid_layout.addWidget(self.data_path_edit, 5, 0)
        grid_layout.addWidget(btn_browse_data, 5, 1)

        grid_layout.setColumnStretch(0, 1)
        main_layout.addWidget(panel_frame)

        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(5, 2, 5, 2)
        
        self.cb_hide_console = QCheckBox("不显示控制台窗口 (--noconsole)")
        self.cb_hide_console.setChecked(True)
        
        self.cb_auto_req = QCheckBox("自动安装依赖")
        self.cb_auto_req.setChecked(True)

        self.cb_use_upx = QCheckBox("启用 UPX 壳压缩")
        self.cb_use_upx.setChecked(True)

        self.cb_use_venv = QCheckBox("启用独立虚拟环境 (Venv)")
        self.cb_use_venv.setChecked(False)

        self.cb_exclude_webengine = QCheckBox("剔除特大 WebEngine 内核")
        self.cb_exclude_webengine.setChecked(True)

        options_layout.addWidget(self.cb_hide_console)
        options_layout.addSpacing(15)
        options_layout.addWidget(self.cb_auto_req)
        options_layout.addSpacing(15)
        options_layout.addWidget(self.cb_use_upx)
        options_layout.addSpacing(15)
        options_layout.addWidget(self.cb_use_venv)
        options_layout.addSpacing(15)
        options_layout.addWidget(self.cb_exclude_webengine)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)

        self.start_btn = QPushButton("开始编译")
        self.start_btn.setObjectName("ActionBtn")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(46)
        self.start_btn.clicked.connect(self.start_pack_process)
        main_layout.addWidget(self.start_btn)

        log_title = QLabel("构建系统输出日志")
        log_title.setStyleSheet(f"color: {FG_MUTED}; font-weight: bold;")
        main_layout.addWidget(log_title)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        main_layout.addWidget(self.log_text_edit)

    def browse_py(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 Python 脚本", "", "Python 脚本文件 (*.py)")
        if file_path:
            self.py_path_edit.setText(os.path.normpath(file_path))

    def browse_img(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标/图像资源", "", 
            "支持的资源类型 (*.ico *.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )
        if file_path:
            self.img_path_edit.setText(os.path.normpath(file_path))

    def browse_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要封装进内层的资源文件", "", "所有资源文件 (*.*)"
        )
        if file_path:
            self.data_path_edit.setText(os.path.normpath(file_path))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        has_py = False
        has_img = False
        has_data = False
        unsupported_files = []

        for url in urls:
            file_path = url.toLocalFile()
            clean_path = os.path.normpath(file_path.strip(' "\''))

            # 🛠️ 智能化拖拽分流逻辑
            if os.path.isdir(clean_path):
                # 只要是文件夹，一律作为附加资源处理
                self.data_path_edit.setText(clean_path)
                has_data = True
                continue

            ext = clean_path.lower()
            if ext.endswith(".py"):
                self.py_path_edit.setText(clean_path)
                has_py = True
            elif ext.endswith((".ico", ".png", ".jpg", ".jpeg", ".bmp")):
                # 如果发现外壳图标还空着，优先填入外壳图标，否则填入附加数据资源
                if not self.img_path_edit.text().strip():
                    self.img_path_edit.setText(clean_path)
                    has_img = True
                else:
                    self.data_path_edit.setText(clean_path)
                    has_data = True
            else:
                # 其他所有乱七八糟的文件，归为资源附加数据
                self.data_path_edit.setText(clean_path)
                has_data = True

        if has_py:
            self.append_log_line("-> 识别至 Python 源脚本，路径已自动同步。")
        if has_img:
            self.append_log_line("-> 识别至外壳图像资源，路径已自动同步。")
        if has_data:
            self.append_log_line("⚡ [智能分流] 识别到附加资源数据包/文件夹，已绑定至 Add-Data 轨道！")

    def start_pack_process(self):
        py_path = self.py_path_edit.text().strip(' "\'')
        img_path = self.img_path_edit.text().strip(' "\'')
        data_path = self.data_path_edit.text().strip(' "\'')

        if not py_path or not os.path.exists(py_path):
            QMessageBox.critical(self, "配置错误", "目标 Python 源脚本路径无效，请核对后重试。")
            return

        self.start_btn.setEnabled(False)
        self.start_btn.setText("正在执行自动化编译流程...")
        self.log_text_edit.clear()

        self.worker = PackWorker(
            py_path, img_path, data_path,
            self.cb_hide_console.isChecked(), 
            self.cb_auto_req.isChecked(),
            self.cb_use_upx.isChecked(),
            self.cb_use_venv.isChecked(),
            self.cb_exclude_webengine.isChecked()
        )
        self.worker.log_signal.connect(self.append_log_line)
        self.worker.finished_signal.connect(self.pack_finished_callback)
        self.worker.start()

    def append_log_line(self, text):
        self.log_text_edit.append(text)
        self.log_text_edit.moveCursor(QTextCursor.End)

    def pack_finished_callback(self, success, message):
        if success:
            QMessageBox.information(self, "操作成功", message)
        else:
            QMessageBox.critical(self, "编译失败", message)
        self.start_btn.setEnabled(True)
        self.start_btn.setText("开始编译")


if __name__ == "__main__":
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mycompany.ezpack.v1.0")
    except Exception:
        pass

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BG_MAIN))
    palette.setColor(QPalette.WindowText, QColor(FG_TEXT))
    palette.setColor(QPalette.Base, QColor(BG_INPUT))
    palette.setColor(QPalette.AlternateBase, QColor(BG_PANEL))
    palette.setColor(QPalette.ToolTipBase, QColor(FG_TEXT))
    palette.setColor(QPalette.ToolTipText, QColor(FG_TEXT))
    palette.setColor(QPalette.Text, QColor(FG_TEXT))
    palette.setColor(QPalette.Button, QColor(BG_PANEL))
    palette.setColor(QPalette.ButtonText, QColor(FG_TEXT))
    app.setPalette(palette)

    ex = EzPackApp()
    ex.show()
    sys.exit(app.exec())
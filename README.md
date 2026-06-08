# EzPack 🚀

[![Python Version](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.0+-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com)

**EzPack** 是一款专为 Python 开发者打造的**现代化、一键式可视化打包配置工具**。基于 PySide6 (Qt for Python) 构建，采用优雅的 macOS 风格暗黑主题界面，旨在解决 `PyInstaller` 繁琐的命令行参数记忆痛点，并彻底解决 Windows 环境下打包及运行时令人烦恼的“CMD黑框”问题。---由Gemini构建开发

无论你是想快速发布一个脚本，还是交付一个大型的 GUI 商业软件，EzPack 都能让你的打包流程变得优雅而简单。

---

## ✨ 核心特性

- 🤫 **全静默编译（无黑框特技）**：通过底层注入 Windows 特有的 `CREATE_NO_WINDOW` 标记，**彻底压制**编译过程中频繁闪烁的 CMD 黑色弹窗，让打包过程宛如后台原生服务般丝滑。
- 📦 **沙盒隔离机制 (Venv)**：支持一键开启独立的干净虚拟环境（Virtual Environment），拒绝本地全局臃肿环境带来的干扰，有效**缩减 50% 以上**的最终 `.exe` 体积。
- 🖼️ **智能图标中转站**：完美支持原生 `.ico` 格式直通；同时内置高保真图像处理，可将 `PNG` / `JPG` / `BMP` 等普通图片**自动转换为标准多尺寸多色彩空间的集成 ICO 图标**。
- 🖲️ **拖拽式智能分流**：支持将 `.py` 脚本和图片资源直接拖入窗口任意位置，算法会自动识别文件后缀并精准填装到对应路径框中。
- ⚡ **巨型库智能剔除**：针对 PySide/PyQt 开发者，内置一键剥离 `QtWebEngine`（网页内核）的优化策略，可直接为最终生成文件**瘦身 100MB+**。
- 📊 **可视化日志与统计**：实时捕获编译流，高亮展示关键节点，并在打包结束后自动统计**编译总耗时**与**最终软件体积**，自动打开输出目录。

---

## 🛠️ 技术栈

* **GUI 框架**：PySide6 (Qt6)
* **核心引擎**：PyInstaller
* **图像处理**：Pillow (PIL)
* **底层通信**：异步 QThread 任务线程 + Subprocess 管道捕获

---

##使用指南
**拖入文件：将你的主 Python 脚本（例如 main.py）拖入软件窗口，再将作为图标的图片拖入窗口。

#勾选配置：

*💡 强烈建议勾选 启用独立虚拟环境 (Venv) 以保证打包出的 exe 体积最小。但打包时长会变长。

*如果你的程序是带界面的（如 PyQt/PySide/Tkinter），勾选 不显示控制台窗口 (--noconsole)，这样最终的用户双击 exe 时就不会弹出黑框。

*点击编译：静静等待绿色日志滚动完毕，程序会自动弹窗提示成功并为你打开 dist 文件夹。

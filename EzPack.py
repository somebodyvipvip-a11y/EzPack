import os
import shutil
import subprocess
import sys


def create_ico(png_path, target_dir):
    """读取 PNG 并生成多尺寸的标准 ICO 文件"""
    try:
        from PIL import Image
    except ImportError:
        print("正在安装必要的图像处理库 Pillow...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pillow"]
        )
        from PIL import Image

    print("开始制作多尺寸 ICO 图标...")
    img = Image.open(png_path)
    ico_path = os.path.join(target_dir, "program_icon.ico")

    # 包含 Windows 资源管理器所需的所有黄金尺寸
    sizes = [(256, 256), (128, 128), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"✅ 图标生成成功：{ico_path}")
    return ico_path


def check_pyinstaller():
    """检查并自动安装 PyInstaller"""
    try:
        import PyInstaller
    except ImportError:
        print("正在安装打包工具 PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"]
        )


def run_pyinstaller(py_path, ico_path):
    """调用 PyInstaller 进行一键打包"""
    print("开始打包程序，请稍候...")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        f"--icon={ico_path}",
        py_path,
    ]

    try:
        # 执行打包命令
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 打包失败，错误信息如下：")
        print(e.stderr)
        return False


def clean_garbage(py_path, ico_path):
    """清理打包生成的 build 文件夹、.spec 文件以及临时的 .ico 文件"""
    print("🧹 正在清理打包留下的缓存垃圾文件...")

    # 获取脚本名（不带后缀）
    base_name = os.path.splitext(os.path.basename(py_path))[0]

    # 1. 删除 build 文件夹
    build_dir = os.path.join(os.getcwd(), "build")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print("-> 已删除 build 文件夹")

    # 2. 删除 .spec 文件
    spec_file = os.path.join(os.getcwd(), f"{base_name}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"-> 已删除 {base_name}.spec 配置文件")

    # 3. 删除刚才临时生成的 ico 图标（如果你想保留图标可以把下面两行删掉）
    if os.path.exists(ico_path):
        os.remove(ico_path)
        print("-> 已删除临时的 ico 图标文件")


if __name__ == "__main__":
    print("====== Python 一键自动打包与垃圾清理工具 ======\n")

    # 1. 获取用户输入的路径
    png_input = input("1. 请输入/拖入你的 PNG 图片路径: ").strip('" ')
    py_input = input("2. 请输入/拖入你要打包的 .py 脚本路径: ").strip('" ')

    # 验证路径正确性
    if not os.path.exists(png_input):
        print(f"❌ 找不到图片文件: {png_input}")
        sys.exit(1)
    if not os.path.exists(py_input):
        print(f"❌ 找不到 Python 脚本: {py_input}")
        sys.exit(1)

    # 获取当前工作目录
    current_dir = os.path.dirname(os.path.abspath(py_input))
    os.chdir(current_dir)  # 切换到脚本 woods 目录

    # 2. 检查并准备环境
    check_pyinstaller()

    # 3. 生成多尺寸 ICO
    generated_ico = create_ico(png_input, current_dir)

    # 4. 执行自动打包
    success = run_pyinstaller(py_input, generated_ico)

    # 5. 打包成功后进行垃圾清理
    if success:
        clean_garbage(py_input, generated_ico)
        print("==========================================")
        print("🎉 一键打包全部完成，且垃圾已清空！")
        print(f"您的干净纯洁的 .exe 文件在：{os.path.join(os.getcwd(), 'dist')}")
        print("==========================================")

    input("\n按回车键退出...")
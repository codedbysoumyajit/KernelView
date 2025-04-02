import os
import platform
import psutil
import socket
import subprocess
import time
import datetime

# Modern color scheme with better contrast
COLOR_HEADER = "\033[38;5;196m"  # Bright red
COLOR_CATEGORY = "\033[38;5;208m"  # Orange
COLOR_KEY = "\033[38;5;255m"  # Bright white
COLOR_VALUE = "\033[38;5;249m"  # Light gray
COLOR_ACCENT = "\033[38;5;33m"  # Blue
COLOR_RESET = "\033[0m"

# Compact ASCII art header
HEADER_ART = rf"""
{COLOR_HEADER}   
  _  __                 ___   ___            
 | |/ /___ _ _ _ _  ___| \ \ / (_)_____ __ __
 | ' </ -_) '_| ' \/ -_) |\ V /| / -_) V  V /
 |_|\_\___|_| |_||_\___|_| \_/ |_\___|\_/\_/ 
                                             

{COLOR_RESET}{COLOR_ACCENT}  System Information Toolkit{COLOR_RESET}
"""

def get_kernel_info():
    try:
        if platform.system() == "Linux":
            kernel_name = subprocess.check_output("uname -s", shell=True).decode().strip()
            kernel_version = subprocess.check_output("uname -r", shell=True).decode().strip()
            return f"{kernel_name} {kernel_version}"
        elif platform.system() == "Windows":
            return platform.win32_ver()[0]
        elif platform.system() == "Darwin":
            kernel_name = "Darwin"
            kernel_version = subprocess.check_output("uname -r", shell=True).decode().strip()
            return f"{kernel_name} {kernel_version}"
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

def get_cpu_info():
    try:
        if platform.system() == "Windows":
            return platform.processor()
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(": ")[-1].strip()
        elif platform.system() == "Darwin":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).strip().decode()
    except Exception:
        return "Unknown"
    return "Unknown"

def get_gpu_info():
    try:
        if platform.system() == "Windows":
            return subprocess.check_output("wmic path win32_videocontroller get caption", shell=True).decode().split("\n")[1].strip()
        elif platform.system() == "Linux":
            return subprocess.check_output("lspci | grep -i 'VGA\\|3D\\|Display'", shell=True).decode().split(": ")[-1].strip()
        elif platform.system() == "Darwin":
            return subprocess.check_output("system_profiler SPDisplaysDataType | grep 'Chipset Model'", shell=True).decode().split(": ")[-1].strip()
    except Exception:
        return "Unknown"

def get_vram_info():
    try:
        output = subprocess.check_output("nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits", shell=True).decode().strip()
        total_vram, used_vram, free_vram = map(int, output.split(','))
        vram_usage = (used_vram / total_vram) * 100 if total_vram > 0 else 0
        return total_vram, used_vram, free_vram, round(vram_usage, 1)
    except Exception:
        return None, None, None, None

def get_cuda_version():
    try:
        return subprocess.check_output("nvcc --version", shell=True).decode().split("release ")[-1].split(",")[0].strip()
    except Exception:
        return "Not Installed"

def get_graphics_framework():
    frameworks = {
        "Vulkan": "vulkaninfo | grep 'Vulkan Instance Version'",
        "OpenGL": "glxinfo | grep 'OpenGL version'"
    }
    installed = []
    for framework, cmd in frameworks.items():
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
            installed.append(f"{framework}: {output.split(':')[-1].strip()}")
        except Exception:
            continue
    return ", ".join(installed) if installed else "None"

def get_cpu_temperature():
    try:
        if platform.system() == "Windows":
            return "Use HWMonitor"
        elif platform.system() == "Linux":
            temp = subprocess.check_output("sensors | grep 'Package id 0'", shell=True).decode().split('+')[-1].split('°')[0].strip()
            return f"{temp}°C"
        elif platform.system() == "Darwin":
            return "Use iStat Menus"
    except Exception:
        return "Unknown"

def get_open_ports():
    open_ports = []
    try:
        with os.popen("netstat -tulnp" if platform.system() == "Linux" else "netstat -ano") as netstat_output:
            for line in netstat_output.readlines():
                parts = line.split()
                if "LISTEN" in line:
                    port = parts[3].split(":")[-1] if platform.system() != "Windows" else parts[1].split(":")[-1]
                    open_ports.append(port)
    except Exception:
        return "Unknown"
    return ", ".join(open_ports[:5]) + ("..." if len(open_ports) > 5 else "") if open_ports else "None"

def get_swap_memory():
    swap = psutil.swap_memory()
    total_swap = round(swap.total / (1024**3))
    used_swap = round(swap.used / (1024**3))
    free_swap = total_swap - used_swap
    swap_usage = swap.percent
    return total_swap, used_swap, free_swap, swap_usage

def get_installed_languages():
    languages = {
        "Python": "python --version",
        "Node.js": "node --version",
        "C": "gcc --version",
        "C++": "g++ --version",
        "C#": "dotnet --version",
        "Go": "go version",
        "Rust": "rustc --version",
        "Java": "java -version",
        "Perl": "perl --version",
        "Ruby": "ruby --version",
        "PHP": "php --version"
    }
    installed = []
    for lang, cmd in languages.items():
        try:
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            installed.append(lang)
        except Exception:
            continue
    return ", ".join(installed[:5]) + ("..." if len(installed) > 5 else "") if installed else "None"

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "Unknown"

def get_resolution():
    try:
        if platform.system() == "Linux":
            if "DISPLAY" in os.environ:
                output = subprocess.check_output("xrandr | grep '*'", shell=True).decode().strip()
                resolutions = [line.split()[0] for line in output.split('\n') if line]
                return ", ".join(resolutions)
            else:
                return "Headless"
        elif platform.system() == "Windows":
            import ctypes
            user32 = ctypes.windll.user32
            return f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
        elif platform.system() == "Darwin":
            output = subprocess.check_output("system_profiler SPDisplaysDataType | grep Resolution", shell=True).decode().strip()
            return output.split(": ")[1] if output else "Unknown"
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

def get_terminal():
    try:
        if platform.system() == "Linux":
            # Try to get terminal from environment variables
            term = os.environ.get('TERM', 'Unknown')
            term_program = os.environ.get('TERM_PROGRAM', '')
            
            # For modern terminal emulators
            if term_program:
                return term_program
            # For X11-based terminals
            elif "DISPLAY" in os.environ:
                ppid = os.getppid()
                with open(f"/proc/{ppid}/cmdline", 'rb') as f:
                    cmdline = f.read().decode().replace('\x00', ' ')
                return cmdline.split()[0].split('/')[-1]
            else:
                return term
        elif platform.system() == "Windows":
            return os.environ.get('WT_SESSION', 'Windows Terminal') or "cmd.exe"
        elif platform.system() == "Darwin":
            return os.environ.get('TERM_PROGRAM', 'Terminal')
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

def get_window_manager():
    try:
        if platform.system() == "Linux":
            if "DISPLAY" in os.environ:
                # Try to detect Wayland
                if "WAYLAND_DISPLAY" in os.environ:
                    return "Wayland"
                # Try to detect X11 window managers
                wm = subprocess.check_output("wmctrl -m | grep 'Name:'", shell=True).decode().split(':')[-1].strip()
                return wm if wm else "Unknown"
            else:
                return "Headless"
        elif platform.system() == "Windows":
            return "Windows Manager"
        elif platform.system() == "Darwin":
            return "Aqua"
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

def get_system_info():
    total_vram, used_vram, free_vram, vram_usage = get_vram_info()
    total_swap, used_swap, free_swap, swap_usage = get_swap_memory()
    disk_usage = psutil.disk_usage('/')
    ram = psutil.virtual_memory()
    
    info = {
        "System": {
            "Hostname": socket.gethostname(),
            "OS": f"{platform.system()} {platform.release()}",
            "OS Version": platform.version(),
            "Kernel": get_kernel_info(),
            "Uptime": str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))),
            "Shell": os.path.basename(os.environ.get('SHELL', 'Unknown')),
            "Python": platform.python_version(),
            "Window Manager": get_window_manager(),
        },
        "Display": {
            "Resolution": get_resolution(),
            "Terminal": get_terminal(),
        },
        "Hardware": {
            "CPU": get_cpu_info(),
            "Architecture": platform.architecture()[0],
            "Cores/Threads": f"{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}",
            "CPU Speed": f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "Unknown",
            "CPU Usage": f"{psutil.cpu_percent(interval=1)}%",
            "CPU Temp": get_cpu_temperature(),
            "GPU": get_gpu_info(),
            "VRAM": f"{used_vram}/{total_vram}MB ({vram_usage}%)" if total_vram else "Unknown",
            "RAM": f"{round(ram.used/(1024**3))}/{round(ram.total/(1024**3))}GB ({ram.percent}%)",
        },
        "Storage": {
            "Disk": f"{round(disk_usage.used/(1024**3))}/{round(disk_usage.total/(1024**3))}GB ({disk_usage.percent}%)",
            "Swap": f"{used_swap}/{total_swap}GB ({swap_usage}%)",
        },
        "Network": {
            "IP Address": get_ip_address(),
            "Open Ports": get_open_ports(),
        },
        "Software": {
            "CUDA": get_cuda_version(),
            "Graphics": get_graphics_framework(),
            "Languages": get_installed_languages(),
        }
    }
    return info

def display_system_info(info):
    # Clear screen and display header
    os.system('cls' if os.name == 'nt' else 'clear')
    print(HEADER_ART)
    
    max_key_length = max(len(key) for category in info.values() for key in category.keys())
    
    for category, data in info.items():
        print(f"{COLOR_CATEGORY}┌─{category.upper()}{'─' * (36 - len(category))}┐{COLOR_RESET}")
        for key, value in data.items():
            print(f"{COLOR_KEY}│ {key:<{max_key_length}} {COLOR_VALUE}{value}{COLOR_RESET}")
        print(f"{COLOR_CATEGORY}└{'─' * 38}┘{COLOR_RESET}\n")

if __name__ == "__main__":
    system_info = get_system_info()
    display_system_info(system_info)
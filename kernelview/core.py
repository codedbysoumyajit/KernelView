import os
import platform
import psutil
import socket
import subprocess
import time
import datetime
import re

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


{COLOR_RESET}{COLOR_ACCENT}  Is a Powerful System Information Tool{COLOR_RESET}
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
            cpu_info = platform.processor()
            if "ARM" in cpu_info:
                return cpu_info
            # More detailed CPU info for Windows
            try:
                output = subprocess.check_output("wmic cpu get name", shell=True).decode().split("\n")[1].strip()
                if output:
                    return output
            except:
                pass
            return cpu_info
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line or "Processor" in line or "Hardware" in line:
                        return line.split(": ")[-1].strip()
                # For ARM CPUs
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" not in line and ("Processor" in line or "Hardware" in line):
                            return line.split(": ")[-1].strip()
        elif platform.system() == "Darwin":
            output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).strip().decode()
            if not output:  # For Apple Silicon
                output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.core_count"]).strip().decode()
                return f"Apple M-series ({output} cores)"
            return output
    except Exception:
        return "Unknown"
    return "Unknown"

def get_gpu_info():
    try:
        if platform.system() == "Windows":
            try:
                # Try NVIDIA first
                output = subprocess.check_output("nvidia-smi --query-gpu=name --format=csv,noheader", shell=True).decode().strip()
                if output:
                    return output.split("\n")[0]
            except:
                pass

            try:
                # Try AMD
                output = subprocess.check_output("wmic path win32_videocontroller where 'name like \"%AMD%\"' get name", shell=True).decode().strip()
                if output and "Name" not in output:
                    return output.split("\n")[1].strip()
            except:
                pass

            try:
                # Try Intel
                output = subprocess.check_output("wmic path win32_videocontroller where 'name like \"%Intel%\"' get name", shell=True).decode().strip()
                if output and "Name" not in output:
                    return output.split("\n")[1].strip()
            except:
                pass

            # Fallback to generic method
            return subprocess.check_output("wmic path win32_videocontroller get name", shell=True).decode().split("\n")[1].strip()

        elif platform.system() == "Linux":
            try:
                # Try NVIDIA
                output = subprocess.check_output("lspci | grep -i 'NVIDIA'", shell=True).decode().strip()
                if output:
                    return output.split(": ")[-1].strip()
            except:
                pass

            try:
                # Try AMD
                output = subprocess.check_output("lspci | grep -i 'AMD'", shell=True).decode().strip()
                if output:
                    return output.split(": ")[-1].strip()
            except:
                pass

            try:
                # Try Intel
                output = subprocess.check_output("lspci | grep -i 'Intel'", shell=True).decode().strip()
                if output:
                    return output.split(": ")[-1].strip()
            except:
                pass

            # Fallback to generic VGA
            return subprocess.check_output("lspci | grep -i 'VGA\\|3D\\|Display'", shell=True).decode().split(": ")[-1].strip()

        elif platform.system() == "Darwin":
            try:
                output = subprocess.check_output("system_profiler SPDisplaysDataType | grep 'Chipset Model'", shell=True).decode().strip()
                if output:
                    return output.split(": ")[-1].strip()
            except:
                return "Apple GPU"
    except Exception:
        return "Unknown"

def get_vram_info():
    try:
        if platform.system() == "Windows":
            try:
                # NVIDIA
                output = subprocess.check_output("nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits", shell=True).decode().strip()
                if output:
                    total_vram, used_vram, free_vram = map(int, output.split(','))
                    vram_usage = (used_vram / total_vram) * 100 if total_vram > 0 else 0
                    return total_vram, used_vram, free_vram, round(vram_usage, 1)
            except:
                pass

            try:
                # AMD - requires AMD Adrenalin software installed
                output = subprocess.check_output("clinfo", shell=True).decode()
                if "CL_DEVICE_GLOBAL_MEM_SIZE" in output:
                    for line in output.split("\n"):
                        if "CL_DEVICE_GLOBAL_MEM_SIZE" in line:
                            total_vram = int(line.split()[-1]) // (1024**2)
                            # AMD doesn't provide used/free easily, so we'll just show total
                            return total_vram, None, None, None
            except:
                pass

            try:
                # Intel - approximate from shared memory
                output = subprocess.check_output("wmic path win32_videocontroller get AdapterRAM", shell=True).decode().strip()
                if output and "AdapterRAM" not in output:
                    total_vram = int(output.split("\n")[1].strip()) // (1024**2)
                    return total_vram, None, None, None
            except:
                pass

        elif platform.system() == "Linux":
            try:
                # NVIDIA
                output = subprocess.check_output("nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits", shell=True).decode().strip()
                if output:
                    total_vram, used_vram, free_vram = map(int, output.split(','))
                    vram_usage = (used_vram / total_vram) * 100 if total_vram > 0 else 0
                    return total_vram, used_vram, free_vram, round(vram_usage, 1)
            except:
                pass

            try:
                # AMD - using ROCm
                output = subprocess.check_output("rocm-smi --showmeminfo vram --csv", shell=True).decode()
                if "vram" in output:
                    total_line = [line for line in output.split("\n") if "Total Memory" in line][0]
                    used_line = [line for line in output.split("\n") if "Used Memory" in line][0]
                    total_vram = int(total_line.split(",")[1].strip())
                    used_vram = int(used_line.split(",")[1].strip())
                    free_vram = total_vram - used_vram
                    vram_usage = (used_vram / total_vram) * 100 if total_vram > 0 else 0
                    return total_vram, used_vram, free_vram, round(vram_usage, 1)
            except:
                pass

            try:
                # Intel - using intel_gpu_top needs root
                output = subprocess.check_output("sudo intel_gpu_top -o -", shell=True).decode()
                if "GPU" in output:
                    for line in output.split("\n"):
                        if "VRAM" in line:
                            parts = line.split()
                            total_vram = int(parts[1])
                            used_vram = int(parts[2])
                            free_vram = total_vram - used_vram
                            vram_usage = (used_vram / total_vram) * 100 if total_vram > 0 else 0
                            return total_vram, used_vram, free_vram, round(vram_usage, 1)
            except:
                pass

        elif platform.system() == "Darwin":
            try:
                output = subprocess.check_output("system_profiler SPDisplaysDataType | grep 'VRAM'", shell=True).decode()
                if output:
                    total_vram = int(output.split(":")[1].strip().split(" ")[0])
                    return total_vram, None, None, None
            except:
                pass

    except Exception:
        pass

    return None, None, None, None

def get_cuda_version():
    try:
        output = subprocess.check_output("nvcc --version", shell=True).decode()
        if "release" in output:
            return output.split("release ")[-1].split(",")[0].strip()
    except Exception:
        pass

    # Check for CUDA in Windows registry
    if platform.system() == "Windows":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\NVIDIA Corporation\CUDA") as key:
                version = winreg.QueryValueEx(key, "Version")[0]
                return f"CUDA {version}"
        except:
            pass

    return "Not Installed"

def get_directx_version():
    try:
        if platform.system() == "Windows":
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\DirectX") as key:
                    version = winreg.QueryValueEx(key, "Version")[0]
                    return f"DirectX {version}"
            except:
                # Alternative method for newer Windows versions
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\DirectX") as key:
                        version = winreg.QueryValueEx(key, "Version")[0]
                        return f"DirectX {version}"
                except:
                    # Fallback to system file version
                    try:
                        dxdiag = subprocess.check_output("dxdiag /t dxdiag.txt", shell=True).decode()
                        with open("dxdiag.txt", "r") as f:
                            content = f.read()
                            match = re.search(r"DirectX Version: ([\d.]+)", content)
                            if match:
                                return f"DirectX {match.group(1)}"
                    except:
                        pass
        return "Not Windows"
    except Exception:
        return "Unknown"

def get_graphics_framework():
    frameworks = []

    # Windows specific
    if platform.system() == "Windows":
        # DirectX
        dx_version = get_directx_version()
        if "Unknown" not in dx_version and "Not Windows" not in dx_version:
            frameworks.append(dx_version)

        # Vulkan
        try:
            output = subprocess.check_output("vulkaninfo --summary", shell=True).decode()
            if "Vulkan Instance Version" in output:
                version = output.split("Vulkan Instance Version: ")[1].split("\n")[0].strip()
                frameworks.append(f"Vulkan {version}")
        except:
            pass

        # OpenGL
        try:
            import ctypes
            opengl = ctypes.windll.opengl32
            version = ctypes.c_char_p()
            opengl.glGetString.restype = ctypes.c_char_p
            version = opengl.glGetString(7938)  # GL_VERSION
            if version:
                frameworks.append(f"OpenGL {version.decode().split()[0]}")
        except:
            pass

    # Linux/macOS specific
    else:
        # Vulkan
        try:
            output = subprocess.check_output("vulkaninfo | grep 'Vulkan Instance Version'", shell=True).decode().strip()
            if output:
                frameworks.append(f"Vulkan: {output.split(':')[-1].strip()}")
        except:
            pass

        # OpenGL
        try:
            output = subprocess.check_output("glxinfo | grep 'OpenGL version'", shell=True).decode().strip()
            if output:
                frameworks.append(f"OpenGL: {output.split(':')[-1].strip()}")
        except:
            pass

    # Metal for macOS
    if platform.system() == "Darwin":
        frameworks.append("Metal")

    return ", ".join(frameworks) if frameworks else "None"

def get_cpu_temperature():
    try:
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output("wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature", shell=True).decode()
                if "CurrentTemperature" in output:
                    temp_kelvin = int(output.split("\n")[1].strip()) / 10.0
                    temp_celsius = temp_kelvin - 273.15
                    return f"{temp_celsius:.1f}°C"
            except:
                return "Use HWMonitor"
        elif platform.system() == "Linux":
            # Try multiple common temperature sources
            sources = [
                "sensors | grep 'Package id 0'",
                "sensors | grep 'Tdie'",
                "sensors | grep 'CPU Temperature'",
                "cat /sys/class/thermal/thermal_zone*/temp"
            ]
            for source in sources:
                try:
                    if "cat" in source:
                        temps = []
                        for zone in os.listdir("/sys/class/thermal/"):
                            if zone.startswith("thermal_zone"):
                                with open(f"/sys/class/thermal/{zone}/type") as f:
                                    if "cpu" in f.read().lower():
                                        with open(f"/sys/class/thermal/{zone}/temp") as temp_file:
                                            temp = int(temp_file.read().strip()) / 1000.0
                                            temps.append(temp)
                        if temps:
                            return f"{max(temps):.1f}°C"
                    else:
                        output = subprocess.check_output(source, shell=True).decode()
                        if output:
                            temp = output.split('+')[-1].split('°')[0].strip()
                            return f"{temp}°C"
                except:
                    continue
            return "Unknown"
        elif platform.system() == "Darwin":
            try:
                output = subprocess.check_output(["osascript", "-e", "tell application \"iStat Menus\" to get temperature of first sensor"], shell=False).decode().strip()
                if output:
                    return f"{output}°C"
            except:
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
    try:
        swap = psutil.swap_memory()
        total_swap = round(swap.total / (1024**3), 1)
        used_swap = round(swap.used / (1024**3), 1)
        free_swap = round(total_swap - used_swap, 1)
        swap_usage = swap.percent
        return total_swap, used_swap, free_swap, swap_usage
    except Exception:
        return 0, 0, 0, 0  # Return zeros if swap info not available

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
            version_output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
            if version_output:
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
            # Check Windows Terminal first
            if os.environ.get('WT_SESSION'):
                return "Windows Terminal"
            # Check for ConEmu
            if os.environ.get('ConEmuPID'):
                return "ConEmu"
            # Check for other terminals
            try:
                parent_process = psutil.Process(os.getppid()).name()
                if parent_process.endswith('.exe'):
                    parent_process = parent_process[:-4]
                return parent_process
            except:
                return "cmd.exe"
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
                try:
                    wm = subprocess.check_output("wmctrl -m | grep 'Name:'", shell=True).decode().split(':')[-1].strip()
                    if wm:
                        return wm
                except:
                    pass
                # Try to detect from environment variables
                desktop = os.environ.get('XDG_CURRENT_DESKTOP', '')
                if desktop:
                    return desktop.split(':')[-1]
                return "Unknown"
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

def get_shell():
    try:
        if platform.system() == "Windows":
            # Check for PowerShell
            if "PSModulePath" in os.environ:
                return "PowerShell"
            # Check for Git Bash
            if "SHELL" in os.environ and "git" in os.environ["SHELL"].lower():
                return "Git Bash"
            # Default to cmd
            return "cmd.exe"
        else:
            shell = os.environ.get('SHELL', 'Unknown')
            return os.path.basename(shell)
    except Exception:
        return "Unknown"

def get_system_info():
    total_vram, used_vram, free_vram, vram_usage = get_vram_info()
    total_swap, used_swap, free_swap, swap_usage = get_swap_memory()
    disk_usage = psutil.disk_usage('/')
    ram = psutil.virtual_memory()

    # Format VRAM information
    vram_display = "Unknown"
    if total_vram is not None:
        if used_vram is not None and vram_usage is not None:
            vram_display = f"{used_vram}/{total_vram}MB ({vram_usage}%)"
        else:
            vram_display = f"{total_vram}MB (total)"

    info = {
        "System": {
            "OS": f"{platform.system()} {platform.release()}",
            "OS Version": platform.version(),
            "Kernel": get_kernel_info(),
            "Uptime": str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))),
            "Shell": get_shell(),
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
            "VRAM": vram_display,
            "RAM": f"{round(ram.used/(1024**3), 1)}/{round(ram.total/(1024**3), 1)}GB ({ram.percent}%)",
        },
        "Storage": {
            "Disk": f"{round(disk_usage.used/(1024**3), 1)}/{round(disk_usage.total/(1024**3), 1)}GB ({disk_usage.percent}%)",
            "Swap": f"{used_swap}/{total_swap}GB ({swap_usage}%)",
        },
        "Network": {
            "Hostname": socket.gethostname(),
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
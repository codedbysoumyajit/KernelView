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
            # Try to get detailed ARM info on Windows
            try:
                import wmi
                w = wmi.WMI()
                for processor in w.Win32_Processor():
                    if "ARM" in processor.Architecture:
                        return f"{processor.Name} ({processor.Architecture})"
            except:
                pass
            return platform.processor()
        
        elif platform.system() == "Linux":
            # Check for ARM architecture first
            with open("/proc/cpuinfo") as f:
                cpuinfo = f.read()
            
            # ARM-specific detection
            if "ARM" in platform.machine() or "aarch64" in platform.machine():
                model_name = "Unknown ARM"
                implementer = "Unknown"
                part = "Unknown"
                
                # Try to get CPU implementer and architecture
                for line in cpuinfo.split('\n'):
                    if "model name" in line:
                        model_name = line.split(": ")[-1].strip()
                    elif "CPU implementer" in line:
                        implementer = line.split(": ")[-1].strip()
                    elif "CPU part" in line:
                        part = line.split(": ")[-1].strip()
                
                # Map ARM implementer codes to names
                implementer_map = {
                    "0x41": "ARM",
                    "0x42": "Broadcom",
                    "0x43": "Cavium",
                    "0x44": "DEC",
                    "0x46": "Fujitsu",
                    "0x48": "HiSilicon",
                    "0x49": "Infineon",
                    "0x4d": "Motorola/Freescale",
                    "0x4e": "NVIDIA",
                    "0x50": "APM",
                    "0x51": "Qualcomm",
                    "0x53": "Samsung",
                    "0x56": "Marvell",
                    "0x61": "Apple",
                    "0x66": "Faraday",
                    "0x69": "Intel",
                }
                
                # Map ARM part numbers to core types
                part_map = {
                    "0xd03": "Cortex-A53",
                    "0xd04": "Cortex-A35",
                    "0xd05": "Cortex-A55",
                    "0xd07": "Cortex-A57",
                    "0xd08": "Cortex-A72",
                    "0xd09": "Cortex-A73",
                    "0xd0a": "Cortex-A75",
                    "0xd0b": "Cortex-A76",
                    "0xd0c": "Neoverse-N1",
                    "0xd0d": "Cortex-A77",
                    "0xd0e": "Cortex-A76AE",
                    "0xd41": "Cortex-A78",
                    "0xd42": "Cortex-A78AE",
                    "0xd44": "Cortex-X1",
                    "0xd46": "Cortex-A510",
                    "0xd47": "Cortex-A710",
                    "0xd48": "Cortex-X2",
                }
                
                # Format the output
                vendor = implementer_map.get(implementer, implementer)
                core = part_map.get(part, part)
                
                if model_name != "Unknown ARM":
                    return model_name
                elif vendor != "Unknown" or core != "Unknown":
                    return f"{vendor} {core}"
                else:
                    return "ARM Processor"
            
            # Standard x86 detection
            for line in cpuinfo.split('\n'):
                if "model name" in line:
                    return line.split(": ")[-1].strip()
            return platform.machine()
        
        elif platform.system() == "Darwin":
            # Apple Silicon detection
            if platform.machine() == "arm64":
                try:
                    # Get Apple-specific processor info
                    output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).strip().decode()
                    if output:
                        return output
                    
                    # Fallback to generic ARM info
                    output = subprocess.check_output(["sysctl", "-n", "hw.model"]).strip().decode()
                    return f"Apple {output}"
                except:
                    return "Apple Silicon (ARM)"
            else:
                return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).strip().decode()
        
        else:
            # Other UNIX-like systems
            try:
                if "ARM" in platform.machine():
                    return f"ARM Processor ({platform.machine()})"
                return subprocess.check_output(["uname", "-p"]).decode().strip()
            except:
                return platform.machine()
    
    except Exception as e:
        return f"Unknown ({platform.machine()})"

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
        # Try NVIDIA first
        try:
            output = subprocess.check_output("nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits", shell=True).decode().strip()
            if output:
                total_vram, used_vram, free_vram = map(int, output.split(','))
                vram_usage = (used_vram / total_vram) * 100 if total_vram > 0 else 0
                return total_vram, used_vram, free_vram, round(vram_usage, 1)
        except:
            pass
        
        # Try AMD on Linux (using radeontop)
        if platform.system() == "Linux":
            try:
                # First try to get total VRAM
                total_vram = 0
                try:
                    output = subprocess.check_output("lspci -v -s $(lspci | grep VGA | cut -d' ' -f1)", shell=True).decode()
                    match = re.search(r'Memory.*?(\d+)MB', output)
                    if match:
                        total_vram = int(match.group(1))
                except:
                    pass
                
                # Try to get current usage via radeontop
                if total_vram > 0:
                    try:
                        # Run radeontop in snapshot mode (-1) and get vram usage
                        output = subprocess.check_output("radeontop -d - -l 1 | grep vram", shell=True).decode()
                        match = re.search(r'vram\s+(\d+)/(\d+)MB', output)
                        if match:
                            used_vram = int(match.group(1))
                            total_vram = int(match.group(2))  # Use detected total from radeontop
                            vram_usage = (used_vram / total_vram) * 100
                            return total_vram, used_vram, total_vram - used_vram, round(vram_usage, 1)
                    except:
                        pass
                
                if total_vram > 0:
                    return total_vram, None, None, None
            except:
                pass
        
        # Try Intel on Linux
        if platform.system() == "Linux":
            try:
                # Check for Intel GPU
                output = subprocess.check_output("lspci -v -s $(lspci | grep VGA | cut -d' ' -f1)", shell=True).decode()
                if "Intel" in output:
                    # Try to get VRAM info from intel_gpu_top (needs root)
                    try:
                        output = subprocess.check_output("sudo intel_gpu_top -l 1 -o -", shell=True).decode()
                        match = re.search(r'VRAM:\s+(\d+\.\d+)%', output)
                        if match:
                            vram_usage = float(match.group(1))
                            # Intel shares memory, so we'll report usage percentage only
                            return None, None, None, round(vram_usage, 1)
                    except:
                        pass
            except:
                pass
        
        # Try Windows (all GPUs)
        if platform.system() == "Windows":
            try:
                import wmi
                w = wmi.WMI()
                for gpu in w.Win32_VideoController():
                    if gpu.AdapterRAM:
                        total_vram = int(gpu.AdapterRAM) // (1024**2)
                        # Windows doesn't provide used VRAM easily
                        return total_vram, None, None, None
            except:
                pass
        
        # Try macOS
        if platform.system() == "Darwin":
            try:
                output = subprocess.check_output("system_profiler SPDisplaysDataType", shell=True).decode()
                match = re.search(r'VRAM \(Total\):\s+(\d+)', output)
                if match:
                    total_vram = int(match.group(1))
                    return total_vram, None, None, None
            except:
                pass
        
        return None, None, None, None
    except Exception as e:
        return None, None, None, None

def get_cuda_version():
    try:
        return subprocess.check_output("nvcc --version", shell=True).decode().split("release ")[-1].split(",")[0].strip()
    except Exception:
        return "Not Installed"

def get_opencl_info():
    try:
        if platform.system() == "Windows":
            try:
                import wmi
                w = wmi.WMI()
                opencl_devices = []
                for gpu in w.Win32_VideoController():
                    if "OpenCL" in gpu.Description:
                        opencl_devices.append(gpu.Description)
                if opencl_devices:
                    return ", ".join(opencl_devices)
            except:
                pass

        # Try using clinfo if available
        try:
            output = subprocess.check_output("clinfo", shell=True, stderr=subprocess.STDOUT).decode()
            devices = []
            for line in output.split('\n'):
                if "Device Name" in line:
                    devices.append(line.split("Device Name")[-1].strip())
            if devices:
                return ", ".join(devices[:3]) + ("..." if len(devices) > 3 else "")
        except:
            pass

        # Try alternative methods on Linux/macOS
        try:
            if platform.system() == "Linux":
                output = subprocess.check_output("ls -l /etc/OpenCL/vendors", shell=True).decode()
                if "libnvidia" in output:
                    return "NVIDIA OpenCL"
                elif "intel" in output.lower():
                    return "Intel OpenCL"
                elif "amd" in output.lower():
                    return "AMD OpenCL"
            elif platform.system() == "Darwin":
                return "Apple OpenCL"  # macOS has built-in OpenCL support
        except:
            pass

        return "Not Detected"
    except Exception:
        return "Unknown"

def get_vulkan_info():
    try:
        vulkan_info = []

        # Try vulkaninfo if available
        try:
            output = subprocess.check_output("vulkaninfo --summary", shell=True, stderr=subprocess.STDOUT).decode()
            # Extract GPU information
            gpu_info = []
            in_gpu_section = False
            for line in output.split('\n'):
                if "GPU id:" in line:
                    in_gpu_section = True
                    gpu_info.append(line.split(":")[-1].strip())
                elif in_gpu_section and "GPU name:" in line:
                    gpu_info.append(line.split(":")[-1].strip())
                    in_gpu_section = False

            if gpu_info:
                vulkan_info.append("Devices: " + ", ".join(gpu_info))

            # Extract Vulkan version
            version_match = re.search(r"Vulkan Instance Version:\s+(\d+\.\d+\.\d+)", output)
            if version_match:
                vulkan_info.append(f"Version: {version_match.group(1)}")
        except:
            pass

        # Fallback for Windows
        if platform.system() == "Windows" and not vulkan_info:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Khronos\Vulkan") as key:
                    version = winreg.QueryValueEx(key, "Version")[0]
                    vulkan_info.append(f"Version: {version}")
            except:
                pass

        # Fallback for Linux
        if platform.system() == "Linux" and not vulkan_info:
            try:
                icd_files = subprocess.check_output("ls /usr/share/vulkan/icd.d/", shell=True).decode()
                if "nvidia" in icd_files.lower():
                    vulkan_info.append("NVIDIA Vulkan")
                if "radeon" in icd_files.lower() or "amd" in icd_files.lower():
                    vulkan_info.append("AMD Vulkan")
                if "intel" in icd_files.lower():
                    vulkan_info.append("Intel Vulkan")
            except:
                pass

        return ", ".join(vulkan_info) if vulkan_info else "Not Installed"
    except Exception:
        return "Unknown"

def get_directx_version():
    try:
        if platform.system() == "Windows":
            try:
                import winreg
                # Check for DirectX 12
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\DirectX") as key:
                        version = winreg.QueryValueEx(key, "Version")[0]
                        return f"DirectX {version}"
                except:
                    pass

                # Check for DirectX 11
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Direct3D") as key:
                        version = winreg.QueryValueEx(key, "Version")[0]
                        return f"DirectX {version}"
                except:
                    pass

                # Fallback method using dxdiag
                try:
                    output = subprocess.check_output("dxdiag /t dxdiag_output.txt", shell=True)
                    with open("dxdiag_output.txt", "r") as f:
                        content = f.read()
                        match = re.search(r"DirectX Version:\s+DirectX (\d+)", content)
                        if match:
                            return f"DirectX {match.group(1)}"
                except:
                    pass

                # Final fallback
                return "DirectX (version unknown)"
            except:
                return "DirectX (detection failed)"
        else:
            return "Windows Only"
    except Exception:
        return "Unknown"

def get_graphics_framework():
    frameworks = {
        "Vulkan": get_vulkan_info(),
        "DirectX": get_directx_version(),
        "OpenCL": get_opencl_info()
    }

    # Format the output
    result = []
    for name, value in frameworks.items():
        if value and value != "Unknown" and value != "Not Detected" and value != "Windows Only":
            result.append(f"{name}: {value}")

    return ", ".join(result) if result else "None detected"

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
    try:
        swap = psutil.swap_memory()
        total_swap = round(swap.total / (1024**3))
        used_swap = round(swap.used / (1024**3))
        free_swap = total_swap - used_swap
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
                try:
                    wm = subprocess.check_output("wmctrl -m | grep 'Name:'", shell=True).decode().split(':')[-1].strip()
                    return wm if wm else "Unknown"
                except:
                    return os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')
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
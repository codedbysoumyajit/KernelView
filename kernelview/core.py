import os
import platform
import psutil
import socket
import subprocess
import time
import datetime
import re

# Modern color scheme with better contrast
COLOR_HEADER = "\033[34m"  # Bright red
COLOR_CATEGORY = "\033[34m"  # Blue
COLOR_KEY = "\033[38;5;255m"  # Bright white
COLOR_VALUE = "\033[38;5;249m"  # Light gray
COLOR_ACCENT = "\033[34m"  # Blue
COLOR_RESET = "\033[0m"

# Compact ASCII art header
if platform.system() == "Linux":
    HEADER_ART = rf"""
{COLOR_HEADER}
    __    _                 
   / /   (_)___  __  ___  __
  / /   / / __ \/ / / / |/_/
 / /___/ / / / / /_/ />  <  
/_____/_/_/ /_/\__,_/_/|_|  
                            
{COLOR_RESET}{COLOR_ACCENT}         KernelView{COLOR_RESET}"""
elif platform.system() == "Windows":
    HEADER_ART = rf"""
    {COLOR_HEADER}
 _       ___           __                  
| |     / (_)___  ____/ /___ _      _______
| | /| / / / __ \/ __  / __ \ | /| / / ___/
| |/ |/ / / / / / /_/ / /_/ / |/ |/ (__  ) 
|__/|__/_/_/ /_/\__,_/\____/|__/|__/____/  
                                           
{COLOR_RESET}{COLOR_ACCENT}         KernelView{COLOR_RESET}"""
elif platform.system() == "Darwin":
    HEADER_ART = rf"""
{COLOR_HEADER}
    __  ___           ____  _____
   /  |/  /___ ______/ __ \/ ___/
  / /|_/ / __ `/ ___/ / / /\__ \ 
 / /  / / /_/ / /__/ /_/ /___/ / 
/_/  /_/\__,_/\___/\____//____/  
                                 
{COLOR_RESET}{COLOR_ACCENT}         KernelView{COLOR_RESET}"""


def get_os_info():
    try:
        system = platform.system()
        if system == "Linux":
            # Extended Linux distribution detection
            distro = "Linux"
            version = platform.release()

            # Check for /etc/os-release first (modern standard)
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    os_release = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_release[key] = value.strip('"')

                    distro = os_release.get('NAME', 'Linux')
                    version = os_release.get('VERSION', platform.release())

                    # Handle special cases for popular distros
                    distro_map = {
                        'ubuntu': 'Ubuntu',
                        'fedora': 'Fedora',
                        'debian': 'Debian',
                        'arch': 'Arch Linux',
                        'manjaro': 'Manjaro',
                        'centos': 'CentOS',
                        'rhel': 'Red Hat Enterprise Linux',
                        'opensuse': 'openSUSE',
                        'alpine': 'Alpine Linux',
                        'kali': 'Kali Linux',
                        'pop': 'Pop!_OS',
                        'elementary': 'elementary OS',
                        'zorin': 'Zorin OS',
                        'mint': 'Linux Mint'
                    }

                    # Get pretty name if available
                    pretty_name = os_release.get('PRETTY_NAME',
                                                 f"{distro} {version}")

                    # Apply distro mapping
                    for key, value in distro_map.items():
                        if key.lower() in distro.lower():
                            pretty_name = pretty_name.replace(distro, value)
                            break

                    return pretty_name

            # Check for older /etc/lsb-release
            if os.path.exists("/etc/lsb-release"):
                with open("/etc/lsb-release") as f:
                    lsb_release = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            lsb_release[key] = value.strip('"')

                    if 'DISTRIB_DESCRIPTION' in lsb_release:
                        return lsb_release['DISTRIB_DESCRIPTION']
                    elif 'DISTRIB_ID' in lsb_release and 'DISTRIB_RELEASE' in lsb_release:
                        return f"{lsb_release['DISTRIB_ID']} {lsb_release['DISTRIB_RELEASE']}"

            # Check for specific distribution files
            distro_files = {
                '/etc/redhat-release': 'Red Hat',
                '/etc/debian_version': 'Debian',
                '/etc/alpine-release': 'Alpine Linux',
                '/etc/arch-release': 'Arch Linux',
                '/etc/gentoo-release': 'Gentoo',
                '/etc/slackware-version': 'Slackware'
            }

            for file, name in distro_files.items():
                if os.path.exists(file):
                    with open(file) as f:
                        return f"{name} {f.read().strip()}"

            # Fallback to generic Linux info
            return f"Linux {version}"

        elif system == "Windows":
            # Comprehensive Windows version mapping
            try:
                import winreg
                with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
                ) as key:
                    product_name = winreg.QueryValueEx(key, "ProductName")[0]
                    release_id = winreg.QueryValueEx(key, "DisplayVersion")[0]
                    build_number = winreg.QueryValueEx(key,
                                                       "CurrentBuildNumber")[0]
                    ubr = winreg.QueryValueEx(key, "UBR")[0] if "UBR" in [
                        x[0] for x in winreg.EnumValue(key, 0)[1]
                    ] else 0

                    # Extended Windows version map
                    version_map = {
                        '10.0.22631': '11 (23H2)',
                        '10.0.22621': '11 (22H2)',
                        '10.0.22000': '11 (21H2)',
                        '10.0.19045': '10 (22H2)',
                        '10.0.19044': '10 (21H2)',
                        '10.0.19043': '10 (21H1)',
                        '10.0.19042': '10 (20H2)',
                        '10.0.19041': '10 (2004)',
                        '10.0.18363': '10 (1909)',
                        '10.0.18362': '10 (1903)',
                        '10.0.17763': '10 (1809)',
                        '10.0.17134': '10 (1803)',
                        '10.0.16299': '10 (1709)',
                        '10.0.15063': '10 (1703)',
                        '10.0.14393': '10 (1607)',
                        '10.0.10586': '10 (1511)',
                        '10.0.10240': '10 (1507)',
                        '6.3.9600': '8.1',
                        '6.2.9200': '8',
                        '6.1.7601': '7 SP1',
                        '6.1.7600': '7',
                        '6.0.6002': 'Vista SP2',
                        '6.0.6001': 'Vista SP1',
                        '6.0.6000': 'Vista',
                        '5.2.3790': 'Server 2003',
                        '5.1.2600': 'XP',
                        '5.0.2195': '2000'
                    }

                    version_key = f"{platform.version().split('.')[0]}.{platform.version().split('.')[1]}.{build_number}"
                    friendly_name = version_map.get(version_key,
                                                    platform.version())

                    return f"{product_name} {friendly_name} (Build {build_number}.{ubr})"
            except Exception as e:
                return f"Windows {platform.release()} {platform.version()}"

        elif system == "Darwin":
            # Comprehensive macOS version mapping
            try:
                product_version = subprocess.check_output(
                    ["sw_vers", "-productVersion"]).decode().strip()

                # Extended macOS version map
                version_map = {
                    '14.': 'Sonoma',
                    '13.': 'Ventura',
                    '12.': 'Monterey',
                    '11.': 'Big Sur',
                    '10.15': 'Catalina',
                    '10.14': 'Mojave',
                    '10.13': 'High Sierra',
                    '10.12': 'Sierra',
                    '10.11': 'El Capitan',
                    '10.10': 'Yosemite',
                    '10.9': 'Mavericks',
                    '10.8': 'Mountain Lion',
                    '10.7': 'Lion',
                    '10.6': 'Snow Leopard',
                    '10.5': 'Leopard',
                    '10.4': 'Tiger',
                    '10.3': 'Panther',
                    '10.2': 'Jaguar',
                    '10.1': 'Puma',
                    '10.0': 'Cheetah'
                }

                # Find matching version
                version_name = "macOS"
                for prefix, name in version_map.items():
                    if product_version.startswith(prefix):
                        version_name = f"macOS {name}"
                        break

                # Add version details
                build_version = subprocess.check_output(
                    ["sw_vers", "-buildVersion"]).decode().strip()
                return f"{version_name} {product_version} (Build {build_version})"
            except:
                return "macOS"

        else:
            return platform.platform()
    except Exception:
        return platform.platform()


def get_shell():
    try:
        if platform.system() == "Windows":
            # Windows shell detection
            shell = os.environ.get('SHELL', '')

            # Check for PowerShell
            if 'PSModulePath' in os.environ:
                # Detect PowerShell version
                try:
                    ps_version = subprocess.check_output(
                        [
                            "powershell", "-Command",
                            "$PSVersionTable.PSVersion.ToString()"
                        ],
                        stderr=subprocess.DEVNULL).decode().strip()
                    return f"PowerShell {ps_version}"
                except:
                    return "PowerShell"

            # Check for Git Bash
            if 'MINGW' in os.environ.get('MSYSTEM',
                                         '') or 'git' in os.environ.get(
                                             'SHELL', '').lower():
                return "Git Bash"

            # Check for CMD vs other Windows terminals
            parent_process = None
            try:
                parent_process = psutil.Process(os.getppid()).name()
            except:
                pass

            if parent_process:
                if 'cmd.exe' in parent_process.lower():
                    return "CMD"
                elif 'powershell.exe' in parent_process.lower():
                    return "PowerShell"
                elif 'bash.exe' in parent_process.lower():
                    return "Bash"
                elif 'zsh.exe' in parent_process.lower():
                    return "Zsh"
                elif 'fish.exe' in parent_process.lower():
                    return "Fish"

            # Fallback to checking COMSPEC
            if 'COMSPEC' in os.environ:
                if 'cmd.exe' in os.environ['COMSPEC'].lower():
                    return "CMD"

            return "Windows Terminal" if os.environ.get(
                'WT_SESSION') else "Unknown Windows Shell"

        else:  # Linux, macOS, etc.
            # Unix-like shell detection
            shell_path = os.environ.get('SHELL', '')

            if not shell_path:
                # Fallback method for getting shell
                try:
                    shell_path = subprocess.check_output(
                        ["ps", "-p",
                         str(os.getppid()), "-o", "comm="],
                        stderr=subprocess.DEVNULL).decode().strip()
                except:
                    pass

            if shell_path:
                shell_name = os.path.basename(shell_path)
                # Map common shell names
                shell_map = {
                    'bash': 'Bash',
                    'zsh': 'Zsh',
                    'fish': 'Fish',
                    'dash': 'Dash',
                    'ksh': 'KornShell',
                    'tcsh': 'Tcsh',
                    'csh': 'Csh',
                    'sh': 'Bourne Shell',
                    'ash': 'Almquist Shell',
                    'mksh': 'MirBSD KornShell'
                }

                # Get version if possible
                version = ''
                try:
                    if shell_name == 'bash':
                        version = subprocess.check_output(
                            [shell_path, "--version"],
                            stderr=subprocess.DEVNULL).decode().split(
                                '\n')[0].split(' ')[3].split('(')[0]
                    elif shell_name == 'zsh':
                        version = subprocess.check_output(
                            [shell_path, "--version"],
                            stderr=subprocess.DEVNULL).decode().split(
                                '\n')[0].split(' ')[1]
                    elif shell_name == 'fish':
                        version = subprocess.check_output(
                            [shell_path, "--version"],
                            stderr=subprocess.DEVNULL).decode().split(
                                '\n')[0].split(' ')[2]
                except:
                    pass

                display_name = shell_map.get(shell_name,
                                             shell_name.capitalize())
                return f"{display_name} {version}".strip(
                ) if version else display_name

            # Final fallback
            return "Unknown Unix Shell"
    except Exception:
        return "Unknown Shell"


def get_kernel_info():
    try:
        if platform.system() == "Linux":
            kernel_name = subprocess.check_output("uname -s",
                                                  shell=True).decode().strip()
            kernel_version = subprocess.check_output(
                "uname -r", shell=True).decode().strip()
            return f"{kernel_name} {kernel_version}"
        elif platform.system() == "Windows":
            return platform.win32_ver()[0]
        elif platform.system() == "Darwin":
            kernel_name = "Darwin"
            kernel_version = subprocess.check_output(
                "uname -r", shell=True).decode().strip()
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
                    "0x41": "ARM Ltd.",
                    "0x42": "Broadcom",
                    "0x43": "Cavium",
                    "0x44": "DEC",
                    "0x46": "Fujitsu",
                    "0x48": "HiSilicon",  # Huawei's chip division
                    "0x49": "Infineon",
                    "0x4d": "Motorola/Freescale",
                    "0x4e": "NVIDIA",
                    "0x50": "APM",
                    "0x51": "Qualcomm",
                    "0x53": "Samsung",
                    "0x56": "Marvell",
                    "0x58": "MediaTek",
                    "0x61": "Apple",
                    "0x66": "Faraday",
                    "0x69": "Intel",
                    "0x70": "Huawei",
                    "0x72": "Unisoc",
                    "0xc0": "Google",
                    "0xc8": "Ampere Computing"
                }

                # Map ARM part numbers to core types
                part_map = {
                    # Standard ARM Cores
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
                    "0xd49": "Cortex-X3",
                    "0xd4a": "Cortex-A715",
                    "0xd4b": "Cortex-X4",
                    "0xd4c": "Cortex-A720",

                    # Qualcomm
                    "0x200": "Kryo",
                    "0x201": "Kryo Silver",
                    "0x202": "Kryo Gold",
                    "0x203": "Kryo 4xx (Silver)",
                    "0x204": "Kryo 4xx (Gold)",
                    "0x205": "Kryo 5xx (Silver)",
                    "0x206": "Kryo 5xx (Gold)",
                    "0x207": "Kryo 6xx (Silver)",
                    "0x208": "Kryo 6xx (Gold)",
                    "0x209": "Kryo 7xx (Silver)",
                    "0x20a": "Kryo 7xx (Gold)",
                    "0x20b": "Oryon Performance",
                    "0x20c": "Oryon Efficiency",

                    # MediaTek
                    "0x300": "MediaTek Helio",
                    "0x301": "MediaTek Dimensity",
                    "0x302": "MediaTek Kompanio",

                    # Huawei/HiSilicon
                    "0x400": "Kirin 610",
                    "0x401": "Kirin 650",
                    "0x402": "Kirin 710",
                    "0x403": "Kirin 810",
                    "0x404": "Kirin 820",
                    "0x405": "Kirin 9000",
                    "0x410": "Taishan Small",
                    "0x411": "Taishan Medium",
                    "0x412": "Taishan Large",

                    # Google
                    "0xc00": "Tensor G1",
                    "0xc01": "Tensor G2",
                    "0xc02": "Tensor G3",
                    "0xc03": "Tensor G4",

                    # Ampere Computing
                    "0xc80": "Ampere Altra",
                    "0xc81": "Ampere Altra Max",
                    "0xc82": "Ampere One",
                    "0xc83": "Ampere eMAG",

                    # Unisoc
                    "0x600": "Tiger T310",
                    "0x601": "Tiger T610",
                    "0x602": "Tiger T618",
                    "0x603": "Tiger T700",
                    "0x610": "Leopard L510",
                    "0x611": "Leopard L610"
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
                    output = subprocess.check_output(
                        ["sysctl", "-n",
                         "machdep.cpu.brand_string"]).strip().decode()
                    if output:
                        return output

                    # Fallback to generic ARM info
                    output = subprocess.check_output(
                        ["sysctl", "-n", "hw.model"]).strip().decode()
                    return f"Apple {output}"
                except:
                    return "Apple Silicon (ARM)"
            else:
                return subprocess.check_output(
                    ["sysctl", "-n",
                     "machdep.cpu.brand_string"]).strip().decode()

        else:
            # Other UNIX-like systems
            try:
                if "ARM" in platform.machine():
                    return f"ARM Processor ({platform.machine()})"
                return subprocess.check_output(["uname",
                                                "-p"]).decode().strip()
            except:
                return platform.machine()

    except Exception as e:
        return f"Unknown ({platform.machine()})"


def get_gpu_info():
    try:
        if platform.system() == "Windows":
            return subprocess.check_output(
                "wmic path win32_videocontroller get caption",
                shell=True).decode().split("\n")[1].strip()
        elif platform.system() == "Linux":
            return subprocess.check_output(
                "lspci | grep -i 'VGA\\|3D\\|Display'",
                shell=True).decode().split(": ")[-1].strip()
        elif platform.system() == "Darwin":
            return subprocess.check_output(
                "system_profiler SPDisplaysDataType | grep 'Chipset Model'",
                shell=True).decode().split(": ")[-1].strip()
    except Exception:
        return "Unknown"


def get_vram_info():
    try:
        # Try NVIDIA first
        try:
            output = subprocess.check_output(
                "nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits",
                shell=True).decode().strip()
            if output:
                total_vram, used_vram, free_vram = map(int, output.split(','))
                vram_usage = (used_vram /
                              total_vram) * 100 if total_vram > 0 else 0
                return total_vram, used_vram, free_vram, round(vram_usage, 1)
        except:
            pass

        # Try AMD on Linux (using radeontop)
        if platform.system() == "Linux":
            try:
                # First try to get total VRAM
                total_vram = 0
                try:
                    output = subprocess.check_output(
                        "lspci -v -s $(lspci | grep VGA | cut -d' ' -f1)",
                        shell=True).decode()
                    match = re.search(r'Memory.*?(\d+)MB', output)
                    if match:
                        total_vram = int(match.group(1))
                except:
                    pass

                # Try to get current usage via radeontop
                if total_vram > 0:
                    try:
                        # Run radeontop in snapshot mode (-1) and get vram usage
                        output = subprocess.check_output(
                            "radeontop -d - -l 1 | grep vram",
                            shell=True).decode()
                        match = re.search(r'vram\s+(\d+)/(\d+)MB', output)
                        if match:
                            used_vram = int(match.group(1))
                            total_vram = int(match.group(
                                2))  # Use detected total from radeontop
                            vram_usage = (used_vram / total_vram) * 100
                            return total_vram, used_vram, total_vram - used_vram, round(
                                vram_usage, 1)
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
                output = subprocess.check_output(
                    "lspci -v -s $(lspci | grep VGA | cut -d' ' -f1)",
                    shell=True).decode()
                if "Intel" in output:
                    # Try to get VRAM info from intel_gpu_top (needs root)
                    try:
                        output = subprocess.check_output(
                            "sudo intel_gpu_top -l 1 -o -",
                            shell=True).decode()
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
                output = subprocess.check_output(
                    "system_profiler SPDisplaysDataType", shell=True).decode()
                match = re.search(r'VRAM \(Total\):\s+(\d+)', output)
                if match:
                    total_vram = int(match.group(1))
                    return total_vram, None, None, None
            except:
                pass

        return None, None, None, None
    except Exception as e:
        return None, None, None, None


def get_open_ports():
    open_ports = []
    try:
        with os.popen("netstat -tulnp" if platform.system() ==
                      "Linux" else "netstat -ano") as netstat_output:
            for line in netstat_output.readlines():
                parts = line.split()
                if "LISTEN" in line:
                    port = parts[3].split(":")[-1] if platform.system(
                    ) != "Windows" else parts[1].split(":")[-1]
                    open_ports.append(port)
    except Exception:
        return "Unknown"
    return ", ".join(open_ports[:5]) + (
        "..." if len(open_ports) > 5 else "") if open_ports else "None"


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
    return ", ".join(installed[:5]) + (
        "..." if len(installed) > 5 else "") if installed else "None"


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
                output = subprocess.check_output("xrandr | grep '*'",
                                                 shell=True).decode().strip()
                resolutions = [
                    line.split()[0] for line in output.split('\n') if line
                ]
                return ", ".join(resolutions)
            else:
                return "Headless"
        elif platform.system() == "Windows":
            import ctypes
            user32 = ctypes.windll.user32
            return f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
        elif platform.system() == "Darwin":
            output = subprocess.check_output(
                "system_profiler SPDisplaysDataType | grep Resolution",
                shell=True).decode().strip()
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
            return os.environ.get('WT_SESSION',
                                  'Windows Terminal') or "cmd.exe"
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
                    wm = subprocess.check_output(
                        "wmctrl -m | grep 'Name:'",
                        shell=True).decode().split(':')[-1].strip()
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


def get_system_locale():
    try:
        if platform.system() == "Windows":
            try:
                import ctypes
                windll = ctypes.windll.kernel32
                locale_id = windll.GetUserDefaultLCID()
                # Buffer for locale name
                buf = ctypes.create_unicode_buffer(85)
                if windll.LCIDToLocaleName(locale_id, buf, 85, 0):
                    return buf.value
                return f"LCID: {locale_id}"
            except:
                return os.environ.get('LANG', 'Unknown')

        elif platform.system() == "Linux" or platform.system() == "Darwin":
            # Try locale command first
            try:
                locale = subprocess.check_output("locale", shell=True).decode()
                lang_line = [
                    line for line in locale.split('\n')
                    if line.startswith('LANG=')
                ][0]
                return lang_line.split('=')[1].strip().replace('"', '')
            except:
                # Fallback to environment variables
                return os.environ.get('LANG',
                                      os.environ.get('LC_ALL', 'Unknown'))
        else:
            return os.environ.get('LANG', 'Unknown')
    except Exception:
        return "Unknown"


def get_desktop_environment():
    try:
        de = "Unknown"

        if platform.system() == "Linux":
            # Method 1: Check XDG_CURRENT_DESKTOP (most reliable)
            de = os.environ.get('XDG_CURRENT_DESKTOP', '')
            if de:
                return de.split(':')[-1]  # Handle cases like "ubuntu:GNOME"

            # Method 2: Check DESKTOP_SESSION
            de = os.environ.get('DESKTOP_SESSION', '')
            if de:
                return de.lower().capitalize()

            # Method 3: Check GDMSESSION
            de = os.environ.get('GDMSESSION', '')
            if de:
                return de.lower().capitalize()

            # Method 4: Check processes
            try:
                processes = subprocess.check_output("ps -e",
                                                    shell=True).decode()
                if "gnome-shell" in processes:
                    return "GNOME"
                elif "plasmashell" in processes:
                    return "KDE Plasma"
                elif "xfce4-session" in processes:
                    return "XFCE"
                elif "cinnamon-session" in processes:
                    return "Cinnamon"
                elif "mate-session" in processes:
                    return "MATE"
                elif "lxqt-session" in processes:
                    return "LXQt"
                elif "lxsession" in processes:
                    return "LXDE"
                elif "budgie-panel" in processes:
                    return "Budgie"
                elif "deepin-session" in processes:
                    return "Deepin"
            except:
                pass

            # Method 5: Check for Wayland
            if "WAYLAND_DISPLAY" in os.environ:
                return "Wayland"

            # Method 6: Check for Xfce (alternative method)
            if os.path.isdir("/usr/share/xfce4"):
                return "XFCE"

            return "Unknown (possibly headless)"

        elif platform.system() == "Windows":
            # Windows doesn't have desktop environments in the Linux sense,
            # but we can detect the major Windows version
            version = platform.win32_ver()
            if "10" in version[0]:
                return "Windows 10"
            elif "11" in version[0]:
                return "Windows 11"
            else:
                return f"Windows {version[0]}"

        elif platform.system() == "Darwin":
            return "macOS Aqua"

        else:
            return "Unknown"

    except Exception:
        return "Unknown"


def get_package_counts():
    try:
        packages = {}

        # Linux package managers
        if platform.system() == "Linux":
            # APT (Debian/Ubuntu)
            try:
                apt_count = int(
                    subprocess.check_output(
                        "dpkg-query -f '${binary:Package}\n' -W | wc -l",
                        shell=True).decode().strip())
                if apt_count > 0:
                    packages["APT"] = apt_count
            except:
                pass

            # Pacman (Arch)
            try:
                pacman_count = int(
                    subprocess.check_output("pacman -Qq | wc -l",
                                            shell=True).decode().strip())
                if pacman_count > 0:
                    packages["Pacman"] = pacman_count
            except:
                pass

            # DNF (Fedora)
            try:
                dnf_count = int(
                    subprocess.check_output("dnf list installed | wc -l",
                                            shell=True).decode().strip())
                if dnf_count > 0:
                    packages["DNF"] = dnf_count
            except:
                pass

            # RPM (RedHat)
            try:
                rpm_count = int(
                    subprocess.check_output("rpm -qa | wc -l",
                                            shell=True).decode().strip())
                if rpm_count > 0:
                    packages["RPM"] = rpm_count
            except:
                pass

            # Flatpak
            try:
                flatpak_count = int(
                    subprocess.check_output("flatpak list | wc -l",
                                            shell=True).decode().strip())
                if flatpak_count > 0:
                    packages["Flatpak"] = flatpak_count
            except:
                pass

            # Snap
            try:
                snap_count = int(
                    subprocess.check_output("snap list | wc -l",
                                            shell=True).decode().strip())
                if snap_count > 0:
                    packages["Snap"] = snap_count
            except:
                pass

            # AppImage (count files in common locations)
            try:
                appimage_count = 0
                for path in [
                        "/usr/local/bin",
                        os.path.expanduser("~/.local/bin"), "/opt"
                ]:
                    if os.path.exists(path):
                        appimage_count += len([
                            f for f in os.listdir(path)
                            if f.lower().endswith('.appimage')
                        ])
                if appimage_count > 0:
                    packages["AppImage"] = appimage_count
            except:
                pass

        # macOS package managers
        elif platform.system() == "Darwin":
            # Homebrew
            try:
                brew_count = int(
                    subprocess.check_output("brew list | wc -l",
                                            shell=True).decode().strip())
                if brew_count > 0:
                    packages["Homebrew"] = brew_count
            except:
                pass

            # MacPorts
            try:
                port_count = int(
                    subprocess.check_output("port installed | wc -l",
                                            shell=True).decode().strip())
                if port_count > 0:
                    packages["MacPorts"] = port_count
            except:
                pass

            # App Store apps (might require sudo)
            try:
                mas_count = int(
                    subprocess.check_output("mas list | wc -l",
                                            shell=True).decode().strip())
                if mas_count > 0:
                    packages["Mac App Store"] = mas_count
            except:
                pass

        # Windows package managers
        elif platform.system() == "Windows":
            # Chocolatey
            try:
                choco_count = int(
                    subprocess.check_output(
                        "choco list --local-only | measure-object | select -expand Count",
                        shell=True).decode().strip())
                if choco_count > 0:
                    packages["Chocolatey"] = choco_count
            except:
                pass

            # Winget
            try:
                winget_count = int(
                    subprocess.check_output(
                        "winget list | measure-object | select -expand Count",
                        shell=True).decode().strip())
                if winget_count > 0:
                    packages["Winget"] = winget_count
            except:
                pass

            # Scoop
            try:
                scoop_count = int(
                    subprocess.check_output(
                        "scoop list | measure-object | select -expand Count",
                        shell=True).decode().strip())
                if scoop_count > 0:
                    packages["Scoop"] = scoop_count
            except:
                pass

        # Format the output string
        if packages:
            return ", ".join([f"{k} ({v})" for k, v in packages.items()])
        return "None detected"

    except Exception:
        return "Unknown"


def get_system_info():
    total_vram, used_vram, free_vram, vram_usage = get_vram_info()
    total_swap, used_swap, free_swap, swap_usage = get_swap_memory()
    disk_usage = psutil.disk_usage('/')
    ram = psutil.virtual_memory()

    info = {
        "System": {
            "OS":
            get_os_info(),
            "Kernel":
            get_kernel_info(),
            "Uptime":
            str(
                datetime.timedelta(seconds=int(time.time() -
                                               psutil.boot_time()))),
            "Shell":
            get_shell(),
            "Python":
            platform.python_version(),
        },
        "Display": {
            "Resolution": get_resolution(),
            "Window Manager": get_window_manager(),
            "DE": get_desktop_environment(),
            "Terminal": get_terminal(),
        },
        "Hardware": {
            "CPU":
            get_cpu_info(),
            "Architecture":
            platform.architecture()[0],
            "Cores/Threads":
            f"{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}",
            "CPU Speed":
            f"{psutil.cpu_freq().current:.2f} MHz"
            if psutil.cpu_freq() else "Unknown",
            "CPU Usage":
            f"{psutil.cpu_percent(interval=1)}%",
            "GPU":
            get_gpu_info(),
            "VRAM":
            f"{used_vram}/{total_vram}MB ({vram_usage}%)"
            if total_vram else "Unknown",
            "RAM":
            f"{round(ram.used/(1024**3))}/{round(ram.total/(1024**3))}GB ({ram.percent}%)",
        },
        "Storage": {
            "Disk":
            f"{round(disk_usage.used/(1024**3))}/{round(disk_usage.total/(1024**3))}GB ({disk_usage.percent}%)",
            "Swap": f"{used_swap}/{total_swap}GB ({swap_usage}%)",
        },
        "Network": {
            "Hostname": socket.gethostname(),
            "Locale": get_system_locale(),
            "IP Address": get_ip_address(),
            "Open Ports": get_open_ports(),
        },
        "Software": {
            "Packages": get_package_counts(),
            "Languages": get_installed_languages(),
        }
    }
    return info


def display_system_info(info):
    # Clear screen and display header
    os.system('cls' if os.name == 'nt' else 'clear')
    print(HEADER_ART)

    max_key_length = max(
        len(key) for category in info.values() for key in category.keys())

    for category, data in info.items():
        print(
            f"{COLOR_CATEGORY}┌─{category.upper()}{'─' * (36 - len(category))}┐{COLOR_RESET}"
        )
        for key, value in data.items():
            print(
                f"{COLOR_KEY}│ {key:<{max_key_length}} {COLOR_VALUE}{value}{COLOR_RESET}"
            )
        print(f"{COLOR_CATEGORY}└{'─' * 38}┘{COLOR_RESET}\n")


if __name__ == "__main__":
    system_info = get_system_info()
    display_system_info(system_info)

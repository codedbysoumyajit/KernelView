import os
import platform
import psutil
import socket
import subprocess
import time
import datetime
import re

# Modern color scheme with better contrast
COLOR_HEADER = "\033[34m"  # Bright blue
COLOR_CATEGORY = "\033[34m"  # Blue
COLOR_KEY = "\033[38;5;255m"  # Bright white
COLOR_VALUE = "\033[38;5;249m"  # Light gray
COLOR_ACCENT = "\033[34m"  # Blue
COLOR_RESET = "\033[0m"

SYSTEM_NAME = platform.system()

# Helper to remove ANSI escape codes for accurate string length calculation
def _strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def _run_command(command, shell=False, suppress_errors=True):
    """Helper to run shell commands and return stripped output."""
    try:
        output = subprocess.check_output(
            command,
            shell=shell,
            stderr=subprocess.PIPE if suppress_errors else None,
            text=True,
            encoding='utf-8'
        ).strip()
        return output
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_os_info():
    """Fetches detailed OS information."""
    if SYSTEM_NAME == "Linux":
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                os_release = dict(
                    line.strip().split('=', 1) for line in f if '=' in line
                )
            pretty_name = os_release.get('PRETTY_NAME', '').strip('"')
            if pretty_name:
                return pretty_name

        if os.path.exists("/etc/lsb-release"):
            with open("/etc/lsb-release") as f:
                lsb_release = dict(
                    line.strip().split('=', 1) for line in f if '=' in line
                )
            description = lsb_release.get('DISTRIB_DESCRIPTION', '').strip('"')
            if description:
                return description
            if lsb_release.get('DISTRIB_ID') and lsb_release.get(
                    'DISTRIB_RELEASE'):
                return (
                    f"{lsb_release['DISTRIB_ID']} {lsb_release['DISTRIB_RELEASE']}"
                )

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

        return f"Linux {platform.release()}"

    elif SYSTEM_NAME == "Windows":
        version_info = platform.win32_ver()
        product_name = version_info[0]
        build_number = version_info[2]
        return f"{product_name} (Build {build_number})"

    elif SYSTEM_NAME == "Darwin":
        product_version = _run_command(["sw_vers", "-productVersion"])
        build_version = _run_command(["sw_vers", "-buildVersion"])
        return f"macOS {product_version} (Build {build_version})"
    else:
        return platform.platform()


def get_shell():
    """Detects the current shell and its version."""
    shell_path = os.environ.get('SHELL')
    if not shell_path and SYSTEM_NAME != "Windows":
        shell_path = _run_command(["ps", "-p", str(os.getppid()), "-o", "comm="])

    if shell_path:
        shell_name = os.path.basename(shell_path)
        version = ""
        if shell_name == 'bash':
            version = _run_command([shell_path, "--version"]).split('\n')[0].split(' ')[3].split('(')[0]
        elif shell_name == 'zsh':
            version = _run_command([shell_path, "--version"]).split('\n')[0].split(' ')[1]
        elif shell_name == 'fish':
            version = _run_command([shell_path, "--version"]).split('\n')[0].split(' ')[2]
        elif shell_name == 'powershell.exe':
            version = _run_command(["powershell", "-Command", "$PSVersionTable.PSVersion.ToString()"])

        display_name = {
            'bash': 'Bash', 'zsh': 'Zsh', 'fish': 'Fish', 'dash': 'Dash',
            'ksh': 'KornShell', 'tcsh': 'Tcsh', 'csh': 'Csh', 'sh': 'Bourne Shell',
            'ash': 'Almquist Shell', 'mksh': 'MirBSD KornShell', 'powershell.exe': 'PowerShell'
        }.get(shell_name, shell_name.capitalize())

        return f"{display_name} {version}".strip() if version else display_name

    if SYSTEM_NAME == "Windows":
        if 'PSModulePath' in os.environ:
            return get_shell()
        if 'MINGW' in os.environ.get('MSYSTEM', ''):
            return "Git Bash"
        if 'COMSPEC' in os.environ and 'cmd.exe' in os.environ['COMSPEC'].lower():
            return "CMD"
        if os.environ.get('WT_SESSION'):
            return "Windows Terminal"

    return "Unknown Shell"


def get_kernel_info():
    """Retrieves kernel name and version."""
    if SYSTEM_NAME == "Linux":
        return f"{_run_command('uname -s')} {_run_command('uname -r')}"
    elif SYSTEM_NAME == "Windows":
        return platform.win32_ver()[0]
    elif SYSTEM_NAME == "Darwin":
        return f"Darwin {_run_command('uname -r')}"
    return "Unknown"


def get_cpu_info():
    """Extracts detailed CPU information."""
    if SYSTEM_NAME == "Windows":
        return platform.processor()
    elif SYSTEM_NAME == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                cpuinfo = f.read()
            model_name_match = re.search(r"model name\s*:\s*(.*)", cpuinfo)
            if model_name_match:
                return model_name_match.group(1).strip()

            if "ARM" in platform.machine() or "aarch64" in platform.machine():
                implementer_match = re.search(r"CPU implementer\s*:\s*(.*)", cpuinfo)
                part_match = re.search(r"CPU part\s*:\s*(.*)", cpuinfo)

                implementer = implementer_match.group(1).strip() if implementer_match else "Unknown"
                part = part_match.group(1).strip() if part_match else "Unknown"

                implementer_map = {
                    "0x41": "ARM Ltd.", "0x61": "Apple", "0x51": "Qualcomm",
                    "0x48": "HiSilicon", "0x58": "MediaTek", "0xc0": "Google"
                }
                vendor = implementer_map.get(implementer, implementer)

                if vendor != "Unknown" or part != "Unknown":
                    return f"{vendor} ARM Processor (Part: {part})"
                else:
                    return "ARM Processor"

            return platform.machine()
        except Exception:
            return f"Unknown ({platform.machine()})"

    elif SYSTEM_NAME == "Darwin":
        if platform.machine() == "arm64":
            output = _run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
            if output:
                return output
            return f"Apple Silicon ({_run_command(['sysctl', '-n', 'hw.model'])})"
        else:
            return _run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
    return f"Unknown ({platform.machine()})"


def get_gpu_info():
    """Retrieves GPU information."""
    if SYSTEM_NAME == "Windows":
        wmic_output = _run_command("wmic path Win32_VideoController get Caption")
        lines = wmic_output.splitlines()
        if len(lines) > 1 and lines[1].strip():
            return lines[1].strip()
        return "Unknown"
    elif SYSTEM_NAME == "Linux":
        output = _run_command("lspci -v | grep -i 'VGA\\|3D\\|Display'")
        match = re.search(r'\[(.*?)\]:\s*(.*)', output)
        if match:
            return match.group(2).strip()
        return output.split(":")[-1].strip() if output else "Unknown"
    elif SYSTEM_NAME == "Darwin":
        output = _run_command("system_profiler SPDisplaysDataType | grep 'Chipset Model'")
        return output.split(": ")[-1].strip() if output else "Unknown"
    return "Unknown"


def get_vram_info():
    """Attempts to get VRAM total, used, and percentage."""
    total_vram, used_vram, free_vram, vram_usage = None, None, None, None

    output = _run_command(
        "nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader,nounits"
    )
    if output:
        try:
            total, used = map(int, output.split(','))
            total_vram = total
            used_vram = used
            free_vram = total - used
            vram_usage = (used / total) * 100 if total > 0 else 0
            return total_vram, used_vram, free_vram, round(vram_usage, 1)
        except ValueError:
            pass

    if SYSTEM_NAME == "Linux":
        output = _run_command("rocminfo | grep 'VRAM Total Memory:'")
        if output:
            match = re.search(r'(\d+)MB', output)
            if match:
                total_vram = int(match.group(1))

        try:
            drm_cards = [d for d in os.listdir('/sys/class/drm') if d.startswith('card') and 'device' in os.listdir(f'/sys/class/drm/{d}')]
            for card in drm_cards:
                vram_usage_file = f'/sys/class/drm/{card}/device/gpu_busy_percent'
                if os.path.exists(vram_usage_file):
                    with open(vram_usage_file, 'r') as f:
                        gpu_percent = int(f.read().strip())
                        return total_vram, None, None, gpu_percent if total_vram else None
        except Exception:
            pass

        output = _run_command("lspci | grep -i 'Intel Corporation.*VGA'")
        if output:
            return None, None, None, "Shared"

    if SYSTEM_NAME == "Darwin":
        output = _run_command("system_profiler SPDisplaysDataType | grep 'VRAM (Total):'")
        if output:
            match = re.search(r'(\d+)', output)
            if match:
                total_vram = int(match.group(1))
                return total_vram, None, None, None

    if SYSTEM_NAME == "Windows":
        output = _run_command("wmic path Win32_VideoController get AdapterRAM /value")
        match = re.search(r'AdapterRAM=(\d+)', output)
        if match:
            total_vram = int(match.group(1)) // (1024**2)
            return total_vram, None, None, None

    return total_vram, used_vram, free_vram, vram_usage


def get_open_ports():
    """Lists currently open TCP/UDP ports."""
    open_ports = []
    if SYSTEM_NAME == "Linux":
        output = _run_command("ss -tuln")
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                address_port = parts[4]
                if ':' in address_port:
                    port = address_port.split(':')[-1]
                    if port.isdigit():
                        open_ports.append(port)
    elif SYSTEM_NAME == "Windows":
        output = _run_command("netstat -ano")
        for line in output.splitlines():
            if "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 2:
                    local_address = parts[1]
                    if ':' in local_address:
                        port = local_address.split(':')[-1]
                        if port.isdigit():
                            open_ports.append(port)
    elif SYSTEM_NAME == "Darwin":
        output = _run_command("lsof -i -P | grep LISTEN")
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 9:
                address_port = parts[8]
                if ':' in address_port:
                    port = address_port.split(':')[-1]
                    if port.isdigit():
                        open_ports.append(port)

    unique_ports = sorted(list(set(open_ports)), key=int)
    return ", ".join(unique_ports[:5]) + ("..." if len(unique_ports) > 5 else "") if unique_ports else "None"


def get_swap_memory():
    """Retrieves swap memory details."""
    swap = psutil.swap_memory()
    total_swap = round(swap.total / (1024**3))
    used_swap = round(swap.used / (1024**3))
    free_swap = total_swap - used_swap
    swap_usage = swap.percent
    return total_swap, used_swap, free_swap, swap_usage


def get_installed_languages():
    """Checks for common programming languages."""
    languages_commands = {
        "Python": ["python3", "--version"],
        "Node.js": ["node", "--version"],
        "C": ["gcc", "--version"],
        "C++": ["g++", "--version"],
        "Go": ["go", "version"],
        "Rust": ["rustc", "--version"],
        "Java": ["java", "-version"],
        "Perl": ["perl", "--version"],
        "Ruby": ["ruby", "--version"],
        "PHP": ["php", "--version"]
    }

    installed = []
    for lang, cmd in languages_commands.items():
        if _run_command(cmd):
            installed.append(lang)
    return ", ".join(installed[:5]) + ("..." if len(installed) > 5 else "") if installed else "None"


def get_ip_address():
    """Determines the local IP address."""
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
    """Gets screen resolution."""
    if SYSTEM_NAME == "Linux":
        if "DISPLAY" in os.environ:
            output = _run_command("xrandr | grep '*'")
            if output:
                return output.splitlines()[0].split()[0]
            return "Unknown (Xorg/Wayland)"
        return "Headless"
    elif SYSTEM_NAME == "Windows":
        output = _run_command("wmic desktopmonitor get screenheight,screenwidth /value")
        height, width = "Unknown", "Unknown"
        for line in output.splitlines():
            if "ScreenHeight=" in line:
                height = line.split('=')[1].strip()
            elif "ScreenWidth=" in line:
                width = line.split('=')[1].strip()
        if height != "Unknown" and width != "Unknown":
            return f"{width}x{height}"
        return "Unknown"
    elif SYSTEM_NAME == "Darwin":
        output = _run_command("system_profiler SPDisplaysDataType | grep 'Resolution'")
        return output.split(": ")[1].strip() if output else "Unknown"
    return "Unknown"


def get_terminal():
    """Identifies the terminal emulator."""
    if SYSTEM_NAME == "Linux":
        term = os.environ.get('TERM_PROGRAM')
        if term:
            return term.replace('-', ' ').title()
        term = os.environ.get('TERM')
        if term and term != "xterm-256color":
            return term.capitalize()
        try:
            return psutil.Process(os.getppid()).name().replace('-', ' ').title()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return "Unknown"
    elif SYSTEM_NAME == "Windows":
        if os.environ.get('WT_SESSION'):
            return "Windows Terminal"
        try:
            parent_process_name = psutil.Process(os.getppid()).name().lower()
            if 'cmd.exe' in parent_process_name:
                return "CMD"
            elif 'powershell.exe' in parent_process_name:
                return "PowerShell"
            elif 'bash.exe' in parent_process_name or 'wsl.exe' in parent_process_name:
                return "WSL Bash"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return "Unknown Windows Terminal"
    elif SYSTEM_NAME == "Darwin":
        return os.environ.get('TERM_PROGRAM', 'Terminal')
    return "Unknown"


def get_window_manager():
    """Detects the window manager or display server."""
    if SYSTEM_NAME == "Linux":
        if "WAYLAND_DISPLAY" in os.environ:
            return "Wayland"
        wm_name = _run_command("wmctrl -m | grep 'Name:'")
        if wm_name:
            return wm_name.split(':')[-1].strip()
        return os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown (X11)')
    elif SYSTEM_NAME == "Windows":
        return "Windows Manager"
    elif SYSTEM_NAME == "Darwin":
        return "Aqua"
    return "Unknown"


def get_system_locale():
    """Retrieves the system's locale settings."""
    if SYSTEM_NAME == "Windows":
        return os.environ.get('LANG', 'Unknown Windows Locale')
    elif SYSTEM_NAME == "Linux" or SYSTEM_NAME == "Darwin":
        locale_output = _run_command("locale")
        lang_match = re.search(r'LANG="(.*?)"', locale_output)
        if lang_match:
            return lang_match.group(1)
        return os.environ.get('LANG', os.environ.get('LC_ALL', 'Unknown'))
    return "Unknown"


def get_desktop_environment():
    """Identifies the desktop environment."""
    if SYSTEM_NAME == "Linux":
        de = os.environ.get('XDG_CURRENT_DESKTOP')
        if de:
            return de.split(':')[-1]
        de = os.environ.get('DESKTOP_SESSION')
        if de:
            return de.replace('-', ' ').title()
        de = os.environ.get('GDMSESSION')
        if de:
            return de.replace('-', ' ').title()
        processes = _run_command("ps -e")
        if "gnome-shell" in processes:
            return "GNOME"
        elif "plasmashell" in processes:
            return "KDE Plasma"
        elif "xfce4-session" in processes:
            return "XFCE"
        elif "cinnamon-session" in processes:
            return "Cinnamon"
        return "Unknown (possibly headless)"
    elif SYSTEM_NAME == "Windows":
        return f"Windows {platform.release()}"
    elif SYSTEM_NAME == "Darwin":
        return "macOS Aqua"
    return "Unknown"


def get_package_counts():
    """Counts packages from various package managers."""
    packages = {}

    if SYSTEM_NAME == "Linux":
        if _run_command("command -v dpkg-query"):
            count = _run_command("dpkg-query -f '${binary:Package}\n' -W 2>/dev/null | wc -l")
            if count.isdigit() and int(count) > 0: packages["APT"] = int(count)
        if _run_command("command -v pacman"):
            count = _run_command("pacman -Qq 2>/dev/null | wc -l")
            if count.isdigit() and int(count) > 0: packages["Pacman"] = int(count)
        if _run_command("command -v dnf"):
            count = _run_command("dnf list installed 2>/dev/null | wc -l")
            if count.isdigit() and int(count) > 0: packages["DNF"] = int(count)
        if _run_command("command -v flatpak"):
            count = _run_command("flatpak list 2>/dev/null | wc -l")
            if count.isdigit() and int(count) > 0: packages["Flatpak"] = int(count)
        if _run_command("command -v snap"):
            count = _run_command("snap list 2>/dev/null | wc -l")
            if count.isdigit() and int(count) > 0: packages["Snap"] = int(count)

    elif SYSTEM_NAME == "Darwin":
        if _run_command("command -v brew"):
            count = _run_command("brew list 2>/dev/null | wc -l")
            if count.isdigit() and int(count) > 0: packages["Homebrew"] = int(count)
        if _run_command("command -v port"):
            count = _run_command("port installed 2>/dev/null | wc -l")
            if count.isdigit() and int(count) > 0: packages["MacPorts"] = int(count)

    elif SYSTEM_NAME == "Windows":
        if _run_command("command -v choco"):
            count = _run_command("choco list --local-only | Measure-Object | Select-Object -ExpandProperty Count", shell=True)
            if count.isdigit() and int(count) > 0: packages["Chocolatey"] = int(count)
        if _run_command("command -v winget"):
            count = _run_command("winget list | Measure-Object | Select-Object -ExpandProperty Count", shell=True)
            if count.isdigit() and int(count) > 0: packages["Winget"] = int(count)
        if _run_command("command -v scoop"):
            count = _run_command("scoop list | Measure-Object | Select-Object -ExpandProperty Count", shell=True)
            if count.isdigit() and int(count) > 0: packages["Scoop"] = int(count)

    return ", ".join([f"{k} ({v})" for k, v in packages.items()]) if packages else "None detected"


def get_system_info():
    """Gathers all system information into a dictionary."""
    total_vram, used_vram, free_vram, vram_usage = get_vram_info()
    total_swap, used_swap, free_swap, swap_usage = get_swap_memory()
    disk_usage = psutil.disk_usage('/')
    ram = psutil.virtual_memory()

    cpu_freq_info = psutil.cpu_freq()
    cpu_speed = f"{cpu_freq_info.current:.2f} MHz" if cpu_freq_info else "Unknown"

    info = {
        "OS": get_os_info(),
        "Kernel": get_kernel_info(),
        "Uptime": str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))),
        "Shell": get_shell(),
        "Python": platform.python_version(),
        "CPU": get_cpu_info(),
        "Cores/Threads": f"{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}",
        "CPU Speed": cpu_speed,
        "CPU Usage": f"{psutil.cpu_percent(interval=1)}%",
        "GPU": get_gpu_info(),
        "VRAM": (
            f"{used_vram}/{total_vram}MB ({vram_usage}%)"
            if total_vram and used_vram is not None
            else (f"{total_vram}MB (Total)" if total_vram else "Unknown")
        ),
        "RAM": f"{round(ram.used/(1024**3))}/{round(ram.total/(1024**3))}GB ({ram.percent}%)",
        "Disk": f"{round(disk_usage.used/(1024**3))}/{round(disk_usage.total/(1024**3))}GB ({disk_usage.percent}%)",
        "Swap": f"{used_swap}/{total_swap}GB ({swap_usage}%)",
        "Hostname": socket.gethostname(),
        "IP Address": get_ip_address(),
        "Open Ports": get_open_ports(),
        "Locale": get_system_locale(),
        "Resolution": get_resolution(),
        "Window Manager": get_window_manager(),
        "DE": get_desktop_environment(),
        "Terminal": get_terminal(),
        "Packages": get_package_counts(),
        "Languages": get_installed_languages(),
    }
    return info


def display_system_info(info):
    """Prints the system information to the console in a compact, text-only format."""
    os.system('cls' if os.name == 'nt' else 'clear')

    # Prepare info lines, grouped by implied categories for a cleaner look
    info_groups = [
        ("System", [
            ("OS", "OS"),
            ("Kernel", "Kernel"),
            ("Uptime", "Uptime"),
            ("Shell", "Shell"),
            ("Terminal", "Terminal"),
        ]),
        ("Hardware", [
            ("CPU", "CPU"),
            ("GPU", "GPU"),
            ("RAM", "RAM"),
            ("VRAM", "VRAM"),
        ]),
        ("Network", [
            ("Hostname", "Hostname"),
            ("IP Address", "IP Address"),
        ]),
        ("Storage", [ # Renamed from "Disk & Swap" for conciseness
            ("Disk", "Disk"),
            ("Swap", "Swap"),
        ]),
        ("Display", [
            ("Resolution", "Resolution"),
            ("DE", "DE"),
            ("WM", "Window Manager"),
        ]),
        ("Software", [
            ("Packages", "Packages"),
            ("Languages", "Languages"),
            ("Python", "Python"),
        ]),
        ("CPU Stats", [ # Separate CPU stats for readability
            ("Cores/Threads", "Cores/Threads"),
            ("Speed", "CPU Speed"),
            ("Usage", "CPU Usage"),
        ]),
        ("Other", [
            ("Locale", "Locale"),
            ("Ports", "Open Ports"),
        ])
    ]

    formatted_info_lines = []

    # Calculate max key length across all info lines for consistent alignment
    max_key_display_length = 0
    for _, group_items in info_groups:
        for key_display, _ in group_items:
            max_key_display_length = max(max_key_display_length, len(key_display))

    for category_display_name, group_items in info_groups:
        current_category_lines = []
        for key_display, info_dict_key in group_items:
            value = info.get(info_dict_key, "N/A")
            if value != "N/A":
                # Format: "Key: Value" with colors and consistent key padding
                line = f"{COLOR_KEY}{key_display.ljust(max_key_display_length)}: {COLOR_VALUE}{value}{COLOR_RESET}"
                current_category_lines.append(line)

        if current_category_lines:
            # Add category header only if there are items in the category
            formatted_info_lines.append(f"{COLOR_CATEGORY}─── {category_display_name} ───{COLOR_RESET}")
            formatted_info_lines.extend(current_category_lines)

    # Calculate max width for the info column (using _strip_ansi for accurate length)
    max_info_width = 0
    for line in formatted_info_lines:
        max_info_width = max(max_info_width, len(_strip_ansi(line)))

    # Print the header (KernelView) centered over the info section
    title_spacing = (max_info_width // 2) - (len("KernelView") // 2)

    print(f"{' ' * max(0, title_spacing)}{COLOR_ACCENT}KernelView{COLOR_RESET}\n")

    for line in formatted_info_lines:
        # Calculate padding for info part to align using _strip_ansi
        clean_info_part_len = len(_strip_ansi(line))
        info_padding = max_info_width - clean_info_part_len if max_info_width > clean_info_part_len else 0

        print(f"{line}{' ' * info_padding}")

    print("\n") # Add a final newline for spacing


if __name__ == "__main__":
    system_info = get_system_info()
    display_system_info(system_info)

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
            stderr=subprocess.DEVNULL if suppress_errors else None, # Use DEVNULL for cleaner suppression
            text=True,
            encoding='utf-8'
        ).strip()
        return output
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError): # Catch PermissionError
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
        # Using platform module for basic Windows version, more reliable than parsing wmic
        version_info = platform.win32_ver()
        product_name = version_info[0]
        build_number = version_info[2]
        # Adding build number for more detail
        return f"{product_name} (Build {build_number})"

    elif SYSTEM_NAME == "Darwin":
        product_version = _run_command(["sw_vers", "-productVersion"])
        build_version = _run_command(["sw_vers", "-buildVersion"])
        return f"macOS {product_version} (Build {build_version})"
    else:
        return platform.platform()


def get_shell():
    """Detects the current shell and its version, more reliably on Windows."""
    # Prioritize well-known environment variables
    shell_path = os.environ.get('SHELL')
    if shell_path: # Linux/macOS/WSL/Git Bash typically set this
        shell_name = os.path.basename(shell_path).lower()
        version_output = ""
        # Try to get version if common shell
        if shell_name == 'bash':
            version_output = _run_command([shell_path, "--version"])
            if version_output: return f"Bash {version_output.splitlines()[0].split(' ')[3].split('(')[0]}"
        elif shell_name == 'zsh':
            version_output = _run_command([shell_path, "--version"])
            if version_output: return f"Zsh {version_output.splitlines()[0].split(' ')[1]}"
        elif shell_name == 'fish':
            version_output = _run_command([shell_path, "--version"])
            if version_output: return f"Fish {version_output.splitlines()[0].split(' ')[2]}"

        return os.path.basename(shell_path) # Fallback to just name if version fails

    if SYSTEM_NAME == "Windows":
        # Check for well-known Windows terminals/shells via environment or direct command
        if os.environ.get('WT_SESSION'):
            return "Windows Terminal"
        if 'PSModulePath' in os.environ:
            ps_version = _run_command(["powershell.exe", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"])
            return f"PowerShell {ps_version}" if ps_version else "PowerShell"
        if 'MINGW' in os.environ.get('MSYSTEM', ''):
            return "Git Bash"
        if 'ComSpec' in os.environ: # Default CMD path
            if 'cmd.exe' in os.environ['ComSpec'].lower():
                return "CMD"

        # Last resort: try to get parent process name
        try:
            parent_process = psutil.Process(os.getppid()).name().lower()
            if 'cmd.exe' in parent_process:
                return "CMD"
            elif 'powershell.exe' in parent_process:
                return "PowerShell"
            elif 'bash.exe' in parent_process: # Could be WSL or Git Bash
                return "Bash"
            elif 'explorer.exe' in parent_process: # Could be graphical launcher
                return "Windows Explorer (Parent)" # Or just "Windows Shell"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass # Silently ignore if process info is not accessible

    return "Unknown Shell"


def get_kernel_info():
    """Retrieves kernel name and version."""
    if SYSTEM_NAME == "Linux":
        kernel_name = _run_command("uname -s", shell=True)
        kernel_version = _run_command("uname -r", shell=True)
        return f"{kernel_name} {kernel_version}"
    elif SYSTEM_NAME == "Windows":
        # platform.win32_ver()[0] is product name, not kernel.
        # Use subprocess to get actual kernel version.
        try:
            kernel_version = _run_command("powershell.exe -NoProfile -Command \"(Get-CimInstance Win32_OperatingSystem).Version\"")
            return f"Windows NT {kernel_version}" if kernel_version else "Windows NT Kernel"
        except Exception:
            return "Windows NT Kernel" # Fallback
    elif SYSTEM_NAME == "Darwin":
        kernel_name = "Darwin"
        kernel_version = _run_command("uname -r", shell=True)
        return f"{kernel_name} {kernel_version}"
    return "Unknown"


def get_cpu_info():
    """Extracts detailed CPU information."""
    if SYSTEM_NAME == "Windows":
        # platform.processor() is quite reliable on Windows for the human-readable name
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


def get_cpu_speed():
    """Fetches current CPU frequency, gracefully handling permissions."""
    try:
        if SYSTEM_NAME == "Linux":
            # Try dynamic frequency from sysfs (may require root, handle PermissionError)
            try:
                with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
                    freq_khz = float(f.read().strip())
                    return f"{freq_khz / 1000:.2f} MHz"
            except (FileNotFoundError, PermissionError):
                # Fallback to nominal frequency from /proc/cpuinfo
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "cpu MHz" in line:
                            return f"{float(line.split(':')[1].strip()):.2f} MHz"
            return "Unknown"
        elif SYSTEM_NAME == "Windows":
            # Use PowerShell to get current clock speed
            output = _run_command("powershell.exe -NoProfile -Command \"(Get-CimInstance Win32_Processor).CurrentClockSpeed\"")
            return f"{output} MHz" if output else "Unknown"
        elif SYSTEM_NAME == "Darwin":
            # Use sysctl for CPU frequency (in Hz)
            output = _run_command(["sysctl", "-n", "hw.cpufrequency"])
            if output:
                freq_hz = float(output)
                return f"{freq_hz / 1e9:.2f} GHz"
            return "Unknown"
        return "Unknown"
    except Exception:
        return "Unknown"


def get_cpu_usage():
    """Fetches CPU usage percentage."""
    # psutil.cpu_percent with interval is reliable and platform-agnostic
    try:
        return f"{psutil.cpu_percent(interval=1)}%"
    except Exception:
        return "N/A" # Cannot get dynamic CPU usage


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

    # Try NVIDIA first (common across OSes if nvidia-smi is in PATH)
    output = _run_command(
        "nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits"
    )
    if output:
        try:
            total_str, used_str, free_str = output.split(',')
            total_vram = int(total_str.strip())
            used_vram = int(used_str.strip())
            free_vram = int(free_str.strip())
            if total_vram > 0:
                vram_usage = (used_vram / total_vram) * 100
                return total_vram, used_vram, free_vram, round(vram_usage, 1)
        except (ValueError, IndexError):
            pass # Continue to other methods

    if SYSTEM_NAME == "Linux":
        # AMD via rocminfo (for total VRAM)
        output = _run_command("rocminfo")
        match = re.search(r'VRAM Total Memory:\s*(\d+)MB', output)
        if match:
            total_vram = int(match.group(1))
            return total_vram, None, None, None # Usage is hard without specific tools

        # Intel GPUs often use shared memory
        if "Intel" in get_gpu_info():
            return None, None, None, "Shared" # Indicate shared memory

    elif SYSTEM_NAME == "Windows":
        # WMIC for AdapterRAM (total VRAM)
        output = _run_command("wmic path Win32_VideoController get AdapterRAM /value")
        match = re.search(r'AdapterRAM=(\d+)', output)
        if match:
            total_vram = int(match.group(1)) // (1024**2) # Convert bytes to MB
            return total_vram, None, None, None # Windows doesn't provide used VRAM easily via WMI/CMD

    elif SYSTEM_NAME == "Darwin":
        output = _run_command("system_profiler SPDisplaysDataType | grep 'VRAM (Total):'")
        match = re.search(r'VRAM \(Total\):\s*(\d+)', output)
        if match:
            total_vram = int(match.group(1))
            return total_vram, None, None, None

    return total_vram, used_vram, free_vram, vram_usage # Return all Nones/Unknown if nothing found


def get_open_ports():
    """Lists currently open TCP/UDP ports."""
    open_ports = []
    try:
        if SYSTEM_NAME == "Linux":
            # Prefer 'ss' for speed and modern systems, fallback to netstat
            output = _run_command("ss -tulnp")
            if not output:
                output = _run_command("netstat -tulnp") # Older/less common fallback

            for line in output.splitlines():
                parts = line.split()
                # ss output: Netid State Recv-Q Send-Q Local-Address:Port Peer-Address:Port Process
                # netstat output: Proto Recv-Q Send-Q Local Address Foreign Address State PID/Program name
                if "LISTEN" in line:
                    if len(parts) > 4: # ss output
                         addr_port = parts[4]
                    elif len(parts) > 3: # netstat output
                        addr_port = parts[3]
                    else:
                        continue # Skip malformed lines

                    if ':' in addr_port:
                        port = addr_port.split(":")[-1]
                        if port.isdigit():
                            open_ports.append(port)
        elif SYSTEM_NAME == "Windows":
            # Using netstat -ano which is common on Windows
            output = _run_command("netstat -ano")
            for line in output.splitlines():
                if "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 2: # Check if local address is present
                        local_address = parts[1]
                        if ':' in local_address:
                            port = local_address.split(':')[-1]
                            if port.isdigit():
                                open_ports.append(port)
        elif SYSTEM_NAME == "Darwin":
            # lsof is preferred on macOS
            output = _run_command("lsof -i -P | grep LISTEN")
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 9:
                    address_port = parts[8]
                    if ':' in address_port:
                        port = address_port.split(':')[-1]
                        if port.isdigit():
                            open_ports.append(port)
                    # Handle IPv6 format like [::]:port if needed, though simpler regex might cover
                    elif '->:' in address_port: # Example for IPv6 from lsof output
                        match = re.search(r':(\d+)\s*\(LISTEN\)', address_port)
                        if match:
                            port = match.group(1)
                            if port.isdigit():
                                open_ports.append(port)
    except Exception:
        return "Unknown" # Catch any unforeseen errors

    # Filter for unique ports and limit to 5 for brevity
    unique_ports = sorted(list(set(open_ports)), key=int)
    return ", ".join(unique_ports[:5]) + ("..." if len(unique_ports) > 5 else "") if unique_ports else "None"


def get_swap_memory():
    """Retrieves swap memory details."""
    try:
        swap = psutil.swap_memory()
        total_swap = round(swap.total / (1024**3))
        used_swap = round(swap.used / (1024**3))
        free_swap = total_swap - used_swap # Directly calculate free swap
        swap_usage = swap.percent
        return total_swap, used_swap, free_swap, swap_usage
    except Exception:
        return 0, 0, 0, 0  # Return zeros if swap info not available


def get_installed_languages():
    """Checks for common programming languages."""
    languages_commands = {
        "Python": ["python3", "--version"], # Prefer python3
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
        # Ensure command is run without shell=True if it's a list for security/portability
        # And specifically handle java -version which prints to stderr
        try:
            if lang == "Java":
                # Java -version prints to stderr, so we need to capture stderr
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            else:
                output = _run_command(cmd)

            if output: # Check if command executed successfully and returned anything
                installed.append(lang)
        except Exception:
            continue
    return ", ".join(installed[:5]) + ("..." if len(installed) > 5 else "") if installed else "None"


def get_ip_address():
    """Determines the local IP address."""
    try:
        # Try connecting to an external server (Google's DNS) to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to hostname resolution if direct connection fails
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "Unknown"


def get_resolution():
    """Gets screen resolution."""
    try:
        if SYSTEM_NAME == "Linux":
            if "DISPLAY" in os.environ:
                output = _run_command("xrandr | grep '*'")
                if output:
                    # xrandr output often contains multiple resolutions for connected displays
                    # We'll just take the first one or primary if available.
                    primary_match = re.search(r'(\d+x\d+)\s*(?=\s+\S+\s+primary)', output)
                    if primary_match:
                        return primary_match.group(1)

                    # Fallback to first resolution if primary not found
                    first_res_match = re.search(r'(\d+x\d+)', output)
                    if first_res_match:
                        return first_res_match.group(1)
                return "Unknown (Xorg/Wayland)"
            return "Headless"
        elif SYSTEM_NAME == "Windows":
            # Use PowerShell for reliable resolution
            output = _run_command("powershell.exe -NoProfile -Command \"Get-WmiObject Win32_VideoController | Select-Object CurrentHorizontalResolution,CurrentVerticalResolution | Format-List\"")
            width_match = re.search(r'CurrentHorizontalResolution\s*:\s*(\d+)', output)
            height_match = re.search(r'CurrentVerticalResolution\s*:\s*(\d+)', output)
            if width_match and height_match:
                return f"{width_match.group(1)}x{height_match.group(1)}"
            return "Unknown"
        elif SYSTEM_NAME == "Darwin":
            output = _run_command("system_profiler SPDisplaysDataType | grep 'Resolution'")
            if output:
                return output.split(": ")[1].strip()
            return "Unknown"
        return "Unknown"
    except Exception:
        return "Unknown"


def get_terminal():
    """Identifies the terminal emulator."""
    try:
        if SYSTEM_NAME == "Linux":
            term_program = os.environ.get('TERM_PROGRAM')
            if term_program:
                return term_program.replace('-', ' ').title()
            term = os.environ.get('TERM')
            if term and term != "xterm-256color":
                return term.capitalize()

            # Fallback to parent process name
            try:
                parent_process_name = psutil.Process(os.getppid()).name().lower()
                # Common terminal processes
                if "gnome-terminal" in parent_process_name: return "Gnome Terminal"
                if "konsole" in parent_process_name: return "Konsole"
                if "xterm" in parent_process_name: return "Xterm"
                if "alacritty" in parent_process_name: return "Alacritty"
                if "kitty" in parent_process_name: return "Kitty"
                if "terminator" in parent_process_name: return "Terminator"
                if "urxvt" in parent_process_name: return "URxvt"
                return parent_process_name.replace('-', ' ').title() # Generic
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            return "Unknown"
        elif SYSTEM_NAME == "Windows":
            if os.environ.get('WT_SESSION'):
                return "Windows Terminal"
            # Try to get parent process name for CMD/PowerShell if WT_SESSION not set
            try:
                parent_process_name = psutil.Process(os.getppid()).name().lower()
                if 'cmd.exe' in parent_process_name:
                    return "CMD"
                elif 'powershell.exe' in parent_process_name:
                    return "PowerShell"
                elif 'bash.exe' in parent_process_name or 'wsl.exe' in parent_process_name:
                    return "WSL Bash" # More specific than just "Bash"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            return "Unknown Windows Terminal"
        elif SYSTEM_NAME == "Darwin":
            return os.environ.get('TERM_PROGRAM', 'Terminal') # Usually "Terminal.app" or "iTerm.app"
        return "Unknown"
    except Exception:
        return "Unknown"


def get_window_manager():
    """Detects the window manager or display server."""
    try:
        if SYSTEM_NAME == "Linux":
            if "WAYLAND_DISPLAY" in os.environ:
                return "Wayland"
            # Try wmctrl for X11 Window Manager (requires wmctrl package)
            wm_name = _run_command("wmctrl -m | grep 'Name:'", shell=True)
            if wm_name:
                return wm_name.split(':')[-1].strip()
            # Fallback to XDG_CURRENT_DESKTOP for Desktop Environment (often the WM for integrated DEs)
            return os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown (X11)')
        elif SYSTEM_NAME == "Windows":
            return "Windows Manager (DWM)" # Default Windows Desktop Window Manager
        elif SYSTEM_NAME == "Darwin":
            return "Aqua" # macOS's native display framework
        return "Unknown"
    except Exception:
        return "Unknown"


def get_system_locale():
    """Retrieves the system's locale settings."""
    try:
        if SYSTEM_NAME == "Windows":
            # PowerShell for current UI culture name
            output = _run_command("powershell.exe -NoProfile -Command \"(Get-Culture).Name\"")
            return output if output else os.environ.get('LANG', 'Unknown Windows Locale')
        elif SYSTEM_NAME == "Linux" or SYSTEM_NAME == "Darwin":
            # Try locale command first
            locale_output = _run_command("locale", shell=True)
            lang_match = re.search(r'LANG="(.*?)"', locale_output)
            if lang_match:
                return lang_match.group(1)
            # Fallback to environment variables
            return os.environ.get('LANG', os.environ.get('LC_ALL', 'Unknown'))
        return os.environ.get('LANG', 'Unknown')
    except Exception:
        return "Unknown"


def get_desktop_environment():
    """Identifies the desktop environment."""
    try:
        if SYSTEM_NAME == "Linux":
            # XDG_CURRENT_DESKTOP is the most reliable
            de = os.environ.get('XDG_CURRENT_DESKTOP', '')
            if de:
                # Handle cases like "ubuntu:GNOME"
                return de.split(':')[-1]
            # Fallback to DESKTOP_SESSION or GDMSESSION
            de = os.environ.get('DESKTOP_SESSION', '')
            if de:
                return de.replace('-', ' ').title()
            de = os.environ.get('GDMSESSION', '')
            if de:
                return de.replace('-', ' ').title()

            # Check for Wayland specific environment variable
            if "WAYLAND_DISPLAY" in os.environ:
                return "Wayland"

            # Check for common DE processes (less reliable, but a fallback)
            processes = _run_command("ps -e", shell=True)
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
            return "Unknown (possibly headless)"
        elif SYSTEM_NAME == "Windows":
            # Windows doesn't have "desktop environments" in the Linux sense.
            # We can report the Windows version.
            return f"Windows {platform.release()}"
        elif SYSTEM_NAME == "Darwin":
            return "macOS Aqua"
        return "Unknown"
    except Exception:
        return "Unknown"


def get_package_counts():
    """Counts packages from various package managers."""
    packages = {}
    try:
        if SYSTEM_NAME == "Linux":
            # APT (Debian/Ubuntu)
            if _run_command("command -v dpkg-query"):
                try: packages["APT"] = int(_run_command("dpkg-query -f '${binary:Package}\n' -W 2>/dev/null | wc -l", shell=True))
                except ValueError: pass
            # Pacman (Arch)
            if _run_command("command -v pacman"):
                try: packages["Pacman"] = int(_run_command("pacman -Qq 2>/dev/null | wc -l", shell=True))
                except ValueError: pass
            # DNF (Fedora)
            if _run_command("command -v dnf"):
                try: packages["DNF"] = int(_run_command("dnf list installed --quiet 2>/dev/null | wc -l", shell=True))
                except ValueError: pass
            # Flatpak
            if _run_command("command -v flatpak"):
                try: packages["Flatpak"] = int(_run_command("flatpak list --columns=application | wc -l", shell=True))
                except ValueError: pass
            # Snap
            if _run_command("command -v snap"):
                try: packages["Snap"] = int(_run_command("snap list | wc -l", shell=True)) # Excludes header
                except ValueError: pass

        elif SYSTEM_NAME == "Darwin":
            # Homebrew
            if _run_command("command -v brew"):
                try: packages["Homebrew"] = int(_run_command("brew list --formula | wc -l", shell=True))
                except ValueError: pass
                try: packages["Homebrew Cask"] = int(_run_command("brew list --cask | wc -l", shell=True))
                except ValueError: pass
            # MacPorts
            if _run_command("command -v port"):
                try: packages["MacPorts"] = int(_run_command("port installed | wc -l", shell=True))
                except ValueError: pass

        elif SYSTEM_NAME == "Windows":
            # Chocolatey
            if _run_command("where choco", shell=True): # Check if choco is in PATH
                try: packages["Chocolatey"] = int(_run_command("powershell.exe -NoProfile -Command \"(choco list --local-only | Measure-Object | Select-Object -ExpandProperty Count)\"", shell=True))
                except ValueError: pass
            # Winget
            if _run_command("where winget", shell=True):
                try: packages["Winget"] = int(_run_command("powershell.exe -NoProfile -Command \"(winget list --query '' | Measure-Object | Select-Object -ExpandProperty Count)\"", shell=True)) # --query '' to get all packages
                except ValueError: pass
            # Scoop
            if _run_command("where scoop", shell=True):
                try: packages["Scoop"] = int(_run_command("powershell.exe -NoProfile -Command \"(scoop list | Measure-Object | Select-Object -ExpandProperty Count)\"", shell=True))
                except ValueError: pass
    except Exception:
        return "Unknown" # Catch broad errors in package counting

    if packages:
        return ", ".join([f"{k} ({v})" for k, v in packages.items()])
    return "None detected"


def get_system_info():
    """Gathers all system information into a dictionary."""
    total_vram, used_vram, free_vram, vram_usage = get_vram_info()
    total_swap, used_swap, free_swap, swap_usage = get_swap_memory()
    disk_usage = psutil.disk_usage('/')
    ram = psutil.virtual_memory()

    info = {
        "OS": get_os_info(),
        "Kernel": get_kernel_info(),
        "Uptime": str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))),
        "Shell": get_shell(),
        "Python": platform.python_version(), # Still showing Python version for Python tool
        "CPU": get_cpu_info(),
        "Cores/Threads": f"{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}",
        "CPU Speed": get_cpu_speed(), # Use dedicated function
        "CPU Usage": get_cpu_usage(), # Use dedicated function
        "GPU": get_gpu_info(),
        "VRAM": (
            f"{used_vram}/{total_vram}MB ({vram_usage}%)"
            if total_vram and used_vram is not None
            else (f"{total_vram}MB (Total)" if total_vram else (vram_usage if isinstance(vram_usage, str) else "Unknown"))
        ),
        "RAM": f"{round(ram.used/(1024**3))}GB/{round(ram.total/(1024**3))}GB ({ram.percent}%)",
        "Disk": f"{round(disk_usage.used/(1024**3))}GB/{round(disk_usage.total/(1024**3))}GB ({disk_usage.percent}%)",
        "Swap": f"{used_swap}GB/{total_swap}GB ({swap_usage}%)",
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
        ("Storage", [
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
        ("CPU Stats", [
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
            # Only consider keys that will actually have a value to be displayed
            # (check against info dictionary before using for length calculation)
            if info.get(group_items[group_items.index((key_display, _))][1], "N/A") != "N/A":
                max_key_display_length = max(max_key_display_length, len(key_display))

    for category_display_name, group_items in info_groups:
        current_category_lines = []
        for key_display, info_dict_key in group_items:
            value = info.get(info_dict_key, "N/A")
            if value not in ["N/A", "Unknown", "None", "0GB/0GB (0.0%)", "0/0GB (0.0%)", "Not installed", "Shared"]: # Filter out "N/A" etc. or empty strings
                # Refine filtering for VRAM specifically to always show if it's "Shared"
                if info_dict_key == "VRAM" and value == "Shared":
                     line = f"{COLOR_KEY}{key_display.ljust(max_key_display_length)}: {COLOR_VALUE}{value}{COLOR_RESET}"
                     current_category_lines.append(line)
                elif value and value not in ["N/A", "Unknown", "None", "0GB/0GB (0.0%)", "0/0GB (0.0%)", "Not installed"]:
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

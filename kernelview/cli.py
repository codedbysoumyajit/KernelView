#!/usr/bin/env python3
# kernelview/cli.py
from .core import get_system_info, display_system_info

def main():
    system_info = get_system_info()
    display_system_info(system_info)

if __name__ == "__main__":
    main()
# KernelView

KernelView is a modern and powerful system information tool built in Python. It provides detailed insights into your system's hardware and software, including CPU, GPU, RAM, OS, and more.

## Features
- **Comprehensive CPU Details**: Model, architecture, core count, clock speed, and temperature.
- **Detailed GPU Insights**: Graphics card model, VRAM usage, and CUDA version.
- **Memory Management**: Total and used RAM and swap memory statistics.
- **Storage Information**: Total, used, and free disk space breakdown.
- **OS and System Details**: OS name, version, and kernel details.
- **Network Monitoring**: Hostname, IP address, and open ports discovery.
- **Programming Language Detection**: Identifies installed languages like Python, Java, C++, Rust, and more.
- **Graphics Frameworks Support**: Detects Vulkan, OpenGL, and DirectX availability.

## Installation
### Install directly from GitHub
```sh
pip install git+https://github.com/Pheonix14/kernelview.git
```

### Run it
```sh
kernelview
```

### Coming Soon
KernelView will soon be available via PyPI for easy installation:
```sh
pip install kernelview
```

## Dependencies
KernelView relies on the following libraries for its functionality:
- `psutil` - System metrics (CPU, RAM, disk usage, etc.)
- `platform` - OS and architecture details
- `subprocess` - Execution of system commands
- `socket` - Network-related information retrieval

## License
KernelView is released under the MIT License, allowing free use and modification.

## Contributing
Contributions are welcome! If you’d like to improve KernelView, feel free to fork the repository, submit issues, or open pull requests on GitHub.

## Contact
For support or inquiries, reach out via [GitHub Issues](https://github.com/Pheonix14/kernelview).


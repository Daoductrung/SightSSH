# SightSSH

**SightSSH** is an accessible, 2-in-1 SSH client and SFTP manager designed for convenience and ease of use.

## About the Project

I am **Đào Đức Trung** (ddt.one). I manage servers frequently and often need to switch between running commands via SSH and uploading files via SFTP. I created this tool primarily for my own personal use to have an interface that is streamlined, accessible, and works exactly the way I want it to.

I am not a professional developer; I built this software in collaboration with **Google DeepMind's Antigravity** AI assistant.

## Why Open Source?

This software is designed to run completely offline and locally on your machine. I decided to open-source the code so that:
1.  **Trust**: You can verify the code yourself to ensure it is secure and truly private.
2.  **Sharing**: Anyone who finds this tool useful or interesting is welcome to use it.

## Features

- **2-in-1 Workflow**: Seamlessly switch between Terminal and SFTP file management in one window.
- **Accessibility First**: Optimized for screen readers (NVDA, JAWS) with dedicated input modes and clean output.
- **Profile Management**: Securely encrypted storage for your server credentials.
- **SFTP Tools**:
  - Dual-pane file manager (Local/Remote).
  - Quick actions: Rename (`F2`), Delete (`Delete`), Recursive Permissions (`Properties`).
  - Resume functionality: Remembers your last used directories.
- **Privacy**: No telemetry, no cloud syncing. Your data stays on your device.

## Installation

### Prerequisites

- Python 3.8+
- [NVDA](https://www.nvaccess.org/) (Recommended for screen reader users)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/trung-k49/SightSSH.git
   cd SightSSH
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python -m sightssh.main
   ```

## Contributing

Since this is a personal project, I maintain it as I have time. However, contributions are welcome! If you find a bug or want to improve the code, feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Credits

- **Concept & Testing**: Đào Đức Trung
- **AI Co-Developer**: Antigravity (Google DeepMind)
- **Libraries**: `wxPython` (GUI), `paramiko` (SSH/SFTP), `cryptography`.

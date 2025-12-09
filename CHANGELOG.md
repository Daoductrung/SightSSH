# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - In Development
### added
- **Stability**: Fixed application crash when saving settings by implementing persistent dialog (Singleton pattern) and safe focus transfer.
- **Stability**: Fixed application exit lag by properly cleaning up hidden dialogs.
- **Accessibility**: Implemented "Dynamic Columns" in SFTP - disabling columns in settings now physically removes them, ensuring screen readers do not announce unwanted information.
- **Settings UI**: Complete redesign with tabs for General, Terminal, and Accessibility.
- **SFTP Permissions**: View and modify remote file permissions (chmod) with recursive support.
- **SFTP Persistence**: Option to restore last used local and remote directories on reconnect.
- **Internationalization**: Full English and Vietnamese language support.
- **Security**: Profile passwords and configuration encryption.
- SSH client wrapper using `paramiko`.
- Basic UI with Create/View Profile and Connect flow.
- Custom storage path: `AppData\Roaming\ddt.one\sightssh`.

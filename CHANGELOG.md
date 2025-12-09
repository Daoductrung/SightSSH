# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-12-10
### Added
- **Update Checker**: Automatically checks for new versions from GitHub on startup.
- **Update Dialog**: Notifies user of new versions and changelogs, with a direct link to the download page.
- **Settings**: Option to enable/disable startup update checks.
- **Accessibility**: Implemented "Dynamic Columns" in SFTP - disabling columns in settings now physically removes them, ensuring screen readers do not announce unwanted information.
- **Settings UI**: Complete redesign with tabs for General, Terminal, and Accessibility.
- **SFTP Permissions**: View and modify remote file permissions (chmod) with recursive support.
- **SFTP Persistence**: Option to restore last used local and remote directories on reconnect.
- **Internationalization**: Full English and Vietnamese language support.
- **Security**: Profile passwords and configuration encryption.
- SSH client wrapper using `paramiko`.
- Basic UI with Create/View Profile and Connect flow.
- Custom storage path: `AppData\Roaming\ddt.one\sightssh`.

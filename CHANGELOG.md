# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2]
- Fixed SFTP: Corrected "Permissions" column display and resolved 'math'/'datetime' errors.
- Fixed SFTP: Resolved crash when disconnecting while panel is active.
- Fixed App: Resolved crash/lag on exit by optimizing shutdown process.
- Improved: SSH connection is now non-blocking (runs in background), preventing UI freeze.
- Improved: Added "Connection Timeout" and "Confirm Disconnect" settings.
- Improved: Removed file locking on `app_error.log` to allow easier log cleanup.

## [1.0.1]
- Fixed critical crash when connecting to SSH (duplicate passphrase argument).
- Fixed Critical Error (RuntimeError) when disconnecting from SFTP/Terminal.
- Added 'Connection Timeout' setting in Terminal preferences.
- Improved application stability and resource cleanup.

## [1.0.0]
First release.
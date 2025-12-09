import PyInstaller.__main__
import os
import shutil

def build():
    # Cleanup
    if os.path.exists('dist'): shutil.rmtree('dist')
    if os.path.exists('build'): shutil.rmtree('build')

    # Define separator
    sep = ';' if os.name == 'nt' else ':'

    # Arguments
    # sightssh/assets -> sightssh/assets inside the bundle
    add_data = f'sightssh/assets{sep}sightssh/assets'

    args = [
        'sightssh/main.py',           # Script to run
        '--name=SightSSH',            # Executable name
        '--noconsole',                # No console window (GUI app)
        '--onefile',                  # Single executable file
        '--clean',                    # Clean cache
        f'--add-data={add_data}',     # Include assets
        '--collect-all=sightssh',     # Collect everything from our package
        # Hidden imports often needed for paramiko/cffi based libs if not auto-detected
        '--hidden-import=wx',
        '--hidden-import=paramiko',
        '--hidden-import=cryptography',
    ]

    print("Building SightSSH...")
    PyInstaller.__main__.run(args)
    print("Build complete. Check 'dist' folder.")

if __name__ == "__main__":
    build()

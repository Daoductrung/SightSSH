
import sys
import traceback
import os
import time

sys.path.insert(0, os.getcwd())
print("DEBUG: Script started", flush=True)

try:
    print("DEBUG: Importing main", flush=True)
    from sightssh.main import main
    print("DEBUG: Running main()", flush=True)
    main()
    print("DEBUG: main() returned", flush=True)
except Exception:
    print("DEBUG: Exception caught", flush=True)
    traceback.print_exc()

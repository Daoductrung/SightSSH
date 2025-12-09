
import sys
import traceback
import os

sys.path.insert(0, os.getcwd())

with open("status.txt", "w") as f:
    f.write("STARTING\n")

try:
    from sightssh.main import main
    with open("status.txt", "a") as f:
        f.write("IMPORTED\n")
    main()
    with open("status.txt", "a") as f:
        f.write("FINISHED\n")
except Exception:
    with open("crash.log", "w") as f:
        f.write(traceback.format_exc())
    sys.exit(1)

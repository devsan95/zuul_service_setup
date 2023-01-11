# Python script to beautify code as per pep 8 guidelines
import subprocess
from pathlib import Path

parent_folder = r"C:\\Users\\vagga\\OneDrive - Nokia\\Zuul_service_setup_script"
pathlist = Path(parent_folder).rglob('*.py')
for path in pathlist:
    path_in_str = str(path)  # because path is object not string
    print(path_in_str)
    subprocess.run(["autopep8",     # Applying autopep8 on file
                    "--in-place",
                    "--aggressive",
                    "--aggressive",
                    path_in_str])
    subprocess.run(["isort", path_in_str])  # Applying isort on file

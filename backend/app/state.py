import os

current_directory: str = os.getcwd()
current_shell: str = "powershell" if os.name == "nt" else "bash"

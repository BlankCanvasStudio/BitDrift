import os, pwd

def expanduser(path):
    user = os.getenv("SUDO_USER") or os.getenv("USER")
    home = pwd.getpwnam(user).pw_dir
    return path.replace("~", home, 1)



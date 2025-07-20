"""
image_gen.py is the image generation payload.  It creates images and stores
them in a directory, then readies them for transfer.
"""
import os, glob
from vehicle.payloads import payload:


def expanduser(path):
    user = os.getenv("SUDO_USER") or os.getenv("USER")
    home = pwd.getpwnam(user).pw_dir
    return path.replace("~", home, 1)


class ImagePayload(payload.Payload):
    def create_image(self):
        # Create a name file based on a root and the time.
        
        image_name = ''
        
    def execute(self):
        return

    def __init__(self, img_dir, timer):
        self.dir = expanduser(img_dir)
        
        

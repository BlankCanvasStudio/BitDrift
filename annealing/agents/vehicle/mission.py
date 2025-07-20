# mission.py
#
# REI mission module
# The mission module generates a small system which calls imagemagick at fixed intervals
#
import os, pwd
import logging
from modules import util


def expanduser(path):
    user = os.getenv("SUDO_USER") or os.getenv("USER")
    home = pwd.getpwnam(user).pw_dir
    return path.replace("~", home, 1)


class Mission:
    """
    Mission class

    This defines a mission object, which contains configuration information for executing a
    time-based message at fixed intervals.

    Commands:
    init (frequency, working directory): constructor
    set_base (base_text): sets the base text for the image, which will have time and image id appended
    """
    def set_base(self, base_text):
        self.base_text = base_text

    def execute(self, current_time):
        """
        execute (time) -- > generates an image in the working directory
        Generates and writes an image to the working directory.  The image is in the form
        img_[epithet]_[id].png

        id is the id, recorded as a zero-packed 8 digit decimal string

        epithet is an 8-character epithet which implicitly defaults to the first
        8 characters of the vehicle ID and has x padding

        time is the time down to 100 microsecond precision
        """
        # This is an exit statement; if the time since last execution
        # is less than the interval, then don't execute the command.
        if current_time - self.last_time <= self.interval: return
        self.last_time = current_time
        logging.info('Executing image generation')
        fn_tmpl = 'img_{:x<8}_{:0>8}.png'
        fn = os.path.join(self.dir,
                          fn_tmpl.format(self.epithet[0:8], self.count))        
        caption = self.base_text + " {} c:{} t:{:.4f}".format(
            self.epithet, self.count, current_time)        
        cmd = self.cmd_tmpl.format(caption, fn)
        if not self.dry_run:
            os.system(cmd)
        self.count += 1
        print(cmd)
        
    def __init__ (self, dry_run, epithet, working_directory, interval):
        self.count = 0
        self.last_time = 0
        self.dry_run = dry_run
        self.interval = interval
        self.epithet = epithet
        self.dir = expanduser(working_directory)
        self.cmd_tmpl = 'magick -gravity center -background black -fill ' +\
            'white -size 640x480 caption:"{}" {}'
        self.base_text = "Basic text"
        logging.info(
            'Mission payload created with epithet {} and interval {}'.format(
                epithet, interval))
        

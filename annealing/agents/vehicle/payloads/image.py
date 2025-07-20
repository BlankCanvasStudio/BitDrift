"""
image_gen.py is the image generation payload.  It creates images and stores
them in a directory, then readies them for transfer.
"""
import os, glob, random, string, logging, sys
from vehicle.payloads import payload

class ImagePayload(payload.Payload):

    def __init__(self, img_dir, areas, log, clock, imglen = 1024):
        """
        __init__
        Payload constructor.  Takes:
        img_dir (string specifying directory): directory to store image files
        areas (array of strings): list of area names to use when generating images
        clock (vehicle.Clock object): timer to provide relative times.
        """
        logging.debug('Creating new image generator')

        # We should have checks on this
        self.log = log
        self.area_index = 0
        self.areas = areas
        self.dir = os.path.expanduser(img_dir)
        self.clock = clock
        self.imglen = imglen


        logging.debug('Directory maintenance')
        if not os.path.exists(self.dir):
            logging.debug('Directory does not exist, creating...')
            os.mkdir(self.dir)

        fset = glob.glob(os.path.join(self.dir, '*.image'))
        if len(fset) > 0:
            logging.debug(f'{len(fset)} Files in directory, removing')
            for i in fset:
                os.unlink(i)


    def create_image(self):
        # Create a name file based on a root and the time.
        time = self.clock.get_time()

        # We will predictably increment through areas.
        area_name = self.areas[self.area_index % len(self.areas)]

        time_offset = int(time)
        image_name = f'{area_name}.{str(time_offset)}.image'

        image_fn = os.path.join(self.dir, image_name)
        image_fh = open(image_fn, 'w')

        with open(image_fn, 'w') as image_fh:
            # Write a 1024 character string of hexadecimal digits
            hds = ''.join(random.choices(string.hexdigits, k = self.imglen))
            image_fh.write(hds)

        return image_name


    def get_full_path(self, img_name):
        result = os.path.join(self.dir, img_name)

        if not os.path.exists(result):
            return None # Return on file not found error.

        return result
        

    def find_image(self, img_spec):
        result = [os.path.basename(i) for i in glob.glob(os.path.join(self.dir, img_spec))]
        return result


    def execute(self):
        self.create_image()
        return


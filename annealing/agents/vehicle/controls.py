# controls.py
#
# This is the general interface for implementing
# controls on the vehicle.  Controls are managed in a
# a separate controls.yaml file and follow the format:
# control name
#
import logging
class Control:
    def startup(self):
        logging.info("Control %s started" % self.name)
    def shutdown(self):
        logging.info("Control %s ended" % self.name)
    def activate(self):
        logging.info("Control %s activated" % self.name)
    def __init__(self, name):
        self.name = name

class TimeoutControl(Control):
    """
    The timeout control defines the maximum timeout for
    any network connection
    """
    def startup(self):
        logging.info("control:{} Creating timeout control with a {} second duration".format(self.name, self.timeout))

    def shutdown(self):
        logging.info("control:{} Nothing of note, assuming image ending".format(self.name))
        
    def __init__(self, args):
        self.name = 'Timeout'
        self.timeout = args['len']

def create_control(cname, args):
    if cname in control_table:
        logging.debug("Creating control {}".format(cname))
        result = control_table[cname](args)
    else:
        logging.warn("Control {} doesn't exist in the control table".format(cname))
    return result

def create_all_controls(ctable):
    result = []
    for cname, args in ctable:
        result.append(create_control(cname, args))
    return result

control_table = {
    'timeout': TimeoutControl
}

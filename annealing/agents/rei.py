#!/usr/bin/env python3

# The REI agent
#
# The REI Agent is an application which manages attacks, defenses,
# communications, etc
#

# Generic modules go here
import argparse, os, sys, time, yaml, logging, queue, random
import threading
from multiprocessing.connection import Listener
# Agent specific modules go here
from modules import command, attack, util

# from vehicle import orbit, power, controls, mission, clock
from vehicle import orbit, power, controls, mission, clock
from vehicle.payloads import query, image, log, memory
# Any default values here
default_cf = os.path.join(os.getcwd(), 'configs/agent.yaml')
default_lf = os.path.join(os.getcwd(), 'agentlog.txt')
default_orbit = os.path.join(os.getcwd(), 'positioning/regress2.json')
default_vehicle = 'default'
# argparse configuration; as of the first iteration, it'll just take a config
# file and a logfile


DEBUG = True
default_if = 'lo'
parser = argparse.ArgumentParser( prog = 'rei_agent',
                                  description = 'Runs the REI agent')

commands = ['run', 'list']


parser.add_argument('-c', '--config', default = default_cf, help =
                    'Master configuration file')
parser.add_argument('-l', '--logger', default = default_lf, help =
                    'Log path')
parser.add_argument('-o', '--orbit', default = default_orbit, help =
                    'Orbit parameters file')
parser.add_argument('-v', '--vehicle', default = default_vehicle, help
                    = 'Vehicle to use for orbit modeling')
parser.add_argument('-s', '--start', type=float, default = 0.0, help =
                    'Start time for orbit')
parser.add_argument('-d', '--dry-run', action = 'store_true',
                    help = 'Instructs the agent to work in dry-run mode')
parser.add_argument('command', default = 'run', help ='command')




def read_config(args):
    """
    read_config(args)
    Given a set of command line arguments, extract the configuration file,
    Verify and normalize the data.  Terminating if nothing is being done. 
    """
    cf_n = utils.expanduser(args.config)
    logging.info('Reading configuration data') 
    with open(cf_n, 'r') as cf_h:
        config_data = yaml.safe_load(cf_h)
    #
    # Verification and fixing -- determine the root directory and
    # place absolute paths for all other directories relative to that absolute
    # root
    if not 'base_dir' in config_data:
        logging.error('No base directory in configuration data, aborting.')
        return None
    elif not os.path.exists(utils.expanduser(config_data['base_dir'])):
        logging.error(f"Base directory '{config_data['base_dir']}' doesn't exist, aborting.")
        return None

    # Now, fix the directories
    # That didn't do what you thought it did. Now it works for real, not as overflow
    config_data['dry_run'] = args.dry_run
    for i in config_data.keys():
        if i == 'base_dir':
            continue

        # If its not absolute, assume its relative
        # Could check for existence here but code could create folders
        if i.split('_')[-1] == 'dir' and not os.path.isabs(config_data[i]):
            config_data[i] = os.path.join(config_data['base_dir'], config_data[i])

    logging.debug('Configuration information')
    for k,v in config_data.items():
        logging.debug('{}:{}'.format(k,v))

    return config_data


def list_config(cfdata):
    for k,v in cfdata.items():
        print("%s: %s" % (k,v))
        

# TODO: Understand how this all fits in
def list_assets(odata):
    results = {}
    for i in odata:
        if not i[0] in results:
            results[i[0]] = i[1]
        if results[i[0]] > i[1]:
            results[i[0]] == i[1]
    for i in results: print("%-20s %.4f" % (i, results[i]))
    return results


def status_line(state):
    """
    status_line prints a status line showing the current state of the system
    """
    buffer = f"{state['obj_t']:.4f} {state['elapsed_t']:.4f} "

    for ifc, bw in state['bws']:
        buffer += "%s:%f " %(ifc, bw)

    logging.info(buffer)
    

def main_loop(dry_run, offset, sleep_interval, duration, bus, mem):
    """
    Main loop for the satellite bus.  In the revised
    version, all connectivty is managed by the msc, so all the
    bus has to do is poll for any outstanding activity
    on fixed intervals. 
    
    """
    zero_t = time.time()
    init_t = offset
    old_ctable = set()
    ccount = 0 

    while(True):
        elapsed = time.time() - zero_t
        current = init_t + elapsed
        ccount += 1

        cbuf = f'{ccount:08}'
        mem.poke('cycles', cbuf)

        logging.info(f'Time {elapsed:6.2f}')
        bus.image.execute()

        if elapsed > duration:
            print(f'time: {elapsed:6.2f}, terminating')
            break

        time.sleep(sleep_interval)


def server_loop(port, bus, mem):
    with open('/etc/hostname') as fd:
        hostname = fd.read().strip()

    hostname = hostname.split('.')[0]

    listener = Listener((hostname, port), authkey=b'secret password')

    while True:
        conn = listener.accept()
        print('Connection accepted from ', listener.last_accepted)

        msg = conn.recv()
        q = query.QMsg('','','') # TODO: read this section of vehicle payloads
        q.read_msg(msg)
        result = bus.execute(q)
        logging.debug(f'Received data {result} from command {q}')

        conn.send(result)
        conn.close()
        
if __name__ == '__main__':
    #
    # Basic Configuration and argument management
    #
    args = parser.parse_args()
    dry_run = args.dry_run

    logging.basicConfig(filename=args.logger, level=logging.DEBUG, force=True)
    logging.info('Starting logging at %s' % time.ctime())

    cfdata = read_config(args)

    # Sets a default sleep interval
    sleep_interval = float(cfdata['sleep']) if 'sleep' in cfdata else 0.5

    # Check for modules for the bus
    master_clock = clock.Clock(time.time())
    spacelog = log.LogPayload(1000, master_clock)

    # Store a random value in memory which we can use for debug and check
    rstart = random.randrange(400000)
    rv = f'{rstart:08}'

    # files seems to be the num of files read
    mpl = memory.MemoryPayload(8192, { 'files': 0, 'cycles': 1024, 'rstart': 2048 } )
    mpl.poke('rstart',rv)

    # Stores and generates images
    ipl = image.ImagePayload(cfdata['image_dir'], ['a','b','c'], spacelog, master_clock)

    # Actually executes things
    qpl = query.QueryPayload(cfdata['keyfile'], ipl, cfdata['mission_dir'], False, spacelog, master_clock, mpl)

    # Mission-specific configuration and argument management
    # odata = list(orbit.load_event_file(args.orbit))
    odata = orbit.load_event_file(args.orbit)

    ctable = [('timeout',{'len':3600})]

    full_controls = controls.create_all_controls(ctable)

    for c in full_controls:
        c.startup()

    # Execute command
    if args.vehicle != 'default':
        # odata = list(orbit.select_vehicle(odata, args.vehicle))
        odata = orbit.select_vehicle(odata, args.vehicle)
    elif args.command == 'list':
        list_assets(odata)
    elif args.command == 'config':
        list_config(cfdata)
    elif args.command == 'abort':
        print('aborting')
        sys.exit(-1)

    if args.command == 'run':
        port = 6000
        buffer = queue.LifoQueue()
        # Start the main loop
        loop_args = (dry_run, 100, sleep_interval, 600, qpl, mpl)
        lthread = threading.Thread(target = main_loop, args = loop_args)
        server_thread = threading.Thread(target = server_loop, args=(port, qpl, mpl))
        lthread.start()
        server_thread.start()
        lthread.join()
        print('finished the main thread')
        sys.exit()


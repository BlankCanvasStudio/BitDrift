#!/usr/bin/env python3
# The channel manager
# The channel manager is a multihomed device which manages
# interfaces between various elements. 
import argparse, os, sys, time, yaml, logging

from modules import command, attack

from vehicle import orbit, power, controls, mission
# Any default values here
default_cf = os.path.join(os.getcwd(), 'configs/msc_agent.yaml')
default_lf = os.path.join(os.getcwd(), 'msc_log.txt')
default_orbit = os.path.join(os.getcwd(), 'positioning/regress2.json')
default_vehicle = []
# argparse configuration; as of the first iteration, it'll just take a config
# file and a logfile


DEBUG = True
default_if = 'lo'
parser = argparse.ArgumentParser( prog = 'msc_agent',
                                  description = 'Runs the channel manager')

commands = ['run', 'init', 'list', 'clear']

parser.add_argument('-c', '--config', default = default_cf, help =
                    'Master configuration file')
parser.add_argument('-l', '--logger', default = default_lf, help =
                    'Log path')
parser.add_argument('-o', '--orbit', default = default_orbit, help =
                    'Orbit parameters file')
parser.add_argument('-v', '--vehicle', default = default_vehicle, action = 'append', help
                    = 'Vehicle to use for orbit modeling')
parser.add_argument('-s', '--start', type=float, default = 0.0, help =
                    'Start time for orbit')
parser.add_argument('-d', '--dry-run', action = 'store_true',
                    help = 'Instructs the agent to work in dry-run mode')
parser.add_argument('-m', '--multiplier', help = 'Timing multiplier', default = 1)
parser.add_argument('command', default = 'run', help =f'Commands for the system, options are {",".join(commands)}')


def read_config(args):
    """
    read_config(args)
    Given a set of command line arguments, extract the configuration file,
    Verify and normalize the data.  Terminating if nothing is being done. 
    """
    cf_n = args.config
    if not os.path.exists(cf_n):
        sys.stderr.write("Configuration file {} does not exist; aborting\n".format(cf_n))

    logging.info('Checking configuration data in file {}'.format(cf_n)) 
    with open(cf_n, 'r') as cf_h:
        config_data = yaml.safe_load(cf_h)

    #
    # Verification and fixing -- determine the root directory and
    # place absolute paths for all other directories relative to that absolute
    # root
    if not 'base_dir' in config_data:
        logging.error('No base directory in configuration data, aborting.')
        return None

    elif not os.path.exists(config_data['base_dir']):
        logging.error(f"Base directory '{config_data['base_dir']}' doesn't exist, aborting.")
        return None

    # Now, fix the directories
    # 2024/10/28 I'm accumulating some technical debt here by making the decision
    # to just automatically modify anything which ends in '_dir' and which doesn't
    # begin with a /.
    config_data['dry_run'] = args.dry_run
    config_data['multiplier'] = int(args.multiplier)
    config_data['stime'] = float(args.start)

    for i in config_data.keys():
        if i == 'base_dir':
            continue

        if i.split('_')[-1] == 'dir' and not os.path.isabs(config_data[i]):
            config_data[i] = os.path.join(config_data['base_dir'], config_data[i])

    logging.debug('Configuration information')
    for k,v in config_data.items():
        logging.debug('{}:{}'.format(k,v))

    linkt = {}

    # Convert the array fo hashes into a single master hash
    for i in config_data['links']:
        linkt.update(i)

    config_data['links'] = linkt

    return config_data


def list_config(cfdata):
    for k,v in cfdata.items():
        print("%s: %s" % (k,v))


def list_assets(odata):
    """
    list_assets (odata):
    For each vehicle, print ground stations and active time to each 
    """
    results = {}
    for i in odata.keys():
        vehicle = i
        bases = {}

        for st,et,_,_,gs in odata[i]: # We don't care about direction/bandwidth
            # We're treating each entry as a tuple of st/et/entries
            # We'll keep min/max/count
            if not gs in bases:
                bases[gs] = [99999999999999.0,-1,0]
            if float(st) <= bases[gs][0]:
                bases[gs][0] = float(st)
            if float(et) >= bases[gs][1]:
                bases[gs][1] = float(et)

            bases[gs][2] += 1 

        results[i] = bases

    for i in results.keys():
        for j in results[i]:
            st,et,pd = results[i][j]
            print(f'{i:12s},{j[0:12]:12s},{st:.5f},{et:.5f},{pd}')
            

def status_line(state):
    """
    status_line prints a status line showing the current state of the system
    """
    buffer = "objective:{:.4f} elapsed:{:.4f} ".format(state['obj_t'], state['elapsed_t'])
    logging.info(buffer)


def main_loop(dry_run, vehicles, timing_data, offset, linkdb, sleep_interval):
    """
    This is the multiple-satellite emulation loop using the revised
    orbit library. 
    """
    run_start(linkdb) # blackhole everything
    state = {'obj_t':0, 'elapsed_t': 0, 'bws':[]}    

    # We start by creating an objective time.
    zero_t = time.time()
    init_t = offset
    old_ctable = set()

    while(True):
        elapsed = time.time() - zero_t
        current = init_t + elapsed
        state = {'obj_t': current, 'elapsed_t': elapsed}
        
        connections = []
        for i in vehicles:
            connections += orbit.get_rel_links(i, current, timing_data)

        ctable = set()
        for i in connections:
            if len(i) <= 0:
                continue

            vehicle, stime, etime, dirc, bw, dest = i
            dest = dest.lower() # Safety check
            ctable.add("{}.{}".format(vehicle, dest))

        all_links = ctable.union(old_ctable)
        for i in all_links:
            if not i in old_ctable:
                s = i.split('.')[0] # I see what you're doing here but this doesn't work with IPs
                d = i.split('.')[1]

                if not d in linkdb:
                    logging.debug(f'Ground station {d} not present, skipping')
                else:
                    logging.info(f"Setting up link from {s} to {d}")
                    sip = linkdb[s]['ip']
                    dip = linkdb[d]['ip']
                    connect(s, sip, d, dip)

            if not i in ctable:
                s = i.split('.')[0]
                d = i.split('.')[1]

                if not d in linkdb:
                    logging.debug(f'Ground station {d} not present, skipping')
                else:
                    logging.info(f"Shutting down  link from {s} to {d}")
                    sip = linkdb[s]['ip']
                    dip = linkdb[d]['ip']
                    disconnect(s, sip, d, dip)

        status_line(state)
        old_ctable = ctable
        time.sleep(sleep_interval)


def run_start(linkdb):
    # We're going to clean out the entire database first, then set up the rules
    
    for i in linkdb.keys():
        for j in linkdb.keys():
            if i == j:
                continue

            if linkdb[i]['space'] is True or linkdb[j]['space'] is True:
                connect(i, linkdb[i]['ip'],j,linkdb[j]['ip'])
                disconnect(i,linkdb[i]['ip'], j,linkdb[j]['ip'])
                
def setup_policies_dummy():
    """
    setup_policies_dummy
    Creates the policy-based routing infrastructure for a
    dummy system.

    This is really a no-op here but it at least logs the action.
    """
    logging.info('Policy setup; dummy machine.')
    return

def connect(v1n, v1ip, v2n, v2ip):
    """
    connect(v1, v2)
    Connects two vehicles to each other
    """
    logging.info("Connecting vehicles {}({}) and {}({})".format(v1n, v1ip, v2n,v2ip))

    cmdstring = "ip rule del from {}/32 to {}/32 lookup scecm".format(v1ip, v2ip)
    print(cmdstring)
    os.system(cmdstring)

    cmdstring = "ip rule del from {}/32 to {}/32 lookup scecm".format(v2ip, v1ip)
    print(cmdstring)
    os.system(cmdstring)

    return

def disconnect(v1n, v1ip, v2n, v2ip):
    """
    disconnect(v1, v2)
    Disconnects two vehicles
    """
    logging.info("Disconnecting vehicles {}({}) and {}({})".format(v1n, v1ip, v2n, v2ip))

    cmdstring = "ip rule add from {}/32 to {}/32 lookup scecm".format(v1ip, v2ip)
    print(cmdstring)
    os.system(cmdstring)

    return

def setup_policies_ubuntu():
    """
    setup_policies_ubuntu()
    Craeates the basic policy infrastructure for running the CM on ubuntu.  This consists
    of creating a second blackhole table.
    """
    rt_path = '/etc/iproute2/rt_tables'

    logging.info('Policy setup; checking to see if the custom table is there')
    if not os.path.exists(rt_path):
        logging.error(f'File {rt_path} missing.  Aborting')
        return None

    r_pipe = open(rt_path,'r')
    rt= {}
    for i in r_pipe.readlines():
        if i[0] == '#': # ignore comments
            continue

        print(i[:-1], len(i))
        index,v = i[:-1].split()
        index = int(index)
        rt[v] = index 

    # This is a bit too elaborate because it assumes that the channel manager VM is
    # running a bunch of other things which is, frankly, dumb.
    if 'scecm' in rt:
        print('Channel manager found, exiting')
        return 

    # Build the channel manager blackhole
    ind_tbl = set(rt.values())
    for i in range(100,200):
        if not i in ind_tbl:
            break
        logging.info('No channel manager channel found, adding')
    # Create the routing tools; the REI works by specifying a second routing table
    # which is just a blackhole.  When a routing policy is added, it pushes any
    # s/d pairings for that policy to the blackhole table (scecm)
    os.system("echo '{}     scecm' >> /etc/iproute2/rt_tables".format(i))
    os.system("ip route add blackhole 10.0.0.0/16 table scecm")


if __name__ == '__main__':

    #
    # Basic Configuration and argument management
    #
    args = parser.parse_args()
    dry_run = args.dry_run

    logging.basicConfig(filename=args.logger, level=logging.DEBUG, force=True)

    ltime = time.ctime()
    logging.info(f'Starting logging at {ltime}')
    logging.info(f'Command line info is: {args}')

    cfdata = read_config(args)
    logging.info(f'cfdata: {cfdata}')

    sleep_interval = float(cfdata['sleep']) if 'sleep' in cfdata else 0.5
        
    # Mission-specific configuration and argument management
    odata = orbit.load_event_file(args.orbit)

    vehicles = []
    ctable = [('timeout',{'len':3600})]

    full_controls = controls.create_all_controls(ctable)
    for c in full_controls:
        c.startup()


    # Execute command
    vehicles = args.vehicle

    if args.command == 'run':
        if cfdata['stime'] == 0.0:
            start_time = orbit.get_vehicle_stime(odata, args.vehicle) - 15 # Where does this magic number come from?
        else:
            start_time = cfdata['stime']

        main_loop(dry_run, vehicles, odata, start_time,
                  cfdata['links'], sleep_interval)
    elif args.command == 'init':
        setup_policies_ubuntu() 
    elif args.command == 'list':
        list_assets(odata)
    elif args.command == 'clear':
        clear_rules(odata)
    elif args.command == 'config':
        list_config(cfdata)
    elif args.command == 'abort':
        print('aborting')
        sys.exit(-1)


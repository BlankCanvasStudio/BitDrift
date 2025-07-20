#!/usr/bin/env python3
#
#
# The defender agent compares the contents of the vehicle's memory
# against the ground station logs, and raises an alert when
# there's 
#
# GFA Log messages:
# time [epoch],action = {ping/fetch/query/request},success (0/1),optional argument (file in case of success fetch)
import argparse, time, os, random, sys, yaml
from multiprocessing.connection import Client

from pythonping import ping 
from vehicle.payloads import query

secrets = {
    'jsmith':'foobar',
    'bjones':'barbaz',
    'sbaratheon': 'mannis',
}

def parse_config(cf_n):
    """
    parse_config (cf_n)
    Parses a configuration file.  The config file consists of 
    two fields: 
        gs: a list of ground stations
        v: a list of vehicles
    The device contacts vehicles and ground stations to compare 
    file counts.
    """
    with open(cf_n, 'r') as cf_h:
        config_data = yaml.safe_load(cf_h)

    return(config_data)

def get_vehicle_pulls(vehicle):
    sys.stderr.write(f'Initiating diagnostic pull from {vehicle}\n')

    pr = ping(vehicle, timeout = 1.0, count = 2)
    if pr.stats_packets_returned == 0:
        # Assume a failure
        sys.stderr.write(f'Vehicle {vehicle} out of range, aborting pull\n')
        return -1

    msg = query.QMsg(query.ACTION_PEEK,'jsmith',f'files:8')
    sys.stderr.write(f'Sending message {msg}\n')

    try:
        conn = Client((vehicle, 6000), authkey=b'secret password')
        conn.send(msg.gen_msg())
        result = int(conn.recv())
    except:
        return -1

    return result


def get_station_pulls(station):
    sys.stderr.write(f'Pulling data from station {station}\n')

    fh = os.popen(f'ssh -i /home/mcollins/.ssh/merge_key mcollins@{station} -o StrictHostKeyChecking=no "cat /home/mcollins/rei_agent/datalog.txt"','r')
    data = fh.readlines()

    result = {}
    for l in data:
        st, tgt, action, status = l.split(',')[0:4]
        st = float(st)
     
        if action != 'fetch':
            continue

        cc = result.get(tgt, 0)

        status = int(status)
        if status <= 0:
            status = 0
            # Implicitly managing negative status codes, a 0 indicates a failure

        result[tgt] = cc + status

    return result

if __name__ == '__main__':
    stime = time.time()

    cf_n = sys.argv[1]
    tgt_interval = int(sys.argv[2])
    tgt_count = int(sys.argv[3])

    cfdata = parse_config(cf_n)

    # First step, get status information from any vehicle
    for i in range(tgt_count):
        sys.stderr.write(f"Running loop, {i}/{tgt_count}\n")
        sys.stderr.write(f"Polling vehicles\n")

        pull_count = {}

        for j in cfdata['vehicles']:
            v_pc = get_vehicle_pulls(j)
            cv_pc = pull_count.get(j,0)
            cv_pc += v_pc
            pull_count[j] = cv_pc

        s_pull_count = {}

        for j in cfdata['stations']:
            s_pc = get_station_pulls(j)
            for k in s_pc.keys():
                sv_pc = s_pull_count.get(k, 0)
                csv_pc = s_pc.get(k, 0)
                s_pull_count[k] = sv_pc + csv_pc

        sys.stderr.write(f"{pull_count} {s_pull_count}")

        for key, value in s_pull_count.items():
            if key not in pull_count:
                continue

            # Could apply de-morgans but I'm lazy
            if not(pull_count[key] != s_pull_count[key] and pull_count[key] > -1):
                continue

            sys.stdout.write(f"{time.time() - stime:.4f},{key},{pull_count[key]},{s_pull_count[key]}\n")
            sys.stdout.flush()
            sys.exit(-1)

            # This shouldn't be reachable, correct?
            sys.stderr.write(f"Alert found at offset {time.time() - stime:.4f}: {key} ({pull_count[key]}/{s_pull_count[key]})\n")

        sys.stderr.write('Sleeping\n')
        time.sleep(tgt_interval)


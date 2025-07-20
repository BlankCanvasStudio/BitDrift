#!/usr/bin/env python3
# The command module for the REI agent handles commands
#
import json
import sys
import argparse
import time
import netifaces
import os

# We are going to work on 200ms timeslice

def is_interface_up(ifid):
    if netifaces.AF_INET in netifaces.ifaddresses(ifid):
        return True
    return False

def stop_interface(ifid):
    os.system('sudo ip link set dev %s down' % ifid)
    return

def start_interface(ifid):
    os.system('sudo ip link set dev %s up' % ifid)
    return


def load_event_file(event_fn):
    """
    load_event_file(event_fn) 
    loads an event file and gets the time/datarate values
    """
    result = []
    with open(event_fn, 'r') as fh:
        # TODO: fix the communication so you have separate uplink/downlink.  Problem is that since
        # the value is handled with a label it's not easily done using a comprehension
        result = [
            (i['asset_id'],i['time'],i['timeslice'],i['communication'][0]['datarate'],
             i['communication'][0]['endpoints']) for i in json.loads(fh.read())['system_state']]
    return result

def create_bandwidth_queues(timing_info):
    """
    Takes the bandwidht data and creates a sequence of event queues
    TODO: Make multitarget
    """
    result = []
    for asset, stime, tslice, bandwidth, targets in timing_info:
        result.append((float(stime), float(bandwidth)))
        result.append((float(stime) + float(tslice), 0))
    return result

# Bogo initialization, sans argparse
# 
if __name__ == '__main__':
    timing_data = load_event_file(df_n)
    timing_queue = create_bandwidth_queues(timing_data)
    tdelta = time.time() - offset
    print(timing_queue)
    while(True):
        t = time.time() - tdelta
        # We will sequentially pop values off of timing queue
        if len(timing_queue) > 1:
            print(t, timing_queue[1][0], t>timing_queue[1][0])
            while t >= timing_queue[1][0]:
                del timing_queue[0]
        current_bw = timing_queue[0][1]
        print(t, current_bw)
        time.sleep(0.5)


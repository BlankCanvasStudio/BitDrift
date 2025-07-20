#orbit.py
#
# orbit.py is the module that handles all the orbital data parsing elements
#
import json
import argparse
import time

# We are going to work on 200ms timeslice

def load_event_file(event_fn):
    """
    load_event_file(event_fn) (file x string) -> list
    loads the event file and returns a data structure read in from that
    description.

    In orbit2, the data structure is now a table indexed by vehicle, then time slice as
    a (stime, etime) pairing.  
    """
    result = {}
    with open(event_fn, 'r') as fh:
        # TODO: fix the communication so you have separate uplink/downlink.  Problem is that since
        # the value is handled with a label it's not easily done using a comprehension
        result = {}
        for i in json.loads(fh.read())['system_state']:
            id = i['asset_id']
            comm_def = tuple([(j['name'],j['type'],j['datarate'],j['endpoints'][0]) for j in i['communication']])
            if not id in result:
                result[id] = []
            st = float(i['time'])
            et = float(i['time']) + float(i['timeslice'])
            for j in comm_def:
                result[id].append((st, et, j[1], j[2], j[3]))
    return result

def get_rel_links(vehicle, otime, event_db):
    result = []
    lt = event_db[vehicle]
    for i in lt:
        if i[0] <= otime and i[1] >= otime:
            result.append(tuple([vehicle] + list(i)))
    return result

def get_vehicle_stime(event_db, vehicle_id):
    mtime = -1
    for i in select_vehicle(event_db, vehicle_id):
        if (mtime == -1) or (float(i[1]) < mtime):
            mtime = i[1]
    return mtime
            
def select_vehicle(event_db, vehicle_id):
    """
    select_vehicle(event_db, vehicle_id)
    filters for a specific vehicle (vehicle id) in the database
    If the vehicle isn't found, return None and terminate
    """
    result = filter(lambda x:x[0] == vehicle_id, event_db)
    if len(list(result)) == 0:
        return None

    return filter(lambda x:x[0] == vehicle_id, event_db)

def create_bandwidth_queues(timing_info):
    """
    Takes the bandwidht data and creates a sequence of event queues
    TODO: Make multitarget
    """
    result = []
    for asset, stime, tslice, links in timing_info:
        for link_id, link_type, link_bw, link_ep in links:
            result.append((float(stime), float(link_bw), asset, link_id, link_ep))
            result.append((float(stime) + float(tslice), 0, asset, link_id, link_ep))
    return result

def create_bandwidth_database(timing_info):
    result = {}
    linkeps = set()
    for asset, stime, tslice, links in timing_info:
        for link_id, link_type, link_bw, link_ep in links:
            linkeps.add(link_ep)
            if not asset in result:
                result[asset] = {}
            if not link_ep in result[asset]:
                result[asset][link_ep] = []
            result[asset][link_ep].append((stime, stime + tslice, link_id, link_type, link_bw))
    return (result, linkeps)


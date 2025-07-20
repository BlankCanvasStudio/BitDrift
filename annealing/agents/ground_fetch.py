#!/usr/bin/env python3
#
#
# The ground fetch agent will grab an image and copy it to local disk
#
# GFA Log messages:
# time [epoch],action = {ping/fetch/query/request},success (0/1),optional argument (file in case of success fetch)
from multiprocessing.connection import Client
import argparse, time, os, sys
from vehicle.payloads import query
import os, sys, random
from pythonping import ping 


secrets = {
    'jsmith':'foobar',
    'bjones':'barbaz',
    'sbaratheon': 'mannis',
}


def log_action(vehicle, action_type,result,arg):
    t = time.time()

    sys.stdout.write(f'{t:.4f},{vehicle},{action_type},{result},{arg}\n')
    sys.stdout.flush()


if __name__ == '__main__':

    tgt_host = sys.argv[1]
    tgt_interval = sys.argv[2]
    tgt_count = int(sys.argv[3])

    for i in range(tgt_count):
        sys.stderr.write('sleeping\n')
        time.sleep(int(tgt_interval) + random.randrange(10))

        # Ping the satellite
        pr = ping(tgt_host, timeout = 1.0, count = 2)

        if pr.stats_packets_returned == 0:
            log_action(tgt_host, 'ping', 0, '')
            sys.stderr.write(f'Currently out of range, aborting this session\n')
            continue

        log_action(tgt_host, 'ping', 1, '')

        user = 'jsmith'
        msg = query.QMsg(query.ACTION_QUERY, 'jsmith', 'a*')

        try:
            conn = Client((tgt_host, 6000), authkey=b'secret password')
        except:
            log_action(tgt_host,'query',0,'')
            continue

        sys.stderr.write(f'Sending message {msg}\n')
        conn.send(msg.gen_msg())

        file_list = conn.recv()
        log_action(tgt_host, 'query', 1, len(file_list.split(':')))
        tgtfile = random.choice(file_list.split(':'))
        conn.close()

        try:
            conn = Client((tgt_host, 6000), authkey=b'secret password')
        except:
            log_action(tgt_host,'reqtoken',0,'')
            continue

        msg = query.QMsg(query.ACTION_REQTOKEN,'jsmith','')
        sys.stderr.write(f'Sending message {msg}\n')
        conn.send(msg.gen_msg())

        token = conn.recv()
        sys.stderr.write(f'{token}\n')
        conn.close()

        log_action(tgt_host,'reqtoken',1,token)            
        qtoken = query.QMsg.gen_msgtoken(user,secrets[user],token)
        msg = query.QMsg(query.ACTION_FETCH,tgtfile,qtoken)

        try:
            conn = Client((tgt_host, 6000), authkey=b'secret password')
        except:
            log_action(tgt_host,'fetch',0,'')
            continue

        sys.stderr.write(f'Sending message {msg}\n')
        conn.send(msg.gen_msg())

        file = conn.recv()
        log_action(tgt_host, 'fetch', 1, '')
        conn.close()

        with open('readfile.img', 'w') as fh:
            fh.write(file)


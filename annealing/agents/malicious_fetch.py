#!/usr/bin/env python3
#
#
# The ground fetch agent will grab an image and copy it to local disk

from multiprocessing.connection import Client
import argparse, time, os, sys
from vehicle.payloads import query
import os, sys, random
secrets = {
    'jsmith':'foobar',
    'bjones':'barbaz',
    'sbaratheon': 'mannis',
}

if __name__ == '__main__':
    tgt_host = sys.argv[1]

    user = 'jsmith'
    msg = query.QMsg(query.ACTION_QUERY,'jsmith','a*')

    conn = Client((tgt_host, 6000), authkey=b'secret password')
    print(f'Sending message {msg}')
    conn.send(msg.gen_msg())

    file_list = conn.recv()
    tgtfile = random.choice(file_list.split(':'))
    conn.close()

    token = 'XXXXXXXXXXXX'
    qtoken = query.QMsg.gen_msgtoken(user,'iamveryevil',token)
    msg = query.QMsg(query.ACTION_FETCH,tgtfile,qtoken)
    conn = Client((tgt_host, 6000), authkey=b'secret password')

    print(f'Sending message {msg}')
    conn.send(msg.gen_msg())

    file = conn.recv()
    conn.close()

    with open('readfile.img','w') as fh:
        fh.write(file)


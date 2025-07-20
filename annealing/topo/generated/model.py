#!/usr/bin/python3
from mergexp import *

# Create a network topology object.
# This is a test project involving a non-CM managed version of the REI to test initial timing and contact
net = Network('multinode',routing == static)

vehicles = []
cm = net.node('cm')



for i in range(0, 4):
    vehicles.append(net.node('birds{}'.format(i)))


# Create a link connecting the two nodes.
value = 16
for index in vehicles:
    new_net = (net.connect([index,cm]))
    new_net[index].socket.addrs = ip4('10.0.%d.1/24' % value)
    new_net[cm].socket.addrs = ip4('10.0.%d.2/24' % value)
    value +=1 


gsnames = []
    

for i in range(0, 2):
    gsnames.append('blue{}'.format(i))



for i in range(0, 2):
    gsnames.append('red{}'.format(i))



for i in range(0, 2):
    gsnames.append('green{}'.format(i))


gs = []

for i in gsnames:
    gs.append(net.node(i))

value = 32
for index in gs:
    ground_net = (net.connect([index,cm]))
    ground_net[index].socket.addrs = ip4('10.0.%d.1/24' % value)
    ground_net[cm].socket.addrs = ip4('10.0.%d.2/24' % value)
    value += 1

# Make this file a runnable experiment based on our two node topology.
experiment(net)
    
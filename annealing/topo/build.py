#!/bin/python3

import os, yaml, re


parameters_path = './parameters.yaml'


def read_parameters():
    config_data = {}

    with open(parameters_path, 'r') as fd:
        config_data = yaml.safe_load(fd)

    return config_data


def make_generated_dirs():
    try:
        os.mkdir('./topo/generated/')
    except FileExistsError:
        pass
    except Exception as e:
        raise e


def generate_topology_file(space, gs):
    birds = 0
    ground_stations = 0

    for key, val in space.items():
        birds += val

    for key, val in gs.items():
        ground_stations += val

    file_contents = f"""#!/usr/bin/python3
        from mergexp import *

        # Create a network topology object.
        # This is a test project involving a non-CM managed version of the REI to test initial timing and contact
        net = Network('multinode',routing == static)

        vehicles = []
        cm = net.node('cm')

        """

    for host, num in space.items():
        file_contents += f"""

        for i in range(0, {num}):
            vehicles.append(net.node('{host}{{}}'.format(i)))

        """

    file_contents += f"""
        # Create a link connecting the two nodes.
        value = 16
        for index in vehicles:
            new_net = (net.connect([index,cm]))
            new_net[index].socket.addrs = ip4('10.0.%d.1/24' % value)
            new_net[cm].socket.addrs = ip4('10.0.%d.2/24' % value)
            value +=1 

        """

    file_contents += f"""
        gsnames = []
    """

    for host, num in gs.items():
        file_contents += f"""

        for i in range(0, {num}):
            gsnames.append('{host}{{}}'.format(i))

        """

    file_contents += f"""
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
    """

    # remove spaces to file isn't annoying to read but follows syntax
    first_loc = file_contents.split('\n')[1]
    extra_padding = '\n'
    for i in range(0, len(first_loc)):
        if first_loc[i] != ' ':
            break
        extra_padding += ' '

    file_contents = re.sub(re.escape(extra_padding), '\n', file_contents)

    with open('./topo/generated/model.py', 'w') as fd:
        fd.write(file_contents)



def main():
    config = read_parameters()

    if 'hosts' not in config:
        raise Exception("hosts not specified in config file")

    if 'space' not in config['hosts']:
        raise Exception("space not specified in hosts section of config file")

    if 'gs' not in config['hosts']:
        raise Exception("space not specified in hosts section of config file")

    make_generated_dirs()
    generate_topology_file(config['hosts']['space'], config['hosts']['gs'])


if __name__ == "__main__":
    main()


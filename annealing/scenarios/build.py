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
        os.mkdir('./scenarios/generated/')
    except FileExistsError:
        pass
    except Exception as e:
        raise e


def generate_inventory_file(hosts):
    file_contents =  "[infra]\n"
    file_contents += "cm\n\n"

    # Write the variety of space vehicles
    for cat, num in hosts['space'].items():
        file_contents += f"[{cat}]\n"

        for i in range(0, num):
            file_contents += f'{cat}{i}\n'

        file_contents += "\n"

    # Write the space wrapper class for ease
    file_contents += "[space:children]\n"
    for cat in hosts['space']:
        file_contents += f"{cat}\n"
    file_contents += "\n"


    # Write the variety of ground segment nodes
    for cat, num in hosts['gs'].items():
        file_contents += f"[{cat}]\n"

        for i in range(0, num):
            file_contents += f'{cat}{i}\n'

        file_contents += "\n"

    # Write the ground segment wrapper class for ease
    file_contents += "[gs:children]\n"
    for cat in hosts['gs']:
        file_contents += f"{cat}\n"
    file_contents += "\n"


    with open('./scenarios/generated/inventory', 'w') as fd:
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
    generate_inventory_file(config['hosts'])


if __name__ == "__main__":
    main()


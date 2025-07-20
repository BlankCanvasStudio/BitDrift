#!/bin/bash

ssh cm "cd ~/rei_agent/agents && sudo python3 ./msc.py -o positioning/Scenario_AWS-LANDSAT.json -c configs/msc_agent.yaml -s 1672630635 -d -v landsat7 -v landsat9 -v landsat4 -v landsat8 run"



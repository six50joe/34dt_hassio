import appdaemon.plugins.hass.hassapi as hass
from appdaemon.appdaemon import AppDaemon
from time import time
from datetime import datetime, timezone

import os
import time
from datetime import datetime
import datetime
from enum import Enum
from collections import defaultdict

CONFIG_FILE_DIR           = "/config/data"
DEVICE_ENTRIES            = "device_status_list.txt"
VARIABLE_FILE_DIR         = "/config/variables"
VARIABLE_FILE             = "monitoring_vars.yaml"
LOVELACE_FILE_DIR         = "/config/lovelace"
DEVICE_STATE_CARDS_FILE   = "device_state_cards.yaml"

class DeviceType(Enum):
    THERMOSTAT = 1
    MOTION_DETECTOR = 2
    LIGHT = 3


now = None
#
# Device Reponsive State
#
# Tracks the last time normal activity occurred on home devices
#

class DeviceResponsiveState(hass.Hass):
    def initialize(self):
        self.log("Initializing DeviceResponsiveState")

        self.device_set = self.read_device_list()

        for dtype in self.device_set.keys():
            for device in self.device_set[dtype]:
                self.log(f"listening to {device['entity_id']}")
                self.listen_state(self.change_detected, device['entity_id'])
        self.generate_upd_variables()
        self.generate_lovelace_cards()

    def generate_upd_variables(self):
        path = VARIABLE_FILE_DIR + "/" + VARIABLE_FILE

        outputFile = open(path, 'w')

        for dtype in self.device_set.keys():
            for device in self.device_set[dtype]:
                outputFile.write(f"{device['var_name']}:\n")
                outputFile.write(f"  initial_value: 0\n")
                outputFile.write(f"  unique_id: {device['var_name']}\n")
                outputFile.write(f"  friendly_name: {device['name']}\n")

        outputFile.close()

    def generate_lovelace_cards(self):
        path = LOVELACE_FILE_DIR + "/" + DEVICE_STATE_CARDS_FILE

        outputFile = open(path, 'w')

        outputFile.write(f"    cards:\n");
        outputFile.write(f"      - type: vertical-stack\n");
        outputFile.write(f"        cards:\n");

        for dtype in self.device_set.keys():
            for device in self.device_set[dtype]:
                self.log(f"Generating card for  {device['entity_id']}")

                outputFile.write(f"        - type: custom:config-template-card\n");
                outputFile.write(f"          entities:\n");
                outputFile.write(f"            - device['entity_id']\n");
                outputFile.write(f"          card:\n");
                outputFile.write(f"            type: markdown\n");
                outputFile.write(f"            content: Returned color working!!!!!\n");
                outputFile.write(f"            title: device['name']\n");
                outputFile.write(f"            card_mod:\n");
                outputFile.write(f"              style: |\n");
                outputFile.write("                {% from 'device_updated_days.jinja' import entity_responsive_color %}\n");
                outputFile.write("                 ha-card {background-color: {{ entity_responsive_color('var.driveway_light_upd') }};}\n");
        outputFile.close()
                


    def read_device_list(self):
        path = CONFIG_FILE_DIR + "/" + DEVICE_ENTRIES
        self.log(path)

        device_set = defaultdict(list[DeviceType])

        inputFile = open(path, 'r')
        for line in inputFile:
            self.log(line)
            (device_name, var_name, entity_id, idtype) = line.split(',')
            device_type = DeviceType[idtype.strip()]
            device_info = { 'name': device_name, 'var_name': var_name, 'entity_id': entity_id }
            device_set[device_type].append(device_info)

        return device_set

    def entity_id_to_device_name(self, entity_id):
        device = None
        for dtype in self.device_set.keys():
            dev_list = self.device_set[dtype]
            device = next((dev for dev in dev_list if dev['entity_id'] == entity_id), None)
            if device:
                break
        return device['name']

    def entity_id_to_var_name(self, entity_id):
        device = None
        for dtype in self.device_set.keys():
            dev_list = self.device_set[dtype]
            device = next((dev for dev in dev_list if dev['entity_id'] == entity_id), None)
            if device:
                break
        return device['var_name']


    def change_detected(self, entity=None, data=None, arg1=None, arg2=None, arg3=None):
        self.log(f"Entity: {str(entity)}  Data: {data} Arg1: {arg1} Arg2: {arg2} Arg3: {arg3}")

        dev_name = self.entity_id_to_device_name(entity)

        if dev_name:
            self.log(f"{dev_name} recevied an update")
        else:
            self.log(f"Error: {entity} not registered")

        var_name = f"var.{self.entity_id_to_var_name(entity)}"

        now = time.time()

        self.call_service("var/set",
                          entity_id=var_name,
                          value=str(now))

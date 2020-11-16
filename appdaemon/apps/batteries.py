import appdaemon.plugins.hass.hassapi as hass
from appdaemon.appdaemon import AppDaemon

import os
import time
import datetime
import re

CONFIG_FILE_DIR           = "/config/data"
STATUS_FILENAME           = "batteries.txt"

#
# Check Battery Levels and Alerts
#
# Args:
#

class Batteries(hass.Hass):
    def initialize(self):
        self.listen_event(self.do_tracking, "scan_device_batteries")
#        self.do_tracking()

    def do_tracking(self, entity=None, data=None, arg1=None, arg2=None, arg3=None):
        file_map = self.read_tracking_file()
        device_map = self.scan_devices(file_map)
        self.check_devices(file_map, device_map)
        self.write_tracking_file(file_map, device_map)

    def send_notification(self, alert):
        self.log("Alerting: %s" % alert)
        self.call_service("notify/34dt_hassio", message=alert)
        
    def check_devices(self, file_map, device_map):
        for entity in device_map:
            if entity in file_map and file_map[entity]['track'] == 'X':
                continue

            rec_dt  = device_map[entity]['last_received_ts']
            sent_dt = device_map[entity]['last_sent_ts']
            recDT   = datetime.datetime.strptime(rec_dt, "%Y-%m-%d %H:%M:%S")
            sentDT  = datetime.datetime.strptime(sent_dt, "%Y-%m-%d %H:%M:%S")

            if recDT < sentDT:
                message = F"WARNING: For '{entity}' response for send at {sent_dt} not received. (last_rec = {rec_dt})"
                self.log(message)
                self.send_notification(message)


            elapsed = recDT - sentDT
            secs_elapsed = divmod(elapsed.total_seconds(), 60)

            if secs_elapsed[0] > (60 * 60 * 24):
                message = F"WARNING: For {'entity'} response for send was longer than a day. (last_rec = {rec_dt}, last_sent = {send_dt})"
                self.log(message)
                self.send_notification(message)
                
            #self.log(F"{entity} - received: {recTS} sent: received: {sentTS}")
            #self.log(F"Elapsed mins: {secs_elapsed}")


    def read_tracking_file(self):
        map = {}
        path = CONFIG_FILE_DIR + "/" + STATUS_FILENAME
        try:
            inp = open(path, 'r')
        except IOError:
            self.log(F"Tracking file '{path}' does not exist, will create later")
            return map

        for line in inp:
            if re.match("^\s*#", line): # Skip comments
                continue

            # X|dev_name|<last_sent_ts>|<last_received_ts>
            (track_ind, entity, last_sent_ts, last_received_ts) = line.split('|')
            map[entity] = { 'track' : track_ind,
                            'last_sent_ts' : last_sent_ts,
                            'last_received_ts' : last_received_ts }

        return map

    def write_tracking_file(self, file_map, scanned_map):
        path = CONFIG_FILE_DIR + "/" + STATUS_FILENAME

        out_file = open(path, 'w')
        out_file.write("#\n")
        out_file.write("# <track indicator> | <entity> | <last sent timestamp> | <last received timestamp>\n")
        out_file.write("# indicator:\n")
        out_file.write("#   - : enable alerts for this device (default)\n")
        out_file.write("#   X : do NOT enable alerts for this device\n")
        out_file.write("# --------------------------------------------------------------------------------\n")
            
        for entity in sorted(scanned_map, key=str):
            ind = '-'
            if entity in file_map:
                ind = file_map[entity]['track']
            out_file.write(F"{ind}|{entity}|{scanned_map[entity]['last_sent_ts']}|{scanned_map[entity]['last_received_ts']}\n")
            

    def scan_devices(self, file_map):
        scanned_map = {}
        zwaves = self.get_state("zwave")
        t = 0
        for entity, v in zwaves.items():
            if not ('receivedTS' in v['attributes'] \
                    and 'sentTS' in v['attributes']):

                # if entity in file_map and file_map[entity]['track'] != 'X':
                #     self.log(F"{entity} does not have timestamps")
                #     for att in v['attributes']:
                #         self.log(F"\tATTR: {att}") 
                continue
            
            recTS  = v['attributes']['receivedTS'][:19]
            sentTS = v['attributes']['sentTS'][:19]
            
            scanned_map[entity] = {}
            scanned_map[entity]['last_received_ts'] = recTS
            scanned_map[entity]['last_sent_ts']     = sentTS
        return scanned_map
            

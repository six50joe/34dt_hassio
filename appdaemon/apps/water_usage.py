import appdaemon.plugins.hass.hassapi as hass
from appdaemon.appdaemon import AppDaemon

import os
import time
import datetime


now = None
#
# Water Usage
#
# Args:
#

class WaterUsage(hass.Hass):
    def initialize(self):
        self.listen_state(self.flow_detected, "sensor.fortrezz_fmi_flow_meter_water")

    def not_home(self):
        joe_home = self.get_state("device_tracker.joe", attribute='name')

        trackers = self.get_trackers()
        for tracker in trackers:
            if tracker == "device_tracker.joe" \
               or tracker == "device_tracker.jamie":
                if not self.get_tracker_state(tracker) == "home":
                    return True
        return False

    def minutes_passed(self, previous_epoch, current_epoch):
        return float( (current_epoch - previous_epoch) / 60 )
        
    def flow_detected(self, entity=None, data=None, arg1=None, arg2=None, arg3=None):
        
        #self.log("ENTITY: %s DATA: %s ARG1: %s ARG2: %s ARG3: %s" \
        #         % (entity, data, arg1, arg2, arg3))

        prev_water_time = float(self.get_state("variable.prev_water_time", "state"))
        prev_water_usage = float(self.get_state("variable.prev_water_usage", "state"))
        
        water_usage = float(arg2)
        now  = time.time()

        minutes_passed = self.minutes_passed(prev_water_time, now)
        if minutes_passed < 15:
            return

        rate = float((water_usage - prev_water_usage) / minutes_passed)
        rate = round(rate, 3)
        self.log("USAGE RATE: %f" % rate)

        if rate > 1:
            if self.not_home():
                self.send_notification("Warning: water usage detected while not at home")
        
        if rate > 5:
            self.send_notification("Warning: water usage (%f) seems high" % rate)

        # ts = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d_%H:%M:%S')
        
        # self.log("EPOCH_NOW: %d FORMATTED: %s" \
        #     % (now, ts))
        
        
        self.call_service("variable/set_variable", variable='water_usage_rate', value=rate)

        self.call_service("variable/set_variable", variable='prev_water_usage', value=water_usage)
        self.call_service("variable/set_variable", variable='prev_water_time', value=now)
        

    def send_notification(self, alert):
        self.log("Alerting: %s" % alert)
        self.call_service("notify/34dt_hassio", message=alert)
        

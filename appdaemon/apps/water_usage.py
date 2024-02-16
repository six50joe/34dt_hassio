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
        self.listen_state(self.flow_detected, "sensor.flow_meter_water_consumption_us_gallons")

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

        water_usage = float(arg2)
        now  = time.time()

        var_prev_water_time = self.get_state("var.prev_water_time", "state")
        if var_prev_water_time:
            prev_water_time = float(self.get_state("var.prev_water_time", "state"))
        else:
            prev_water_time = now - (16 * 60)
        
        var_prev_water_usage = self.get_state("var.prev_water_usage", "state")
        if var_prev_water_usage:
            prev_water_usage = float(var_prev_water_usage)
        else:
            prev_water_usage = water_usage
        
        minutes_passed = self.minutes_passed(prev_water_time, now)
        if minutes_passed < 15:
            return

        rate = float((water_usage - prev_water_usage) / minutes_passed)
        rate = round(rate, 3)
        self.log("USAGE RATE: %f (reading=%f, previous=%f)" % (rate, water_usage, prev_water_usage))

        if rate > 1:
            if self.not_home():
                self.send_notification("Warning: water usage detected while not at home")
        
        if rate > 5:
            self.send_notification("Warning: water usage (%f) seems high" % rate)

        # ts = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d_%H:%M:%S')
        
        # self.log("EPOCH_NOW: %d FORMATTED: %s" \
        #     % (now, ts))
        
        
        self.call_service("var/set", entity_id='var.water_usage_rate', value=rate)

        self.call_service("var/set", entity_id='var.prev_water_usage', value=water_usage)
        self.call_service("var/set", entity_id='var.prev_water_time', value=now)
        

    def send_notification(self, alert):
        self.log("Alerting: %s" % alert)
        self.call_service("notify/34dt_hassio", message=alert)
        


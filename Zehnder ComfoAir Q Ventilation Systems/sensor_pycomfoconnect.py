# -*- coding: utf-8 -*-

import json
import sys
import argparse

from prtg.sensor.result import CustomSensorResult
from prtg.sensor.units import ValueUnit

from pycomfoconnect import *

local_name = 'PRTG'
local_uuid = bytes.fromhex('00000000000000000000000000000005')

sensor_data = {56: "",
               SENSOR_FAN_EXHAUST_FLOW: "",
               SENSOR_FAN_SUPPLY_FLOW: "",
               SENSOR_FAN_EXHAUST_SPEED: "",
               SENSOR_FAN_SUPPLY_SPEED: "",
               SENSOR_POWER_CURRENT: "",
               SENSOR_DAYS_TO_REPLACE_FILTER: "",
               SENSOR_TEMPERATURE_SUPPLY: "",
               SENSOR_BYPASS_STATE: "",
               SENSOR_TEMPERATURE_EXTRACT: "",
               SENSOR_TEMPERATURE_EXHAUST: "",
               SENSOR_TEMPERATURE_OUTDOOR: "",
               SENSOR_HUMIDITY_EXTRACT: "",
               SENSOR_HUMIDITY_EXHAUST: "",
               SENSOR_HUMIDITY_OUTDOOR: "",
               SENSOR_HUMIDITY_SUPPLY: "",
               }


def callback_sensor(sensor_id, sensor_value):
    sensor_data[sensor_id] = sensor_value


def discover_bridge(comfoconnect_ip):
    bridges = Bridge.discover(comfoconnect_ip)
    bridge = bridges[0] if bridges else None
    if bridge is None: 
        raise Exception("No bridges found!")
    return bridge


def register_sensors(comfoconnect): 
    comfoconnect.register_sensor(56)  # Operation mode
    comfoconnect.register_sensor(SENSOR_FAN_EXHAUST_FLOW)  # Temperature & Humidity: Supply Air (temperature)
    comfoconnect.register_sensor(SENSOR_FAN_SUPPLY_FLOW)  # Fans: Supply fan flow
    comfoconnect.register_sensor(SENSOR_FAN_EXHAUST_SPEED)  # Fans: Exhaust fan speed
    comfoconnect.register_sensor(SENSOR_FAN_SUPPLY_SPEED)  # Fans: Supply fan speed
    comfoconnect.register_sensor(SENSOR_FAN_SPEED_MODE)  # Fans: User Setting
    comfoconnect.register_sensor(SENSOR_POWER_CURRENT)  # Power Consumption: Current Ventilation
    comfoconnect.register_sensor(SENSOR_DAYS_TO_REPLACE_FILTER)  # Days left before filters must be replaced
    comfoconnect.register_sensor(SENSOR_TEMPERATURE_SUPPLY)  #  Temperaturee Supply
    comfoconnect.register_sensor(SENSOR_BYPASS_STATE)  # Bypass state
    comfoconnect.register_sensor(SENSOR_TEMPERATURE_EXTRACT)  # Temperature & Humidity: Extract Air (temperature)
    comfoconnect.register_sensor(SENSOR_TEMPERATURE_EXHAUST)  # Temperature & Humidity: Exhaust Air (temperature)
    comfoconnect.register_sensor(SENSOR_TEMPERATURE_OUTDOOR)  # Temperature & Humidity: Outdoor Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_EXTRACT)  # Temperature & Humidity: Extract Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_EXHAUST)  # Temperature & Humidity: Exhaust Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_OUTDOOR)  # Temperature & Humidity: Outdoor Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_SUPPLY)  # Temperature & Humidity: Supply Air (temperature)


def retrieve_sensor_data_for_seconds(comfoconnect, seconds): 
    while seconds > 0 :
        # Callback messages will arrive in the callback method.
        time.sleep(1)
        seconds = seconds - 1
        if not comfoconnect.is_connected():
            break


def connect_to_comfoconnect(comfoconnect_ip, comfoconnect_pin): 
    bridge = discover_bridge(comfoconnect_ip)
    comfoconnect = ComfoConnect(bridge, local_uuid, local_name, comfoconnect_pin)
    comfoconnect.callback_sensor = callback_sensor 
    comfoconnect.connect(False)  # Disconnect existing clients.
    return comfoconnect


def run_comfoconnect_handler(comfoconnect_ip, comfoconnect_pin):
    comfoconnect = connect_to_comfoconnect(comfoconnect_ip, comfoconnect_pin)
    register_sensors(comfoconnect)  
    retrieve_sensor_data_for_seconds(comfoconnect, 5)   
    comfoconnect.disconnect()   


def extract_ip(data):
    if not data["params"]:
        raise Exception("""
        No IP as parameter defined!"
        Make sure to pass arguments in sensor settings in following format:
        "<ip> <pin>". E.g: "193.123.23.1 9432"
        """)
    ip = data["params"].split(" ")[0]
    return ip


def extract_pin(data):
    if len(data["params"].split(" ")) < 2:
        raise Exception("""
        No PIN as parameter defined!
        Make sure to pass arguments in sensor settings in following format:
        "<ip> <pin>". E.g: "193.123.23.1 9432"
        """)
    pin = data["params"].split(" ")[1]
    return pin
    

if __name__ == "__main__":
    try:
        data = json.loads(sys.argv[1])
        csr = CustomSensorResult(text="This sensor runs on %s" % data["host"])
        
        #Params need to be set like this in sensor settings: "Additonal parameters: <ip> <pin>"
        comfoconnect_ip = extract_ip(data)
        comfoconnect_pin = extract_pin(data) 
        
        run_comfoconnect_handler(comfoconnect_ip, comfoconnect_pin) 
        
        
        ################################
        ####CODE SAMPLE FOR MIN MAX ####
        ################################
    #    csr.add_channel(name="Error-Warning-Threshold-Example",
    #                    value=81, #Der Wert beispielsweise würde limit_max_warning=70 überschreiten und dementsprechend eine Warnung werfen
    #                    unit=ValueUnit.PERCENT, 
    #                    is_limit_mode=True,
    #                    limit_max_error=90,   #Hier definierst du den Error Grenze nach oben hin. Werte größer 90 kommen in den Error Status
    #                    limit_max_warning=70, #Hier definierst du den Warning Grenze nach oben hin. Werte größer 70 kommen in den Warning Status
    #                    limit_min_error=10, #Hier definierst du die Error Grenze nach unten hin. Werte unter 10 kommen in den Error Status
    #                    limit_min_warning=30, #Hier definierst du die Warning Grenze nach unten hin. Werte unter 30 kommen in den Warning Status
    #                    limit_error_msg="Error occursed because of something!", #Die Error message die angezeigt wird wenn ein Error Wert erreicht worden ist
    #                    limit_warning_msg="Warning occured because of something!") #Die Warning message die angezeigt wird wenn ein Warning Wert erreicht worden ist                     
        ################################
        ####CODE SAMPLE FOR MIN MAX ####
        ################################

        csr.add_channel(name="Betriebsmodus",
                        value=sensor_data[56],
                        unit="Modus") # "-1" ist "Betrieb: Automatik", "1" ist "Betrieb: Manuell"    
        csr.add_channel(name="Lüftungsstufe",
                        value=sensor_data[SENSOR_FAN_SPEED_MODE],
                        unit="Stufe",
                        is_limit_mode=True,
                        limit_min_warning=-0.1,
                        limit_max_warning=3.1) # "0" ist "Außer Haus", "1","2","3" sind die Lüftungsstufen 1/2/3   
        csr.add_channel(name="Volumen Fortluftventilator",
                        value=sensor_data[SENSOR_FAN_EXHAUST_FLOW],
                        unit="m³/h",
                        is_limit_mode=True,
                        limit_min_warning=40)
        csr.add_primary_channel(name="Volumen Zuluftventilator",
                        value=sensor_data[SENSOR_FAN_SUPPLY_FLOW],
                        unit="m³/h",
                        is_limit_mode=True,
                        limit_min_warning=40)
        csr.add_channel(name="Drehzahl Fortluftventilator",
                        value=sensor_data[SENSOR_FAN_EXHAUST_SPEED],
                        unit="rpm")
        csr.add_channel(name="Drehzahl Zuluftventilator",
                        value=sensor_data[SENSOR_FAN_SUPPLY_SPEED],
                        is_limit_mode=True,
                        limit_min_error=1, 
                        limit_error_msg="Ventilator steht!",
                        unit="rpm")
        csr.add_channel(name="Energieverbrauch Lüftung",
                        value=sensor_data[SENSOR_POWER_CURRENT],
                        unit="Watt")
        csr.add_channel(name="Restlaufzeit Filter",
                        value=sensor_data[SENSOR_DAYS_TO_REPLACE_FILTER],
                        unit="Tage",
                        is_limit_mode=True,
                        limit_min_error=10, 
                        limit_min_warning=30,
                        limit_error_msg="Filterwechsel dringend",
                        limit_warning_msg="Filterwechsel demnächst")                
        csr.add_channel(name="Status Bypass",
                        value=sensor_data[SENSOR_BYPASS_STATE],
                        unit=ValueUnit.PERCENT)
        csr.add_channel(name="Temperatur Zuluft",
                        value=sensor_data[SENSOR_TEMPERATURE_SUPPLY]/10,
                        is_float=True,
                        unit=ValueUnit.TEMPERATURE,
                        is_limit_mode=True,
                        limit_min_warning=-10,
                        limit_min_error=-20,
                        limit_max_warning=50,
                        limit_max_error=60)
        csr.add_channel(name="Temperatur Abluft",
                        value=sensor_data[SENSOR_TEMPERATURE_EXTRACT]/10,
                        is_float=True,
                        unit=ValueUnit.TEMPERATURE,
                        is_limit_mode=True,
                        limit_min_warning=-10,
                        limit_min_error=-20,
                        limit_max_warning=50,
                        limit_max_error=60)
        csr.add_channel(name="Temperatur Fortluft",
                        value=sensor_data[SENSOR_TEMPERATURE_EXHAUST]/10,
                        is_float=True,
                        unit=ValueUnit.TEMPERATURE,
                        is_limit_mode=True,
                        limit_min_warning=-10,
                        limit_min_error=-20,
                        limit_max_warning=50,
                        limit_max_error=60)
        csr.add_channel(name="Temperatur Außenluft",
                        value=sensor_data[SENSOR_TEMPERATURE_OUTDOOR]/10,
                        is_float=True,
                        unit=ValueUnit.TEMPERATURE,
                        is_limit_mode=True,
                        limit_min_warning=-10,
                        limit_min_error=-20,
                        limit_max_warning=50,
                        limit_max_error=60)
        csr.add_channel(name="Feuchtigkeit Abluft",
                        value=sensor_data[SENSOR_HUMIDITY_EXTRACT],
                        unit=ValueUnit.PERCENT,
                        is_limit_mode=True,
                        limit_min_warning=30,
                        limit_min_error=20,
                        limit_max_warning=60,
                        limit_max_error=70)
        csr.add_channel(name="Feuchtigkeit Fortluft",
                        value=sensor_data[SENSOR_HUMIDITY_EXHAUST],
                        unit=ValueUnit.PERCENT)
        csr.add_channel(name="Feuchtigkeit Außenluft",
                        value=sensor_data[SENSOR_HUMIDITY_OUTDOOR],
                        unit=ValueUnit.PERCENT)                        
        csr.add_channel(name="Feuchtigkeit Zuluft",
                        value=sensor_data[SENSOR_HUMIDITY_SUPPLY],
                        unit=ValueUnit.PERCENT)                               

        print(csr.json_result)
    except Exception as e:
        csr = CustomSensorResult(text="Python Script execution error")
        csr.error = "Python Script execution error: %s" % str(e)
        print(csr.json_result)
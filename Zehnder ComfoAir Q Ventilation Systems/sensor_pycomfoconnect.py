# -*- coding: utf-8 -*-

import json
import sys
import argparse

from prtg.sensor.result import CustomSensorResult
from prtg.sensor.units import ValueUnit

from pycomfoconnect import *

local_name = 'PRTG'
local_uuid = bytes.fromhex('00000000000000000000000000000005')

sensor_data = {
    56: "",
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


def extract_pin(data):
    if not data["params"]:
        raise Exception("""
        No PIN as parameter defined!
        Make sure to pass arguments in sensor settings in following format:
        "<pin>". E.g: "9432"
        """)
    pin = data["params"].split(" ")[0]
    return pin
    

def set_ventilation_stage_message(ventilation_stage): 
    msg = ""
    if ventilation_stage == 0:
        msg = "Außer Haus"
    elif ventilation_stage in (1, 2, 3): 
        msg = f"Lüftungsstufe: {ventilation_stage}"
    return msg


def set_operation_message(operation): 
    msg = ""
    if operation == -1:
        msg = "Betrieb: Automatik"
    elif operation == 1:
        msg = "Betrieb: Manuell"
    return msg


def set_status_message(operation, ventilation_stage): 
    ventilation_stage_msg = set_ventilation_stage_message(ventilation_stage)
    operation_msg = set_operation_message(operation)
    msg = f"{operation_msg} | {ventilation_stage_msg}"
    return msg


if __name__ == "__main__":
    try:
        data = json.loads(sys.argv[1])
        
        comfoconnect_ip = data["host"] # Automatically read from it's device IP
        comfoconnect_pin = extract_pin(data) # Pin needs to be defined in sensor settings: "Additonal parameters: <pin>", default is 0
        
        # Gets all the data
        run_comfoconnect_handler(comfoconnect_ip, comfoconnect_pin) 
        
        # Status Message is depending on the values of the operation and ventilation stage sensors
        csr = CustomSensorResult(text=f"{set_status_message(sensor_data[56], sensor_data[SENSOR_FAN_SPEED_MODE])}")

        csr.add_channel(name="Betriebsmodus",
                        value=sensor_data[56],
                        unit="Modus")    
        
        csr.add_channel(name="Lüftungsstufe",
                        value=sensor_data[SENSOR_FAN_SPEED_MODE],
                        unit="Stufe",
                        is_limit_mode=True,
                        limit_min_warning=-0.1,
                        limit_max_warning=3.1)  
        
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
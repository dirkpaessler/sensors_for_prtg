# TP-Link Wi-Fi Smart Plug Protocol Client Sensor for PRTG
# For use with TP-Link HS-110 and PRTG
#
#
# COPY OF ORIGINAL CODE LICENCE
# Copyright 2016 softScheck GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import socket
import json
from struct import pack
from prtg.sensor.result import CustomSensorResult
from prtg.sensor.units import ValueUnit

# Predefined Smart Plug Commands
commands = {
    'info': '{"system":{"get_sysinfo":{}}}',
    'energy': '{"emeter":{"get_realtime":{}}}'
}


# Easy handler class for the Smart Plug connection
# Stores a single connection configuration of a Smart Plug for sending requests
class SmartPlugHandler():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    # Encryption and Decryption of TP-Link Smart Home Protocol
    # XOR Autokey Cipher with starting key = 171
    def _encrypt(self, string):
        key = 171
        result = pack('>I', len(string))
        for i in string:
            a = key ^ ord(i)
            key = a
            result += bytes([a])
        return result

    def _decrypt(self, string):
        key = 171
        result = ""
        for i in string:
            a = key ^ i
            key = i
            result += chr(a)
        return result

    # Set target IP, port and command to send
    # And Send command and receive reply
    def _send_command_and_get_reply(self, command):
        try:
            cmd = commands[command]
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.ip, self.port))
            sock_tcp.settimeout(None)
            sock_tcp.send(self._encrypt(cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            decrypted = self._decrypt(data[4:])

            return decrypted

        except socket.error:
            quit(f"Could not connect to host {self.ip}: {str(self.port)}")

    # Sends request to smart plug to get power consumption and converts it to percent
    def get_relay_state(self):
        return_message = json.loads(
            self._send_command_and_get_reply('info'))
        return int(return_message['system']['get_sysinfo']['relay_state'])*100

    # Sends request to smart plug to get power consumption of smart plug and converts it to wattage
    def get_wattage_consumption(self):
        return_message = json.loads(
            self._send_command_and_get_reply('energy'))
        return int(return_message['emeter']['get_realtime']['power_mw'])/1000


if __name__ == "__main__":
    try:
        data = json.loads(sys.argv[1])

        # Setup the handler class for the smartplug connection
        sp_handler = SmartPlugHandler(data["host"], 9999)
        # Sends request to get the wattage consumption of the plug
        wattage_consumption = sp_handler.get_wattage_consumption()
        # Sends request to get the relay state of the plug
        relay_state = sp_handler.get_relay_state()

        csr = CustomSensorResult(text="This sensor runs on %s" % data["host"])

        csr.add_primary_channel(name="Power Usage",
                                value=wattage_consumption,
                                unit="Watt",
                                is_float=True)

        csr.add_channel(name="Power State",
                        value=relay_state,
                        unit=ValueUnit.PERCENT)

        print(csr.json_result)
    except Exception as e:
        csr = CustomSensorResult(text="Python Script execution error")
        csr.error = "Python Script execution error: %s" % str(e)
        print(csr.json_result)

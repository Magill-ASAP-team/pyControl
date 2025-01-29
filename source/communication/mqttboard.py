# this is a virtual board to communicate with a MQTT broker
# it provide the same interface
import os
import re
import time
import json
import inspect
from serial import SerialException
from array import array
from .pyboard import Pyboard, PyboardError
from .data_logger import Data_logger
from .message import MsgType, Datatuple
from source.gui.settings import VERSION, user_folder
from source.communication.pycboard import State_machine_info
from dataclasses import dataclass
import paho.mqtt.client as mqtt


# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------


class MqttBoard:
    """Pycontrol board inherits from Pyboard and adds functionality for file transfer
    and pyControl operations.
    """

    def __init__(self, verbose=True, print_func=print, data_consumers=None):

        self.print = print_func  # Function used for print statements.
        self.print('starting mqtt')
        self.data_logger = Data_logger(board=self, print_func=print_func)
        self.data_consumers = data_consumers
        self.status = {"serial": '', "framework": True, "usb_mode": ''}
        
        self.reset()
        self.unique_ID = 'mqtt'


        # MQTT settings
        self.broker_address = "broker.emqx.io"
        self.broker_port = 1883
        self.topic = "teris/topic"

        # MQTT client setup
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set('emqx','public')
        

        def on_connect(client, userdata, flags, rc, properties):
            self.print(f"Connected to MQTT broker with result code {rc}")
            self.client.subscribe(self.topic)
        
        def on_message(client, userdata, msg:mqtt.MQTTMessage):
            self.print(f"Message received: {msg.topic} {msg.payload.decode()}")

            # inject the message to the event queue
            new_data = []
            msg_json = json.loads(msg.payload.decode())
            new_data.append(Datatuple(time=msg_json['time'], type=MsgType(msg_json['type'].encode()), subtype=msg_json['subtype'], content=msg_json['content']))
            
            self.data_logger.process_data(new_data)
            if self.data_consumers:
                #that's where the plotting is done
                for data_consumer in self.data_consumers:
                    data_consumer.process_data(new_data)

        self.client.on_connect = on_connect
        self.client.on_message = on_message

        # Connect to the broker
        self.print('Now connecting to MQTT broker')
        try:
            self.client.connect(self.broker_address, self.broker_port, 60)
            self.client.loop_start()
        except mqtt.Error as e:
            self.print(f"Connection failed: {e}")
            time.sleep(5)

        self.print('MQTT connected')



   

    def reset(self):
        """Enter raw repl (soft reboots pyboard), import modules."""

        self.framework_version = '2.0'
        self.micropython_version = '2.0'

        self.framework_running = False
        self.data_logger.reset()


    def hard_reset(self, reconnect=True):
        pass

    def gc_collect(self):
        pass

    def DFU_mode(self):
        pass

    def disable_mass_storage(self):
        pass

    def enable_mass_storage(self):
        pass
    # ------------------------------------------------------------------------------------
    # Pyboard filesystem operations.
    # ------------------------------------------------------------------------------------

    def write_file(self, target_path, data):
        pass

    def get_file_hash(self, target_path):
        return -1

    def transfer_file(self, file_path, target_path=None):
        pass

    def transfer_folder(
        self, folder_path, target_folder=None, file_type="all", files="all", remove_files=True, show_progress=False
    ):
        pass

    def remove_file(self, file_path):
        pass

    def get_folder_contents(self, folder_path, get_hash=False):
        return [] if not get_hash else {}

    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def load_framework(self):
        """Copy the pyControl framework folder to the board, reset the devices folder
        on pyboard by removing all devices files, and rebuild the device_class2file dict."""
        return

    def load_hardware_definition(self, hwd_path):
        """Transfer a hardware definition file to pyboard."""
        return

    def transfer_device_files(self, ref_file_path):
        """Transfer device driver files defining classes used in ref_file to the pyboard devices folder.
        Driver file that are already on the pyboard are only transferred if they have changed
        on the computer."""
        return

    def _get_used_device_files(self, ref_file_path):
        """Return a list of device driver file names containing device classes used in ref_file"""
        return []

    def make_device_class2file_map(self):
        """Make dict mapping device class names to file in devices folder containing
        the class definition."""
        return

    def setup_state_machine(self, sm_name, sm_dir=None, uploaded=False):
        """Transfer state machine descriptor file sm_name.py from folder sm_dir
        to board and setup state machine on pyboard."""
        states = self.get_states()
        events = self.get_events()

        self.sm_info = State_machine_info(
            name=sm_name,
            task_hash= 'hash',
            states=states,  # {name:ID}
            events=events,  # {name:ID}
            ID2name={ID: name for name, ID in {**states, **events}.items()},  # {ID:name}
            analog_inputs=self.get_analog_inputs(),  # {ID: {'name':, 'fs':, 'dtype': 'plot':}}
            variables=self.get_variables(),
            framework_version=self.framework_version,
            micropython_version=self.micropython_version,
        )
        self.data_logger.reset()
        self.timestamp = 0
        return

    def get_states(self):
        """Return states as a dictionary {state_name: state_ID}"""
        return {'cue':0,'break_after_trial':1}

    def get_events(self):
        """Return events as a dictionary {event_name: state_ID}"""
        return {'spout':0}

    def get_analog_inputs(self):
        """Return analog_inputs as a dictionary: {ID: {'name':, 'fs':, 'dtype': 'plot':}}"""
        return {}

    def start_framework(self, data_output=True):
        """Start pyControl framwork running on pyboard."""
        self.framework_running = True

    def stop_framework(self):
        """Stop framework running on pyboard by sending stop command."""
        self.framework_running = False

    def process_data(self):
        """Read data from serial line, generate list new_data of data tuples,
        pass new_data to data_logger and print_func if specified, return new_data."""
        # self.client.loop()
        pass
       

    def trigger_event(self, event_name, source="u"):
        """Trigger specified task event on the pyboard."""
        pass

    def get_timestamp(self):
        """Get the current pyControl timestamp in ms since start of framework run."""
        seconds_elapsed = time.time() - self.last_message_time
        return self.timestamp + round(1000 * (seconds_elapsed))

    def send_serial_data(self, data, command, cmd_type=""):
        """Send data to the pyboard while framework is running."""
        pass

    # ------------------------------------------------------------------------------------
    # Getting and setting variables.
    # ------------------------------------------------------------------------------------

    def set_variable(self, v_name, v_value, source="s"):
        """Set the value of a state machine variable. If framework is not running
        returns True if variable set OK, False if set failed.  Returns None framework
        running, but variable event is later output by board."""
        pass

    def get_variable(self, v_name):
        """Get the value of a state machine variable. If framework not running returns
        variable value if got OK, None if get fails.  Returns None if framework
        running, but variable event is later output by board."""
        pass

    def get_variables(self):
        """Return variables as a dictionary {v_name: v_value}"""
        return {}
    
    def close(self):
        pass
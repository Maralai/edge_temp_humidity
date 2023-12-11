import json
import threading
import time
from gpio_device import GpioDevice
import os
import logging

from logging_utils import configure_logging
configure_logging()

def load_profiles(filename):
    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Profile file {filename} not found.", exc_info=True)
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {filename}.", exc_info=True)
    except Exception as e:
        logging.error(f"Unexpected error loading profiles: {e}", exc_info=True)
    return {}

profiles = load_profiles('./config/buzzer_profiles.json')
options_list = [profile['name'] for profile in profiles]

class Buzzer(GpioDevice):
    def __init__(self, mqtt_client, config):
        logging.info(f"Initializing Buzzer")
        self.buzzer_pin = None
        self.interrupted = True

        # Add the options list to the profile
        config['buzzer_profile']['ha_discovery_payload']['options'] = options_list

        # Set the current profile to the first profile in the list
        self.current_profile = profiles[0]
        super().__init__(mqtt_client, config)
        self.GPIO.output(self.buzzer_pin, self.GPIO.LOW)

    def setup_gpio(self):
        try:
            self.buzzer_pin = int(os.getenv('BUZZER_PIN'))
            self.GPIO.setup(self.buzzer_pin, self.GPIO.OUT)
        except Exception as e:
            logging.error(f"General error in GPIO setup: {e}")

    def subscribe_to_command_topic(self):
        # Return the switch command topic from the config
        switch_command_topic = self.config['buzzer_switch']['ha_discovery_payload']['command_topic']
        self.mqtt_client.subscribe(switch_command_topic)
        logging.debug(f"Subscribed to switch command topic: {switch_command_topic}")
        # Return profile the command topic from the config
        profile_command_topic = self.config['buzzer_profile']['ha_discovery_payload']['command_topic']
        self.mqtt_client.subscribe(profile_command_topic)
        logging.debug(f"Subscribed to profile command topic: {profile_command_topic}")

    def register_homeassistant(self):
        # setup the switch
        switch_discovery_topic = self.config['buzzer_switch']["ha_discovery_topic"]
        switch_discovery_payload = json.dumps(self.config['buzzer_switch']["ha_discovery_payload"])
        self.mqtt_client.publish(switch_discovery_topic, switch_discovery_payload, retain=True)
        
        # setup the profile
        profile_discovery_topic = self.config['buzzer_profile']["ha_discovery_topic"]
        profile_discovery_payload = json.dumps(self.config['buzzer_profile']["ha_discovery_payload"])
        self.mqtt_client.publish(profile_discovery_topic, profile_discovery_payload, retain=True)

        logging.debug(f"Registered Buzzer switch and profile to Home Assistant")
        self.publish_state()
        
    def on_message(self, topic, payload):
        logging.debug(f"Processing MQTT message on topic {topic}")
        if topic.startswith('tower/select/') and topic.endswith('/set'):
            self.set_profile(payload)
        elif topic.startswith('tower/switch') and topic.endswith('/set'):
            if payload == 'OFF':
                self.interrupt()
            elif payload == 'ON':
                logging.info(f"Received message: {payload} on topic {topic}")
                self.execute_profile(self.current_profile)
        self.publish_state()

    def set_profile(self, profile_name):
        profile = [profile for profile in profiles if profile['name'] == profile_name]
        if len(profile) > 0:
            self.current_profile = profile[0]
            logging.info(f"Set profile to {profile_name}")
        else:
            logging.error(f"Unknown profile: {profile_name}")

    def execute_profile_thread(self, profile):
        logging.info(f"Thread started for executing profile: {profile['name']}")
        try:            
            self.interrupted = False
            repeat = int(profile['repeat']) if profile['repeat'] != '~' else 1
            delay_start = int(profile['delay_start'])
            delay_end = int(profile['delay_end'])
            pattern = profile['pattern']

            logging.debug(f"Executing profile {profile['name']} with {profile['repeat']} repeats, {delay_start}ms delay start, {delay_end}ms delay end")

            time.sleep(delay_start / 1000)  # Convert ms to seconds for sleep
            while repeat > 0:
                if self.interrupted:
                    break
                for state, duration in pattern:
                    if self.interrupted:
                        break
                    logging.debug(f"Setting buzzer to {state} for {duration}ms")
                    self.GPIO.output(self.buzzer_pin, self.GPIO.HIGH if state == 'ON' else self.GPIO.LOW)
                    time.sleep(duration / 1000)  # Convert ms to seconds for sleep
                if profile['repeat'] != '~':
                    repeat -= 1
                time.sleep(delay_end / 1000)  # Convert ms to seconds for sleep
            # Turn off the buzzer, we have finished.
            self.interrupted = True
            self.GPIO.output(self.buzzer_pin, self.GPIO.LOW)
            logging.info(f"Finished executing profile {profile['name']}")
            self.publish_state()
        except Exception as e:
            logging.error(f"Unexpected error in execute_profile_thread: {e}")
        finally:
            self.interrupt()

    def execute_profile(self, profile):
        thread = threading.Thread(target=self.execute_profile_thread, args=(profile,))
        thread.start()

    def interrupt(self):
        self.interrupted = True

    def publish_state(self):
        switch_topic = self.config['buzzer_switch']['ha_discovery_payload']['state_topic']
        buzzer_topic = self.config['buzzer_profile']['ha_discovery_payload']['state_topic']
        if self.interrupted:
            self.mqtt_client.publish(switch_topic, 'OFF', retain=True)
        else:
            self.mqtt_client.publish(switch_topic, 'ON', retain=True)
        self.mqtt_client.publish(buzzer_topic, self.current_profile['name'], retain=True)
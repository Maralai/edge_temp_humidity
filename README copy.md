# Tower Light and Buzzer

## Overview

This project offers a versatile IoT solution, designed to control GPIO devices across various Jetson platforms or Raspberry Pi. It employs MQTT for communication, enabling it to integrate with systems like Home Assistant for home automation, although it's not strictly bound to such integrations. This plugin focuses on managing devices like Tower Lights and Buzzers, responding to MQTT commands and updating their states accordingly.

## Directory Structure

```
./
    __init__.py
    .gitignore
    docker-compose.yaml
    README.md
    build/
        Dockerfile
        requirements.txt
    worker/
        __init__.py
        device_manager.py
        gpio_device.py
        gpio_handler.py
        logging_utils.py
        mqtt_client_wrapper.py
        tower_buzzer.py
        tower_light.py
        worker.py
        config/
            mqtt_topics.json
            buzzer_profiles.json
```

## Key Components

- **Docker Setup**: `docker-compose.yaml` and `Dockerfile` in the `build` directory facilitate containerized deployment.
- **MQTT Client Wrapper**: Implements `paho-mqtt` for robust MQTT communications.
- **Device Manager**: Responsible for configuring a variety of GPIO devices like Tower Lights and Buzzers, orchestrating their interactions and responses.
- **GPIO Device Abstractions**: `GpioDevice` offers a base class for device inheritance and `GpioHandler` abstracts the GPIO configuration to support interfaces for Jetson or Raspberry Pi GPIO control and operations.
- **Tower Light & Buzzer Implementations**: These classes interpret MQTT messages to manipulate the respective GPIO devices.
- **Configuration Management**: Device behaviors and MQTT topics are configurable via JSON files in the `config` directory, are initialized by the `DeviceManager`, and are used by the `GpioDevice` implementations.
- **Worker Script**: `worker.py` initializes and manages the MQTT client and device manager, handling incoming MQTT messages and device state updates.

## Requirements and Setup

- **Dependencies**: See `./build/requirements.txt`.
- **Environment Setup**: An `.env` file is necessary to define environment variables such as log level, platform type, device pin configurations, MQTT server details, and time zone. An example `.env` file is provided below.

    ### Example .env File

    ```env
    # Logging configuration
    LOG_LEVEL = DEBUG

    # Specify platform as 'jetson' or 'rpi'
    PLATFORM = 'jetson'

    # Worker configuration
    YELLOW_PIN = 13
    RED_PIN = 18
    GREEN_PIN = 11
    BUZZER_PIN = 15

    DEVICE_ID = 'jn003'

    # Time zone setting
    TZ = America/Indiana/Indianapolis

    # MQTT server configuration
    MQTT_SERVER = server.lan
    MQTT_USERNAME = [username]
    MQTT_PASSWORD = [password]
    ```
- **Running the Worker**: Execute `worker.py` to start the system. It sets up MQTT communication and manages device configurations.
- **Customization**: Adjust `mqtt_topics.json` and `buzzer_profiles.json` in the `config` directory for specific device behaviors and MQTT topic management.

## Integration with Home Assistant

The system can integrate with Home Assistant through MQTT Discovery but also functions independently, offering flexibility for various automation setups.

## Logging

Logging throughout the plugin is managed via `logging_utils.py`, and the level of detail is configurable through the `.env` file.

## Future Enhancements

- Expanding support for additional IoT platforms.
- Adding support for additional GPIO devices.
- Developing a more dynamic configuration system for adding new devices.

## Notes

- Initialization with either Jetson and Raspberry Pi platforms is determined by the `PLATFORM` variable in the `.env` file.
- Adjust the Dockerfile and docker-compose.yaml as needed to align with your deployment environment. 
- Include this plugin in a larger Docker setup or deploy it as a standalone container.
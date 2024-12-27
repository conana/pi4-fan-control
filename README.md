# Raspberry Pi 4 Fan Controller

This project provides a smart PWM-based fan controller for the Raspberry Pi 4. It automatically adjusts the fan speed based on CPU temperature, using smooth transitions to minimize sudden changes in fan noise.

## Features

- Smooth PWM-based fan speed control
- Configurable temperature thresholds
- Automatic startup as a system service
- System logging via syslog
- Configurable via JSON file

## Hardware Requirements

- Raspberry Pi 4
- PWM-capable fan connected to GPIO 14 (Pin 8)

## Installation

1. Install pre-requisites:
   ```bash
   sudo apt update
   sudo apt install git python3-pip python3-venv
   ```
1. Create the installation directory and install files:
   ```bash
   # Create directory with root, then set ownership
   sudo mkdir -p /opt/pi4-fan
   sudo chown $USER:$USER /opt/pi4-fan
   
   cd /opt/pi4-fan
   git clone https://github.com/conana/pi4-fan.git .
   ```
1. Set up Python virtual environment:
   ```bash
   python3 -m venv pi4-fan-env
   source pi4-fan-env/bin/activate
   pip3 install -r requirements.txt
   deactivate
   ```
1. Add your user to the gpio group (needed for interactive use):
   ```bash
   sudo usermod -a -G gpio $USER
   # Log out and back in for the group change to take effect
   ```
1. Install the service:
   ```bash
   sudo cp fan_controller.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable fan_controller
   sudo systemctl start fan_controller
   ```

## Running Interactively
   
Instead of running as a service, you can run the fan controller interactively for testing or debugging:

```bash
# Activate the virtual environment
source /opt/pi4-fan/pi4-fan-env/bin/activate

# Run with sudo while preserving the virtual environment
sudo --preserve-env=PATH,VIRTUAL_ENV python3 fan_controller.py
```

The controller will show temperature and fan speed updates in real-time. Press Ctrl+C to stop.

When done testing, deactivate the virtual environment:
```bash
deactivate
```

## Configuration

Edit `/opt/pi4-fan/config.json` to customize the controller behavior:

```json
{
    "fan_pin": 14,          // GPIO pin number
    "temp_lower": 45,       // Temperature in °C below which fan is off
    "temp_upper": 75,       // Temperature in °C at which fan runs at 100%
    "pwm_frequency": 100,   // PWM frequency in Hz
    "update_interval": 2,   // How often to update fan speed (seconds)
    "smoothing_factor": 0.1 // How smooth the transitions should be (0-1)
}
```

## Monitoring

Check the service status:
```bash
sudo systemctl status fan_controller
```

View the logs:
```bash
# View all logs
sudo journalctl -u fan_controller

# Follow new log entries
sudo journalctl -u fan_controller -f

# View logs since last boot
sudo journalctl -u fan_controller -b
```

## Stopping/Starting

```bash
sudo systemctl stop fan_controller    # Stop the service
sudo systemctl start fan_controller   # Start the service
sudo systemctl restart fan_controller # Restart the service

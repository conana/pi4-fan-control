#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import signal
import sys
import logging
import logging.handlers
import json
import os

class FanController:
    def __init__(self, config_path='/opt/pi4-fan/config.json'):
        # Default configuration
        self.default_config = {
            'fan_pin': 14,  # GPIO 14 (Pin 8)
            'temp_lower': 45,  # °C
            'temp_upper': 75,  # °C
            'pwm_frequency': 100,  # Hz
            'update_interval': 2,  # seconds
            'smoothing_factor': 0.1  # How quickly to adjust (0-1, lower = smoother)
        }
        
        self.config = self.load_config(config_path)
        self.current_duty_cycle = 0
        self.setup_logging()
        self.setup_gpio()
        self.setup_signal_handlers()

    def setup_logging(self):
        self.logger = logging.getLogger('pi4-fan')
        self.logger.setLevel(logging.INFO)
        
        # Determine if running interactively
        is_interactive = sys.stdout.isatty()
        
        if is_interactive:
            # Use console logging for interactive mode
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        else:
            # Use syslog for service mode
            handler = logging.handlers.SysLogHandler(address='/dev/log', facility=logging.handlers.SysLogHandler.LOG_DAEMON)
            formatter = logging.Formatter('pi4-fan[%(process)d]: %(levelname)s - %(message)s')
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing values
                return {**self.default_config, **config}
        except FileNotFoundError:
            # If config file doesn't exist, create it with defaults
            with open(config_path, 'w') as f:
                json.dump(self.default_config, f, indent=4)
            return self.default_config

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.config['fan_pin'], GPIO.OUT)
        self.pwm = GPIO.PWM(self.config['fan_pin'], self.config['pwm_frequency'])
        self.pwm.start(0)
        self.logger.info("GPIO initialized")

    def setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self.cleanup)
        signal.signal(signal.SIGINT, self.cleanup)

    def get_cpu_temperature(self):
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
            return temp
        except Exception as e:
            self.logger.error(f"Error reading temperature: {e}")
            return 0

    def calculate_target_duty_cycle(self, temperature):
        if temperature <= self.config['temp_lower']:
            return 0
        elif temperature >= self.config['temp_upper']:
            return 100
        else:
            # Linear interpolation between lower and upper limits
            temp_range = self.config['temp_upper'] - self.config['temp_lower']
            temp_above_min = temperature - self.config['temp_lower']
            return (temp_above_min / temp_range) * 100

    def adjust_fan_speed(self, target_duty_cycle):
        # Smooth the transition using exponential moving average
        diff = target_duty_cycle - self.current_duty_cycle
        self.current_duty_cycle += diff * self.config['smoothing_factor']
        
        # Ensure duty cycle is between 0 and 100
        self.current_duty_cycle = max(0, min(100, self.current_duty_cycle))
        
        self.pwm.ChangeDutyCycle(self.current_duty_cycle)
        return self.current_duty_cycle

    def cleanup(self, signum=None, frame=None):
        self.logger.info("Cleaning up GPIO")
        self.pwm.stop()
        GPIO.cleanup()
        sys.exit(0)

    def run(self):
        self.logger.info("Fan controller started")
        try:
            while True:
                temp = self.get_cpu_temperature()
                target_duty = self.calculate_target_duty_cycle(temp)
                actual_duty = self.adjust_fan_speed(target_duty)
                
                self.logger.info(f"Temp: {temp:.1f}°C, Target PWM: {target_duty:.1f}%, Actual PWM: {actual_duty:.1f}%")
                time.sleep(self.config['update_interval'])
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.cleanup()

if __name__ == "__main__":
    controller = FanController()
    controller.run()

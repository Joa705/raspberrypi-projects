"""
Heat Sensor Module

This module contains heat sensor hardware interaction logic.
It uses mock implementations to be safe on non-Raspberry Pi systems.
Replace with actual sensor library calls when deployed on hardware.
"""

import logging
import random
import time
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class HeatSensor:
    """
    Heat sensor hardware interface.
    
    This is a mock implementation that generates random temperature readings.
    Replace with actual sensor code (DHT22, DS18B20, etc.) when running on
    a Raspberry Pi with a temperature sensor.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.base_temperature = 22.0  # Mock baseline temperature in Celsius
        self._initialize()
    
    def _initialize(self):
        """
        Initialize the heat sensor hardware.
        """
        try:
            # Mock initialization
            # In real implementation, this would initialize GPIO and sensor
            logger.info("[MOCK] Initializing heat sensor...")
            time.sleep(0.05)  # Simulate initialization delay
            self.is_initialized = True
            logger.info("[MOCK] Heat sensor initialized successfully")
        except Exception as e:
            logger.error(f"[MOCK] Heat sensor initialization failed: {e}")
            self.is_initialized = False
    
    def read_temperature(self) -> Optional[float]:
        """
        Read temperature from the sensor.
        
        Returns:
            Optional[float]: Temperature in Celsius, or None if read failed
        """
        if not self.is_initialized:
            logger.warning("[MOCK] Heat sensor not initialized")
            return None
        
        try:
            # Mock temperature reading with some variation
            # Real implementation would read from actual sensor
            variation = random.uniform(-2.0, 2.0)
            temperature = self.base_temperature + variation
            
            logger.debug(f"[MOCK] Temperature reading: {temperature:.1f}°C")
            return round(temperature, 1)
            
        except Exception as e:
            logger.error(f"[MOCK] Temperature read failed: {e}")
            return None
    
    def read_humidity(self) -> Optional[float]:
        """
        Read humidity from the sensor (if supported).
        
        Returns:
            Optional[float]: Humidity percentage, or None if not supported/failed
        """
        if not self.is_initialized:
            return None
        
        try:
            # Mock humidity reading
            # Some sensors like DHT22 provide both temperature and humidity
            humidity = random.uniform(40.0, 60.0)
            logger.debug(f"[MOCK] Humidity reading: {humidity:.1f}%")
            return round(humidity, 1)
            
        except Exception as e:
            logger.error(f"[MOCK] Humidity read failed: {e}")
            return None
    
    def get_reading(self) -> Dict:
        """
        Get a complete sensor reading with temperature and humidity.
        
        Returns:
            Dict: Dictionary containing temperature, humidity, and timestamp
        """
        temperature = self.read_temperature()
        humidity = self.read_humidity()
        
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        return {
            "temperature_celsius": temperature,
            "humidity_percent": humidity,
            "timestamp": timestamp,
            "status": "success" if temperature is not None else "error"
        }
    
    def cleanup(self):
        """
        Clean up sensor resources.
        """
        logger.info("[MOCK] Cleaning up heat sensor resources...")
        self.is_initialized = False

from connections import connect_mqtt, connect_internet
from time import sleep
from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import framebuf
import time
import dht
import json


# Display setup
WIDTH = 128
HEIGHT = 64
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)
display = SSD1306_I2C(128, 64, i2c)

# Sensor setup
d = dht.DHT11(Pin(26))  # DHT11 sensor
ldr = ADC(27)  # Photoresistor
trigger = Pin(14, Pin.OUT)  # Ultrasonic trigger
echo = Pin(15, Pin.IN)  # Ultrasonic echo

# Connection status
wifi_connected = False
MQTT_connected = False

def updateDisplay(sensor_data=None):
    display.fill(0)  # Clear display
    
    # WiFi Status
    if wifi_connected:
        display.text("WiFi: Connected", 0, 0)
    else:
        display.text("WiFi: Disconnected", 0, 0)
    
    # MQTT Status
    if MQTT_connected:
        display.text("MQTT: Connected", 0, 10)
    else:
        display.text("MQTT: Disconnected", 0, 10)
    
    # Display sensor data if available
    if sensor_data:
        display.text(f"T:{sensor_data['temp_f']:.1f}F", 0, 20)
        display.text(f"H:{sensor_data['humidity']:.1f}%", 0, 30)
        display.text(f"L:{sensor_data['lumens']:.1f}", 0, 40)
        display.text(f"D:{sensor_data['distance']:.1f}cm", 0, 50)
    
    display.show()

def read_internal_temp():
    """Read Pico's internal temperature sensor"""
    sensor_temp = ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature

def read_dht():
    """Read DHT11 temperature and humidity"""
    try:
        d.measure()
        temperature_c = d.temperature()
        temp_f = temperature_c * 9/5 + 32  # Convert to Fahrenheit
        humidity = d.humidity()
        return temp_f, humidity
    except:
        print("DHT11 read error")
        return None, None

def read_ldr():
    """Read photoresistor and convert to lumens"""
    ldr_value = ldr.read_u16()
    lumens = (19/1224000) * ldr_value - (361/6120)
    return ldr_value, lumens

def read_ultrasonic():
    """Read ultrasonic distance sensor"""
    try:
        trigger.low()
        time.sleep_us(2)
        trigger.high()
        time.sleep_us(5)
        trigger.low()
        
        # Timeout to prevent infinite loops
        timeout = time.ticks_us() + 30000  # 30ms timeout
        
        while echo.value() == 0:
            signaloff = time.ticks_us()
            if time.ticks_us() > timeout:
                return None
                
        while echo.value() == 1:
            signalon = time.ticks_us()
            if time.ticks_us() > timeout:
                return None
                
        timepassed = signalon - signaloff
        distance = (timepassed * 0.0343) / 2
        return distance
    except:
        print("Ultrasonic read error")
        return None

def read_all_sensors():
    """Read all sensors and return data dictionary"""
    # Read DHT11
    temp_f, humidity = read_dht()
    
    # Read photoresistor
    ldr_value, lumens = read_ldr()
    
    # Read ultrasonic
    distance = read_ultrasonic()
    
    # Read internal temperature as backup
    internal_temp = read_internal_temp()
    
    # Use DHT temp if available, otherwise internal temp
    final_temp = temp_f if temp_f is not None else internal_temp
    
    sensor_data = {
        "temp_f": final_temp,
        "temp_c": (final_temp - 32) * 5/9,
        "humidity": humidity if humidity is not None else 0,
        "ldr_value": ldr_value,
        "lumens": lumens,
        "distance": distance if distance is not None else 0,
        "internal_temp": internal_temp,
        "timestamp": time.ticks_ms()
    }
    
    return sensor_data

def sub_cp(topic, msg):
    """MQTT subscription callback"""
    print("Received:", msg.decode())
    display.fill(0)
    display.text("Msg received:", 0, 0)
    display.text(msg.decode(), 0, 40)
    display.show()
    time.sleep(2)  # Show message for 2 seconds

def main():
    global wifi_connected, MQTT_connected
    
    try:
        # Initial display update
        updateDisplay()
        
        # Connect to WiFi
        print("Connecting to WiFi...")
        connect_internet("HAcK-Project-WiFi-1", password="UCLA.HAcK.2024.Summer")
        wifi_connected = True
        updateDisplay()
        print("WiFi connected!")
        
        # Connect to MQTT
        print("Connecting to MQTT...")
        client = connect_mqtt("b8e39dde76a54dd58c34a907bd0c505c.s1.eu.hivemq.cloud", 
                             "OmarGarcia", "@5FWmr44-F")
        MQTT_connected = True
        updateDisplay()
        print("MQTT connected!")
        
        # Set up MQTT
        client.set_callback(sub_cp)
        client.connect()
        client.subscribe(b'display')
        
        print("Starting sensor loop...")
        
        while True:
            # Check for incoming MQTT messages
            client.check_msg()
            
            # Read all sensors
            sensor_data = read_all_sensors()
            
            # Print sensor data
            print("\n--- Sensor Readings ---")
            print(f"Temperature: {sensor_data['temp_f']:.1f}°F ({sensor_data['temp_c']:.1f}°C)")
            print(f"Humidity: {sensor_data['humidity']:.1f}%")
            print(f"LDR Value: {sensor_data['ldr_value']}")
            print(f"Lumens: {sensor_data['lumens']:.2f}")
            print(f"Distance: {sensor_data['distance']:.1f}cm")
            print(f"Internal Temp: {sensor_data['internal_temp']:.1f}°C")
            
            # Update display with sensor data
            updateDisplay(sensor_data)
            
            # Publish individual sensor topics
            client.publish(b'temp', f"{sensor_data['temp_f']:.1f}".encode())
            client.publish(b'humidity', f"{sensor_data['humidity']:.1f}".encode())
            client.publish(b'light', f"{sensor_data['lumens']:.2f}".encode())
            client.publish(b'ultrasonic', f"{sensor_data['distance']:.1f}".encode())
            
            # Publish all data as JSON
            json_data = json.dumps(sensor_data)
            client.publish(b'sensors/all', json_data.encode())
            
            # Wait before next reading
            sleep(2)
            
    except KeyboardInterrupt:
        print('Keyboard interrupt - stopping...')
        
    except Exception as e:
        print(f'Error: {e}')
        # Try to show error on display
        display.fill(0)
        display.text("Error occurred!", 0, 0)
        display.text(str(e)[:20], 0, 10)
        display.show()

if __name__ == "__main__":
    main()

from connections import connect_mqtt, connect_internet
from time import sleep
from machine import Pin, ADC
import framebuf
import time
import dht
import json
import dht

# Sensor setup
d = dht.DHT11(Pin(26))  # DHT11 sensor
ldr = ADC(27)  # Photoresistor
trigger = Pin(14, Pin.OUT)  # Ultrasonic trigger
echo = Pin(15, Pin.IN)  # Ultrasonic echo

# Connection status
wifi_connected = False
MQTT_connected = False

temp = "temp"
distance ="cm"
lumens = "lumens"
humidity = "humidity"

def ultra():
   trigger.low()
   time.sleep_us(2)
   trigger.high()
   time.sleep_us(5)
   trigger.low()
   while echo.value() == 0:
       signaloff = time.ticks_us()
   while echo.value() == 1:
       signalon = time.ticks_us()
   timepassed = signalon - signaloff
   distance = (timepassed * 0.0343) / 2 
   print("The distance from object is ",distance,"cm")

def updateDisplay(sensor_data=None):
    
    # WiFi Status
    if wifi_connected:
        print("wifi connected")
    else:
        print("wifi disconnected")
    
    # MQTT Status
    if MQTT_connected:
        print("MQTT connected")
    else:
        print("MQTT disconnected")

def sub_cp(topic, msg):
    """MQTT subscription callback"""
    print("Received:", msg.decode())
    display.fill(0)
    display.text("Msg received:", 0, 0)
    display.text(msg.decode(), 0, 40)
    display.show()
    time.sleep(2)  # Show message for 2 seconds

def main():
    global wifi_connected, MQTT_connected, temp, distance, humidity, lumens
    
    try:
        # Initial display update
        updateDisplay()
        
        # Connect to WiFi
        print("Connecting to WiFi...")
        connect_internet("bruins", password="connect12")
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
            
            d.measure()
            temperature_c = d.temperature()
            temp = str(temperature_c * 9/5 + 32 -8)  # Convert to Fahrenheit
            humidity = str(d.humidity() + 30)
           
            # Read photoresistor loop
            ldr_value = ldr.read_u16()  # Read the LDR value
            lumens = str((10/1224000) * ldr_value + (.45)) # Convert to lumens (example conversion factor)

            # Print outputs
            if humidity is not None and temperature_c is not None:
                print("Temperature:", temp, "degrees Fahrenheit")
                print("Humidity:", humidity, "%")

            print("LDR Value:", ldr_value)  # Print the LDR value to the console
            print("Lumens:", lumens)  # Print the lumens value
            # Read distance loop
            print("temp", temp)
            ultra()
            print("temp", temp)
            time.sleep(1)  # Sleep for a second before the next iteration
            # Publish individual sensor topics
            client.publish(b'temp', temp.encode())
            print("temp", temp)
            client.publish(b'distance', distance.encode())
            client.publish(b'lumens', lumens.encode())
            client.publish(b'humidity', humidity.encode())
            print("here")
            
            # Wait before next reading
            sleep(2)
            
    except KeyboardInterrupt:
        print('Keyboard interrupt - stopping...')
        
    except Exception as e:
        print(f'Error: {e}')
        # Try to show error on display

        print("Error occurred!", 0, 0)
        print(str(e)[:20], 0, 10)

if __name__ == "__main__":
    main()

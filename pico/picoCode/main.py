from connections import connect_mqtt, connect_internet
from time import sleep
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import framebuf
import time

WIDTH = 128
HEIGHT = 64


i2c = I2C(0, scl = Pin(17), sda = Pin(16), freq=400000)

display = SSD1306_I2C(128, 64, i2c)

wifi_connected=False
MQTT_connected=False

temp = "empty"
def updateDisplay():
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
    temp = read_temp()
    print("Publishing temperature:", temp)
    display.text(temp,0,20)
    
    display.show()

def read_temp():
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature = 27 - (reading - 0.706)/0.001721
    formatted_temperature = "{:.1f}".format(temperature)
    string_temperature = str("Temperature:" + formatted_temperature)
    print(string_temperature)
    time.sleep(2)
    return string_temperature

def sub_cp(topic,msg):
    print(msg.decode())
    display.fill(0)
    display.text(msg.decode(),0,30)
    display.show()
    
def main():
    global wifi_connected, MQTT_connected
    try:
        updateDisplay()
        connect_internet("HAcK-Project-WiFi-1",password="UCLA.HAcK.2024.Summer") #ssid (wifi name), pass
        wifi_connected = True
        updateDisplay()
        client = connect_mqtt("b8e39dde76a54dd58c34a907bd0c505c.s1.eu.hivemq.cloud", "OmarGarcia", "@5FWmr44-F") # url, user, pass
        MQTT_connected = True
        updateDisplay()
        client.set_callback(sub_cp)
        client.connect()
        client.subscribe(b'display')

        while True:
            client.check_msg()
            sleep(0.1)
            temp = read_temp()
            #print("Publishing temperature2:", temp)
            client.publish(b'temp', temp.encode())
    except KeyboardInterrupt:
        print('keyboard interrupt')
        
        
if __name__ == "__main__":
    main()


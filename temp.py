import dht
import machine
import time
d = dht.DHT11(machine.Pin(26))





while True:
    d.measure()
    temperature_c = d.temperature()
    temp = temperature_c * 9/5 + 32  # Convert to Fahrenheit
    humidity = d.humidity()
    if humidity is not None and temperature_c is not None:
        print("Temperature:", temp, "degrees Fahrenheit")
        print("Humidity:", humidity, "%")
        print("\n")   
    time.sleep(1)
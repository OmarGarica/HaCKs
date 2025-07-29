from machine import Pin
import time
import dht

# dht setup
d = dht.DHT11(Pin(26))

# photoresistor setup
ldr = machine.ADC(27)

# distance sensor setup
trigger = Pin(14, Pin.OUT)
echo = Pin(15, Pin.IN)
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

while True:
    # Read dht sensor loop
    d.measure()
    temperature_c = d.temperature()
    temp = temperature_c * 9/5 + 32 -8  # Convert to Fahrenheit
    humidity = d.humidity() + 30
   
    # Read photoresistor loop
    ldr_value = ldr.read_u16()  # Read the LDR value
    lumens = (10/1224000) * ldr_value + (.45) # Convert to lumens

    # Print outputs
    if humidity is not None and temperature_c is not None:
        print("Temperature:", temp, "degrees Fahrenheit")
        print("Humidity:", humidity, "%")

    print("LDR Value:", ldr_value)  # Print the LDR value to the console
    print("Lumens:", lumens)  # Print the lumens value
    # Read distance loop 
    ultra()
    time.sleep(1)  # Sleep for a second before the next iteration
    

       
from machine import Pin  
import time            
ldr = machine.ADC(27)  # Initialize an ADC object for pin 27
while True:
    ldr_value = ldr.read_u16()  # Read the LDR value and convert it to a 16-bit unsigned integer
    lumens = (10/1224000) * ldr_value + (.45) # Convert to lumens
    print("LDR Value:", ldr_value)  # Print the LDR value to the console
    print("Lumens:", lumens)  # Print the lumens value
    time.sleep(2)  

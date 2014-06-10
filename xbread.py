from xbee import XBee
import serial

ser = serial.Serial('/dev/tty.usbserial-FTE4XS76', 115200)

xbee = XBee(ser)

# Continuously read and print packets
while True:
    try:
        response = xbee.wait_read_frame()['rf_data']
        print response
    except KeyboardInterrupt:
        break
        
ser.close()

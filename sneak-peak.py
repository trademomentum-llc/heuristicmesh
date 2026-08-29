import struct
import serial
ser = serial.Serial('/dev/ttyUSB0', 921600)
while True:
    if ser.read(2) == b'\xAA\xBB':
        frame_idx = ser.read(1)[0]
        ts = struct.unpack('<Q', ser.read(8))[0]
        data = struct.unpack('<768f', ser.read(768*4))
        # data is now a numpy-ready tuple of 768 floats for that frame
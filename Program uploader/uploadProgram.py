import serial
import signal
import time

port = 'COM4'

ser = serial.Serial(port,115200,timeout=None)

def handler(signum, frame):
    exit()

signal.signal(signal.SIGINT, handler)

# Serial write section
with open('out.txt', 'r') as file:
    ser.flush()
    time.sleep(5)

    for line in file:
        print(line)
        ser.write(line[:-1].encode('UTF-8'))
        print(ser.readline().decode()[:-2])

print("Done Writing")

# Serial read section
ser.write("p 0 0fff".encode('UTF-8'))

msg = ""
while msg[:3] != 'END':
    msg = ser.readline()[:-2].decode('UTF-8')
    print(msg)

print("Done")

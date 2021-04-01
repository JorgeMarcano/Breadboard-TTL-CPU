import serial
import signal

port = 'COM4'

ser = serial.Serial(port,115200,timeout=None)

def handler(signum, frame):
    exit()

signal.signal(signal.SIGINT, handler)

#with open('file.bin', 'r') as file:
#while True:
# Serial write section
ser.flush()

ser.write(input().encode('UTF-8'))

# Serial read section
running = True
with open("received.txt", "w") as file:
    while running:
        msg = ser.readline()[:-2].decode('UTF-8')
        if (msg[:3] == "END"):
            running = False
        #print(msg)
        file.write(msg + "\n")

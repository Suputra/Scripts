import serial
import time
#example command: '20 090 090 090 090 090 073 '

if __name__ == '__main__':
    try:
        ser = serial.Serial('/dev/ttyACM0',9600, timeout=1)
    except FileNotFoundError:
        ser = serial.Serial('/dev/ttyACM1',9600, timeout=1)

    ser.flush()

    while True:
        #update values for servos and step delay
        step_delay = input('input step_delay: ')
        command = step_delay.strip() + ' '

        for i in range(6):
            sub_command = input('input servo ' + str(i+1) + ':').strip()
            sub_command = (3 - len(sub_command))*'0' + sub_command
            command = command + sub_command  + ' '

        ser.write(command.encode('ascii'))
        #print(command)
        command = ''

        #print(ser.readline().decode('ascii').strip())

import time
import threading
import serial

ser_data = ""


def read_ser_task():
    global ser_data
    while True:
        ser_data = ser.readline().decode().strip()
        print(f"> {ser_data}")
        time.sleep(0.1)


def open_serial_communication(com_port="COM6", baud_rate=9600):
    try:
        ser = serial.Serial(com_port, baud_rate)
        print("serial connection success!")
    except Exception as error:
        print(f"Error: {error}")
        exit(0)
    return ser


def set_button(n):
    ser.write("SetMode\n".encode())
    time.sleep(0.1)
    ser.write(f"selected button {n}\n".encode())


def free_send():
    threading.Thread(target=read_ser_task).start()
    while True:
        print("COMMAND LIST\n"
              "- SetMode\n"
              " * key *\n"
              "- StartRecord\n"
              "- StopRecord\n"
              "- StartStreaming\n"
              "- StopStreaming\n"
              "- ChangeScene\n"
              " * scene name *\n"
              "- SetInputVolume\n")
        ser.write(input().encode() + "\n".encode())


ser = open_serial_communication()
free_send()

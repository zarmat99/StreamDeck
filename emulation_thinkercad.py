import time
import serial
from selenium import webdriver

TIME = 30


def open_serial_communication(com_port="COM8", baud_rate=9600):
    try:
        ser = serial.Serial(com_port, baud_rate)
        print("serial connection success!")
    except Exception as error:
        print(f"Error: {error}")
        exit(0)
    return ser


with open("access_data.txt", 'r') as access_data:
    data = access_data.read().splitlines()
    username = data[0]
    password_user = data[1]
ser = open_serial_communication()
driver = webdriver.Edge()
driver.get("https://www.tinkercad.com/things/lkiSEeQDA52-mighty-hillar/editel?tenant=circuits")
driver.implicitly_wait(TIME)
signInPersonalAccounts = driver.find_element(by="id", value="signInPersonalAccounts")
signInPersonalAccounts.click()
driver.implicitly_wait(TIME)
autodeskProviderButton = driver.find_element(by="id", value="autodeskProviderButton")
autodeskProviderButton .click()
driver.implicitly_wait(TIME)
userName = driver.find_element(by="id", value="userName")
userName.send_keys(username)
driver.implicitly_wait(TIME)
verify_user_btn = driver.find_element(by="id", value="verify_user_btn")
verify_user_btn .click()
driver.implicitly_wait(TIME)
password = driver.find_element(by="id", value="password")
password.send_keys(password_user)
driver.implicitly_wait(TIME)
btnSubmit = driver.find_element(by="id", value="btnSubmit")
btnSubmit .click()
driver.implicitly_wait(TIME)
time.sleep(2)
CODE_EDITOR_ID = driver.find_element(by="id", value="CODE_EDITOR_ID")
CODE_EDITOR_ID .click()
driver.implicitly_wait(TIME)
time.sleep(2)
SIMULATION_ID = driver.find_element(by="id", value="SIMULATION_ID")
SIMULATION_ID .click()
driver.implicitly_wait(TIME)
time.sleep(2)
button_close = driver.find_element(by="class name", value="new-feature-details-toast-title-button-close")
button_close.click()
driver.implicitly_wait(TIME)
time.sleep(2)
decline = driver.find_element(by="id", value="adsk-eprivacy-privacy-decline-all-button")
decline.click()
driver.implicitly_wait(TIME)
time.sleep(2)
SERIAL_MONITOR_ID = driver.find_element(by="id", value="SERIAL_MONITOR_ID")
SERIAL_MONITOR_ID.click()
driver.implicitly_wait(TIME)
time.sleep(2)
monitor = driver.find_element(by="class name", value="code_panel__serial__top")
cancel = driver.find_element(by="link text", value="Canc")
lines_last_text = 0
while True:
    text = monitor.text
    lines_text = len(text.splitlines())
    if lines_text > 50:
        cancel.click()
    if lines_text != lines_last_text:
        lines = lines_text - lines_last_text
        last_lines = text.splitlines()[-lines:]
        for line in last_lines:
            print(line)
            ser.write(line.encode() + "\n".encode())
        last_text = text
        lines_last_text = len(last_text.splitlines())
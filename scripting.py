import time
import pyautogui
import json

pyautogui.PAUSE = 0.01
command_list = ["press", "hold", "release", "combo", "write", "delay"]

def save_scripts(scripts):
    with open('scripts.json', 'w') as file:
        json.dump(scripts, file)


def load_scripts():
    dictionary = {}
    try:
        with open("scripts.json", 'r') as file:
            dictionary = json.load(file)
    except FileNotFoundError:
        print(FileNotFoundError)
    return dictionary


def create_script(scripts):
    script = []
    command = ""
    name = input("name: ")
    while command != "exit":
        command = input("key: ")
        script.append(command)
    script.pop(-1)
    scripts[name] = script
    return scripts


def send_combo_command(command):
    command = command.split("$")
    for key in command:
        pyautogui.keyDown(key)
    for key in command:
        pyautogui.keyUp(key)


def transform_to_combo(command):
    command_tmp = ""
    for char in command[len("write "):]:
        command_tmp += "$" + char
    return command_tmp


def execute_script(script):
    for command in script:
        if "press " in command:
            pyautogui.press(command[len("press "):])
        elif "hold " in command:
            pyautogui.keyDown(command[len("hold "):])
        elif "release " in command:
            pyautogui.keyUp(command[len("release "):])
        elif "combo " in command:
            send_combo_command(command)
        elif "write " in command:
            command = transform_to_combo(command)
            send_combo_command(command)
        elif "delay " in command:
            time.sleep(float(command[len("delay "):]))

import time
import pyautogui

pyautogui.PAUSE = 0.01


def read_script(file_name):
    dictionary = {}
    key = None
    raw_value = []
    with open(file_name, 'r') as f:
        for raw in f:
            raw = raw.strip()
            if key is None:
                key = raw
                raw_value = []
            elif raw == "":
                dictionary[key] = raw_value
                key = None
            else:
                raw_value.append(raw)
    if key is not None and raw_value:
        dictionary[key] = raw_value
    return dictionary


def save_scripts(file_name, scripts):
    with open(file_name, 'w') as f:
        for key, list in scripts.items():
            f.write(key + '\n')
            for element in list:
                f.write(element + '\n')
            f.write('\n')


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

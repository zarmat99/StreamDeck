/**
 * StreamDeck Control reference firmware.
 *
 * Protocol: newline-delimited ASCII, version 1.  The implementation avoids
 * dynamic String allocations and blocking button loops so serial commands,
 * LEDs and all controls remain responsive under load.
 *
 * INPUT_ACTIVE_LOW=0 preserves the original active-high/external-pulldown
 * hardware.  Set it to 1 for buttons wired to ground using INPUT_PULLUP.
 */

#include <Arduino.h>

#ifndef INPUT_ACTIVE_LOW
#define INPUT_ACTIVE_LOW 0
#endif

namespace {

constexpr char FIRMWARE_VERSION[] = "3.0.0";
constexpr uint8_t PROTOCOL_VERSION = 1;
constexpr unsigned long BAUD_RATE = 9600;
constexpr unsigned long DEBOUNCE_MS = 30;
constexpr unsigned long POT_SAMPLE_MS = 20;
constexpr unsigned long POT_EMIT_MS = 50;
constexpr int POT_TOLERANCE = 6;
constexpr size_t LINE_BUFFER_SIZE = 96;

constexpr uint8_t RECORD_PIN = 9;
constexpr uint8_t STREAM_PIN = 8;
constexpr uint8_t SCENE_PINS[] = {10, 11, 12, 13};
constexpr uint8_t POT_PINS[] = {A0, A1, A2, A3};
constexpr uint8_t LED_PINS[] = {7, 2};  // stream, record
constexpr uint8_t GENERAL_PINS[] = {3, 4, 5, 6};
constexpr size_t CONTROL_COUNT = 4;

struct DebouncedInput {
  bool stable = false;
  bool candidate = false;
  unsigned long changedAt = 0;
};

DebouncedInput recordInput;
DebouncedInput streamInput;
DebouncedInput sceneInputs[CONTROL_COUNT];
DebouncedInput generalInputs[CONTROL_COUNT];

int potValues[CONTROL_COUNT] = {-1, -1, -1, -1};
unsigned long potLastEmitted[CONTROL_COUNT] = {0, 0, 0, 0};
unsigned long lastPotSample = 0;

bool deviceStarted = false;
char lineBuffer[LINE_BUFFER_SIZE];
size_t lineLength = 0;

bool rawPressed(uint8_t pin) {
#if INPUT_ACTIVE_LOW
  return digitalRead(pin) == LOW;
#else
  return digitalRead(pin) == HIGH;
#endif
}
void configureInput(uint8_t pin) {
#if INPUT_ACTIVE_LOW
  pinMode(pin, INPUT_PULLUP);
#else
  pinMode(pin, INPUT);  // Reference active-high board requires external pulldown.
#endif
}

bool updateInput(uint8_t pin, DebouncedInput &input, unsigned long now,
                 bool &pressedEdge, bool &releasedEdge) {
  pressedEdge = false;
  releasedEdge = false;
  const bool sample = rawPressed(pin);

  if (sample != input.candidate) {
    input.candidate = sample;
    input.changedAt = now;
  }

  if (input.candidate != input.stable && now - input.changedAt >= DEBOUNCE_MS) {
    input.stable = input.candidate;
    pressedEdge = input.stable;
    releasedEdge = !input.stable;
    return true;
  }
  return false;
}

void sendReady() {
  Serial.print(F("READY "));
  Serial.print(PROTOCOL_VERSION);
  Serial.print(' ');
  Serial.print(FIRMWARE_VERSION);
  Serial.println(F(" controls=B0-B3,P0-P3,G0-G3 leds=stream,record"));
}

void setLed(uint8_t index, bool enabled) {
  if (index >= 2) {
    Serial.println(F("NACK invalid_led"));
    return;
  }
  digitalWrite(LED_PINS[index], enabled ? HIGH : LOW);
  Serial.println(F("ACK LED"));
}

void handleCommand(const char *line) {
  if (strcmp(line, "HELLO 1") == 0 || strcmp(line, "HELLO") == 0) {
    sendReady();
    return;
  }
  if (strcmp(line, "PING") == 0) {
    Serial.print(F("PONG "));
    Serial.println(millis());
    return;
  }
  if (strcmp(line, "START") == 0 || strcmp(line, "start") == 0) {
    deviceStarted = true;
    Serial.println(strcmp(line, "start") == 0 ? F("start ok") : F("ACK START"));
    return;
  }
  if (strcmp(line, "STOP") == 0 || strcmp(line, "stop") == 0) {
    deviceStarted = false;
    Serial.println(strcmp(line, "stop") == 0 ? F("stop ok") : F("ACK STOP"));
    return;
  }

  // Version 1 LED command: LED <stream=0|record=1> <off=0|on=1>
  if (strncmp(line, "LED ", 4) == 0) {
    int index = -1;
    int state = -1;
    if (sscanf(line + 4, "%d %d", &index, &state) == 2 && index >= 0 &&
        index <= 1 && state >= 0 && state <= 1) {
      setLed(static_cast<uint8_t>(index), state == 1);
    } else {
      Serial.println(F("NACK invalid_led_command"));
    }
    return;
  }

  // Legacy commands retained for existing desktop releases.
  if (strcmp(line, "StreamOnLed") == 0) {
    setLed(0, true);
  } else if (strcmp(line, "StreamOffLed") == 0) {
    setLed(0, false);
  } else if (strcmp(line, "RecordOnLed") == 0) {
    setLed(1, true);
  } else if (strcmp(line, "RecordOffLed") == 0) {
    setLed(1, false);
  } else {
    Serial.println(F("NACK unknown_command"));
  }
}

void pollSerial() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());
    if (incoming == '\r') {
      continue;
    }
    if (incoming == '\n') {
      if (lineLength > 0) {
        lineBuffer[lineLength] = '\0';
        handleCommand(lineBuffer);
        lineLength = 0;
      }
      continue;
    }
    if (lineLength < LINE_BUFFER_SIZE - 1) {
      lineBuffer[lineLength++] = incoming;
    } else {
      lineLength = 0;
      Serial.println(F("NACK line_too_long"));
    }
  }
}

void pollDigitalControls(unsigned long now) {
  bool pressed = false;
  bool released = false;

  if (updateInput(RECORD_PIN, recordInput, now, pressed, released)) {
    Serial.println(pressed ? F("StartRecord") : F("StopRecord"));
  }
  if (updateInput(STREAM_PIN, streamInput, now, pressed, released)) {
    Serial.println(pressed ? F("StartStream") : F("StopStream"));
  }

  for (size_t index = 0; index < CONTROL_COUNT; ++index) {
    if (updateInput(SCENE_PINS[index], sceneInputs[index], now, pressed, released) &&
        pressed) {
      Serial.print(F("ChangeScene B"));
      Serial.println(index);
    }
    if (updateInput(GENERAL_PINS[index], generalInputs[index], now, pressed,
                    released) &&
        pressed) {
      Serial.print(F("ExecuteScript G"));
      Serial.println(index);
    }
  }
}

void pollPotentiometers(unsigned long now) {
  if (now - lastPotSample < POT_SAMPLE_MS) {
    return;
  }
  lastPotSample = now;

  for (size_t index = 0; index < CONTROL_COUNT; ++index) {
    const int sample = 1023 - analogRead(POT_PINS[index]);
    if (potValues[index] < 0) {
      potValues[index] = sample;
      continue;
    }

    // Small integer low-pass filter reduces ADC noise without floating point.
    const int filtered = (potValues[index] * 3 + sample) / 4;
    if (abs(filtered - potValues[index]) >= POT_TOLERANCE &&
        now - potLastEmitted[index] >= POT_EMIT_MS) {
      potValues[index] = filtered;
      potLastEmitted[index] = now;
      Serial.print(F("SetInputVolume P"));
      Serial.print(index);
      Serial.print(' ');
      Serial.println(filtered);
    } else if (abs(sample - potValues[index]) < POT_TOLERANCE) {
      potValues[index] = filtered;
    }
  }
}

}  // namespace

void setup() {
  configureInput(RECORD_PIN);
  configureInput(STREAM_PIN);
  for (size_t index = 0; index < CONTROL_COUNT; ++index) {
    configureInput(SCENE_PINS[index]);
    configureInput(GENERAL_PINS[index]);
    pinMode(POT_PINS[index], INPUT);
  }
  for (uint8_t ledPin : LED_PINS) {
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);
  }

  Serial.begin(BAUD_RATE);
}

void loop() {
  pollSerial();
  if (!deviceStarted) {
    return;
  }

  const unsigned long now = millis();
  pollDigitalControls(now);
  pollPotentiometers(now);
}

// Constants
const int DELAY = 10;                   // Milliseconds delay
const int TOLERANCE = 3;                // Tolerance for analog inputs
const int MIN_POT = 93;                 // Minimum value for potentiometer
const int MAX_POT = 1022;               // Maximum value for potentiometer
const int MAX_ANALOG_READ = 1023;       // Maximum value for analog read
const int MAX_ANALOG_WRITE = ((MAX_ANALOG_READ + 1) / 4) - 1; // Maximum value for analog write

// Pin Definitions
const int RECORD_PIN = 8;               // Pin for recording
const int STREAM_PIN = 9;               // Pin for streaming
const int SET_MODE_PIN = 2;             // Pin for setting mode
const int SCENE_PINS[] = {10, 11, 12, 13}; // Pins for scenes
const int POT_PINS[] = {A0, A1, A2};    // Pins for potentiometers
const int LED_PINS[] = {A3, A4};        // Pins for LEDs
const int GEN_PUR_PINS[] = {3, 4, 5, 6}; // Pins for general purpose

// Variables
int time = 0;                           // Milliseconds
int volume[] = {MAX_POT, MAX_POT, MAX_POT}; // Array to store volume levels
int recording = 0;                      // Recording state
int streaming = 0;                      // Streaming state
bool startReceived = false;             // Flag to track if "start" message received

// Function prototypes
int adjustVolume(int volume, char identifier, int pin);
void dumbMode();
void handleControls();

void setup() {
  // Pin mode setup
  pinMode(RECORD_PIN, INPUT);
  pinMode(STREAM_PIN, INPUT);
  pinMode(SET_MODE_PIN, INPUT);
  for (int i = 0; i < 4; i++) {
    pinMode(SCENE_PINS[i], INPUT);
    digitalWrite(SCENE_PINS[i], LOW);
  }
  for (int i = 0; i < 2; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    analogWrite(LED_PINS[i], 0);
  }
  for (int i = 0; i < 4; i++) {
    pinMode(GEN_PUR_PINS[i], INPUT);
    digitalWrite(GEN_PUR_PINS[i], LOW);
  }
  for (int i = 0; i < 3; i++) {
    pinMode(POT_PINS[i], INPUT);
    analogWrite(POT_PINS[i], 0);
  }

  // Serial communication setup
  Serial.begin(9600);
}

void loop() {
  if (startReceived) {
    handleControls();

    // Adjust volume if necessary
    if (time > 200) {
      for (int i = 0; i < 3; i++) {
        volume[i] = adjustVolume(volume[i], '0' + i, POT_PINS[i]);
      }
      time = 0;
    }

    delay(DELAY);
    time += DELAY;
  } else {
    // Check if "start" message received
    if (Serial.available()) {
      String line = Serial.readStringUntil('\n');
      if (line == "start") 
      {
        startReceived = true;
        Serial.println("start ok");
      }
    }
  }
}

// Function to adjust volume
int adjustVolume(int volume, char identifier, int pin) {
  int newVolume = analogRead(pin);
  
  // Send serial data only if the potentiometer value changes significantly
  if (abs(newVolume - volume) > TOLERANCE) {
    volume = newVolume;
    Serial.println("SetInputVolume");
    Serial.print("P");
    Serial.println(identifier);
    Serial.println(volume);
  }
  
  return volume;
}

// Function to handle dumb mode
void dumbMode() {
  while (true) {
    if (Serial.available()) {
      String line = Serial.readStringUntil('\n');
      if (line == "NormalOperation") {
        break;
      }
    }
  }
}

// Function to handle controls
void handleControls() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');

    // DumbMode control
    if (line == "DumbMode") {
      dumbMode();
    }

    // LED state control
    if (line == "RecordOnLed") {
      analogWrite(LED_PINS[0], MAX_ANALOG_WRITE);
    }
    if (line == "RecordOffLed") {
      analogWrite(LED_PINS[0], 0);
    }
    if (line == "StreamOnLed") {
      analogWrite(LED_PINS[1], MAX_ANALOG_WRITE);
    }
    if (line == "StreamOffLed") {
      analogWrite(LED_PINS[1], 0);
    }
  }

  // Record controls
  if (digitalRead(RECORD_PIN) == HIGH && !recording) {
    Serial.println("StartRecord");
    recording = 1;
  } else if (digitalRead(RECORD_PIN) == LOW && recording) {
    Serial.println("StopRecord");
    recording = 0;
  }

  // Streaming controls
  else if (digitalRead(STREAM_PIN) == HIGH && !streaming) {
    Serial.println("StartStream");
    streaming = 1;
  } else if (digitalRead(STREAM_PIN) == LOW && streaming) {
    Serial.println("StopStream");
    streaming = 0;
  }

  // Scene controls
  else {
    for (int i = 0; i < 4; i++) {
      if (digitalRead(SCENE_PINS[i]) == HIGH) {
        Serial.println("ChangeScene");
        Serial.print("B");
        Serial.println(i);
        while (digitalRead(SCENE_PINS[i]) == HIGH);
        break;
      }
    }
  }

  // General purpose controls
  for (int i = 0; i < 4; i++) {
    if (digitalRead(GEN_PUR_PINS[i]) == HIGH) {
      Serial.println("ExecuteScript");
      Serial.print("G");
      Serial.println(i);
      while (digitalRead(GEN_PUR_PINS[i]) == HIGH);
      break;
    }
  }
}

// Constants
const int DELAY = 10;                   // Milliseconds delay
const int TOLERANCE = 5;                // Tolerance for analog inputs
const int MAX_ANALOG_READ = 1023;       // Maximum value for analog read

// Pin Definitions
const int RECORD_PIN = 9;               // Pin for recording
const int STREAM_PIN = 8;               // Pin for streaming
const int SCENE_PINS[] = {10, 11, 12, 13}; // Pins for scenes
const int POT_PINS[] = {A0, A1, A2, A3};    // Pins for potentiometers
const int LED_PINS[] = {7, 2};        // Pins for LEDs
const int GEN_PUR_PINS[] = {3, 4, 5, 6}; // Pins for general purpose

// Variables
int time = 0;                           // Milliseconds
int volume[] = {0, 0, 0, 0}; // Array to store volume levels
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

  for (int i = 0; i < 2; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], 0);
  }
  for (int i = 0; i < 4; i++) {
    pinMode(GEN_PUR_PINS[i], INPUT);
    digitalWrite(GEN_PUR_PINS[i], LOW);
  }
  for (int i = 0; i < 3; i++) {
    pinMode(POT_PINS[i], INPUT);
  }

  // Serial communication setup
  Serial.begin(9600);
}

void loop() {
  // Check for start/stop commands
  if (Serial.available()) 
  {
    String line = Serial.readStringUntil('\n');

    // Handle start and stop messages
    if (line == "start") {
      startReceived = true;
      Serial.println("start ok");
    } 
    else if (line == "stop") 
    {
      startReceived = false;
      Serial.println("stop ok");
    }
  }

  // If start received, handle controls
  if (startReceived) {
    handleControls();
  }
}

// Function to adjust volume
int adjustVolume(int volume, char identifier, int pin) {
  int newVolume = 1023 - analogRead(pin);
  
  // Send serial data only if the potentiometer value changes significantly
  if (abs(newVolume - volume) > TOLERANCE) 
  {
    volume = newVolume;
    String message = "SetInputVolume P" + String(identifier) + " " + String(volume);
    Serial.println(message);
  }
  
  return volume;
}

// Function to handle dumb mode
void dumbMode() 
{
  while (true) 
  {
    if (Serial.available()) 
    {
      String line = Serial.readStringUntil('\n');
      if (line == "NormalOperation") 
      {
        break;
      }
    }
  }
}

// Function to handle controls
void handleControls() {
  if (Serial.available()) 
  {
    String line = Serial.readStringUntil('\n');

    // DumbMode control
    if (line == "DumbMode") 
    {
      dumbMode();
    }

    // LED state control
    if (line == "RecordOnLed") 
    {
      digitalWrite(LED_PINS[1], HIGH);
      Serial.println("Record Led HIGH");
    }
    if (line == "RecordOffLed") {
      digitalWrite(LED_PINS[1], LOW);
    }
    if (line == "StreamOnLed") {
      digitalWrite(LED_PINS[0], HIGH);
    }
    if (line == "StreamOffLed") {
      digitalWrite(LED_PINS[0], LOW);
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
        String message = "ChangeScene B" + String(i);
        Serial.println(message);
        while (digitalRead(SCENE_PINS[i]) == HIGH);
        break;
      }
    }
  }

  // General purpose controls
  for (int i = 0; i < 4; i++) {
    if (digitalRead(GEN_PUR_PINS[i]) == HIGH) {
      String message = "ExecuteScript G" + String(i);
      Serial.println(message);
      while (digitalRead(GEN_PUR_PINS[i]) == HIGH);
      break;
    }
  }
  
  // Adjust volume if necessary
  for (int i = 0; i < 4; i++) 
  {
    volume[i] = adjustVolume(volume[i], '0' + i, POT_PINS[i]);
  }
}

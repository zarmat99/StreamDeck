#include <EEPROM.h>

#define DELAY 10 //milliseconds
#define SCENEBUTTON0 0
#define SCENEBUTTON1 1
#define SCENEBUTTON2 2
#define SCENEBUTTON3 3

const int EEPROM_SIZE = 512;
const int STRING_LENGTH = 20;
const int recordPin = 4;     
const int setmodePin = 7;
const int scene1Pin = 2;  //SCENEBUTTON0
const int scene2Pin = 3;  //SCENEBUTTON1

int t = 0;
int t_flut = 0;
int recording = 0;

String scenes[] = {"no scene", "no scene", "no scene", "no scene"};


void ReadSettings()
{
  for (int i = 0; i < 4; i++)
  {
    char buffer[STRING_LENGTH]; 
    EEPROM.get(i * 20, buffer);
    scenes[i] = String(buffer);
  }
}

void SaveSettings()
{
  for (int i = 0; i < 4; i++)
  {
    char buffer[STRING_LENGTH]; 
    scenes[i].toCharArray(buffer, 20);
    EEPROM.put(i * 20, buffer);
  }
}

void setup() 
{
  pinMode(recordPin, INPUT);
  pinMode(setmodePin, INPUT);  
  pinMode(scene1Pin, INPUT);
  pinMode(scene2Pin, INPUT);
  digitalWrite(scene1Pin, LOW);
  digitalWrite(scene2Pin, LOW);  
  digitalWrite(recordPin, LOW); 
  digitalWrite(setmodePin, LOW);  
  ReadSettings();
  Serial.begin(9600);          
}


int TimeTriggerEventHandler(int pin, int milliseconds, int add_delay)
{
   if (digitalRead(pin) == HIGH)
     milliseconds += add_delay;
   else
     milliseconds = 0;
   delay(add_delay);
   return milliseconds;
}


void SetMode()
{
  t = 0;
  int i = -1;
  String data;
  int exit_flag = 0;
  while (1)
  {
    data = "";
    // until a button to be set is pressed, do nothing except manage the exit event
    while (digitalRead(scene1Pin) == LOW && digitalRead(scene2Pin) == LOW)   //and scene3 or scene4 ecc..
    {
      t = TimeTriggerEventHandler(setmodePin, t, DELAY);
      if (t >= 2000)
      {
        exit_flag = 1;
        break;
      }   
    }
    if (exit_flag)
      break;
   
    // understands which button was pressed
    if (digitalRead(scene1Pin) == HIGH)
    {
      Serial.println("selected button 0");
      i = 0;
    }
     else if (digitalRead(scene2Pin) == HIGH)
    {
      Serial.println("selected button 1");
      i = 1;
    }
   // elif scene3Pin == HIGH ...

    // wait until I receive consistent data from the user
    while (data == "")
    {
      data = Serial.readString();
      t = TimeTriggerEventHandler(setmodePin, t, 1000);
      if (t >= 2000)
      {
        exit_flag = 1;
        break;
      }
    }
    if (exit_flag)
      break;
  
    scenes[i] = data;
    SaveSettings();
    Serial.print(scenes[i]);
    Serial.print(" setted in button ");
    Serial.println(i);
  }
  
}


void loop() 
{
  // setmode controls
  if (digitalRead(setmodePin) == HIGH)
    t += DELAY;
  else
    t = 0;

  if (t > 2000)
  {
    Serial.println("SetMode");
    SetMode();
    t = 0;
    Serial.println("Normal Operation");
  }

  // record controls
  if (digitalRead(recordPin) == HIGH && !recording)    
  {
    Serial.println("StartRecord");    // start recording
    recording = 1;
  } 
  else if(digitalRead(recordPin) == LOW && recording)
  {
    Serial.println("StopRecord");
    recording = 0;
  }
  else if(digitalRead(scene1Pin) == HIGH)
  {
    Serial.println("ChangeScene");
    Serial.println(scenes[SCENEBUTTON0]);
    while(digitalRead(scene1Pin) == HIGH);
  }
  else if(digitalRead(scene2Pin) == HIGH)
  {
    Serial.println("ChangeScene");
    Serial.println(scenes[SCENEBUTTON1]);
    while(digitalRead(scene2Pin) == HIGH);
  }
  
  delay(DELAY);
}
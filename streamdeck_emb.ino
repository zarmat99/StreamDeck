#include <EEPROM.h>

const int DELAY 10 //milliseconds
const int EEPROM_SIZE = 512;
const int STRING_LENGTH = 20;
const int recordPin = 12;  
const int streamPin = 11;   
const int setmodePin = 2;
const int scene0Pin = 8; 
const int scene1Pin = 9;  
const int pot0Pin = A0;
const int pot1Pin = A1;
const int pot2Pin = A2;

int t = 0;
int t_flut = 0;
int recording = 0;
int streaming = 0;

String scenes[] = {"no scene", "no scene", "no scene", "no scene"};
int volumes[] = {0, 0, 0};


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
  pinMode(streamPin, INPUT);
  pinMode(setmodePin, INPUT);  
  pinMode(scene0Pin, INPUT);
  pinMode(scene1Pin, INPUT);
  digitalWrite(scene0Pin, LOW);
  digitalWrite(scene1Pin, LOW);  
  digitalWrite(recordPin, LOW); 
  digitalWrite(streamPin, LOW); 
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
    while (digitalRead(scene0Pin) == LOW && digitalRead(scene1Pin) == LOW)   //and scene3 or scene4 ecc..
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
    if (digitalRead(scene0Pin) == HIGH)
    {
      Serial.println("B0");
      i = 0;
    }
     else if (digitalRead(scene1Pin) == HIGH)
    {
      Serial.println("B1");
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
  else if(digitalRead(streamPin) == HIGH && !streaming)    
  {
    Serial.println("StartStream");    // start recording
    streaming = 1;
  } 
  else if(digitalRead(streamPin) == LOW && streaming)
  {
    Serial.println("StopStream");
    streaming = 0;
  }
  else if(digitalRead(scene0Pin) == HIGH)
  {
    Serial.println("ChangeScene");
    Serial.println(scenes[0]);
    while(digitalRead(scene0Pin) == HIGH);
  }
  else if(digitalRead(scene1Pin) == HIGH)
  {
    Serial.println("ChangeScene");
    Serial.println(scenes[1]);
    while(digitalRead(scene1Pin) == HIGH);
  }
  /*
  Serial.println("SetInputVolume");
  Serial.println(volumes[0]);
  Serial.println(analogRead(pot0Pin));
  Serial.println("SetInputVolume");
  Serial.println(volumes[1]);
  Serial.println(analogRead(pot1Pin));
  Serial.println("SetInputVolume");
  Serial.println(volumes[2]);
  Serial.println(analogRead(pot2Pin));
  */
  delay(DELAY);
}
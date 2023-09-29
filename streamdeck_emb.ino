const int DELAY = 10;       //milliseconds
const int TOLLERANCE = 10;
const int MIN_POT = 93;
const int MAX_POT = 1022;
const int recordPin = 12;  
const int streamPin = 11;   
const int setmodePin = 2;
const int scene0Pin = 8; 
const int scene1Pin = 9;  
const int pot0Pin = A0;
const int pot1Pin = A1;
const int pot2Pin = A2;

int volume[] = {MAX_POT, MAX_POT, MAX_POT};
int t = 0;
int t_flut = 0;
int recording = 0;
int streaming = 0;

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
  int exit_flag = 0;
  String selection = "";
  while (1)
  {
    // until a button to be set is pressed, do nothing except manage the exit event
    while (digitalRead(scene0Pin) == LOW && digitalRead(scene1Pin) == LOW && 
           analogRead(pot0Pin) > (volume[0] - TOLLERANCE) && analogRead(pot0Pin) < (volume[0] + TOLLERANCE) &&
           analogRead(pot1Pin) > (volume[1] - TOLLERANCE) && analogRead(pot1Pin) < (volume[1] + TOLLERANCE) &&
           analogRead(pot2Pin) > (volume[2] - TOLLERANCE) && analogRead(pot2Pin) < (volume[2] + TOLLERANCE))   //and scene3 or scene4 ecc..
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
      if(selection != "B0")
        Serial.println("B0");
      selection = "B0";
    }
    else if (digitalRead(scene1Pin) == HIGH)
    {
      if(selection != "B1")
        Serial.println("B1");
      selection = "B1";
    }
    
    // understands which potentiometer triggered
    else if(analogRead(pot0Pin) < (volume[0] - TOLLERANCE) || analogRead(pot0Pin) > (volume[0] + TOLLERANCE))
    {
      volume[0] = analogRead(pot0Pin);
      if(selection != "P0")
        Serial.println("P0");  
      selection = "P0";
    }
    else if(analogRead(pot1Pin) < (volume[1] - TOLLERANCE) || analogRead(pot1Pin) > (volume[1] + TOLLERANCE))
    {
      volume[1] = analogRead(pot1Pin);
      if(selection != "P1")
        Serial.println("P1"); 
      selection = "P1"; 
    }
    else if(analogRead(pot2Pin) < (volume[2] - TOLLERANCE) || analogRead(pot2Pin) > (volume[2] + TOLLERANCE))
    {
      volume[2] = analogRead(pot2Pin);
      if(selection != "P2")
        Serial.println("P2"); 
      selection = "P2"; 
    }
      
   while (digitalRead(scene0Pin) == HIGH || digitalRead(scene1Pin) == HIGH);
  }
  
}


int VolumeHandler(int volume, char i, int pin)
{
  volume = analogRead(pin);
  Serial.println("SetInputVolume");
  Serial.print("P");
  Serial.println(i);
  Serial.println(volume);
  return volume;
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
    Serial.println("NormalOperation");
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
    Serial.println("B0");
    while(digitalRead(scene0Pin) == HIGH);
  }
  else if(digitalRead(scene1Pin) == HIGH)
  {
    Serial.println("ChangeScene");
    Serial.println("B1");
    while(digitalRead(scene1Pin) == HIGH);
  }
  
  if(analogRead(pot0Pin) < (volume[0] - TOLLERANCE) || analogRead(pot0Pin) > (volume[0] + TOLLERANCE))
    volume[0] = VolumeHandler(volume[0], '0', pot0Pin);
  if(analogRead(pot1Pin) < (volume[1] - TOLLERANCE) || analogRead(pot1Pin) > (volume[1] + TOLLERANCE))
    volume[1] = VolumeHandler(volume[1], '1', pot1Pin);
  if(analogRead(pot2Pin) < (volume[2] - TOLLERANCE) || analogRead(pot2Pin) > (volume[2] + TOLLERANCE))
    volume[2] = VolumeHandler(volume[2], '2', pot2Pin);
  
  delay(DELAY);
}
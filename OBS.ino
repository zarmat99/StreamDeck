#define DELAY 10 //milliseconds
#define SCENEBUTTON0 0
#define SCENEBUTTON1 1
#define SCENEBUTTON2 2
#define SCENEBUTTON3 3
#define TEST 0

const int recordPin = 4;     
const int setmodePin = 7;
const int scene1Pin = 2;  //SCENEBUTTON0

int t = 0;
int t_flut = 0;
int recording = 0;

String scenes[] = {"no scene", "no scene", "no scene", "no scene"};

void setup() 
{
  pinMode(recordPin, INPUT);
  pinMode(setmodePin, INPUT);  
  pinMode(scene1Pin, INPUT);
  digitalWrite(scene1Pin, LOW);  
  digitalWrite(recordPin, LOW); 
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
  int i = -1;
  String data;
  int exit_flag = 0;
  while (1)
  {
    data = "";
    // until a button to be set is pressed, do nothing except manage the exit event
    while (digitalRead(scene1Pin) == LOW)   //or scene2 or scene3 ecc..
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
   // elif scene2Pin == HIGH ...

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
    Serial.print(scenes[i]);
    Serial.println(" setted in button 0");
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
  
  
  delay(DELAY);
}

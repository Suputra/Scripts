#include <Braccio.h>
#include <Servo.h>

char currChar; //current character
char currWord[3]; //current word/number/command
int commands[7]; //commands sent to robot 
String strCommand;

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;

void setup()
{
  Braccio.begin();
  Serial.begin(9600);
}

void loop()
{
  if (Serial.available()) {
    currChar = Serial.read();
    currWord[0] = currChar;
    currChar = Serial.read();
    currWord[1] = currChar;
    currChar = Serial.read();
    commands[0] = atoi(currWord);
    
    for (int i = 0; i < 24; i++) {
      currChar = Serial.read();
      if (i%4 == 0){
        commands[i/4] = atoi(currWord);
        //currWord[0] = '\0';
      } else {
        currWord[i%4 - 1] = currChar;
      }
    }
    
    for(int i = 0; i < 7; i++) {
      Serial.print(commands[i]);
      Serial.print(' ');
    }
    Serial.println();
    
    Braccio.ServoMovement(commands[0], commands[1], commands[2], commands[3], commands[4], commands[5], commands[6]); 
}

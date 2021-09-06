#include <Braccio.h>
#include <Servo.h>

char currChar; //current character
int charInd = 0; //current index in word/number/command
char currWord[5]; //current word/number/command
int wordInd = 0; //current index of word/number/command
int commands[7]; //commands sent to robot 

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
    while (wordInd < 8) {
      currChar = Serial.read();
      if (currChar != ' ') {
        currWord[charInd] = currChar;
        charInd++;
        Serial.println(currWord);
      } else {
        commands[wordInd] = atoi(currWord);
        currWord[0] = '\0';
        charInd = 0;
        wordInd++;
      }
    }
    
    for(int i = 0; i < 7; i++) {
      Serial.print(commands[i]);
      Serial.print(' ');
    }
    Serial.println();
    
    Braccio.ServoMovement(commands[0], commands[1], commands[2], commands[3], commands[4], commands[5], commands[6]); 
    wordInd = 0; 
    
  }
}

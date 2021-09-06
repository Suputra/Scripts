#include <Braccio.h>
#include <Servo.h>

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
    strCommand = Serial.readStringUntil('\n');
    strCommand.trim();
    
    commands[0] = (strCommand.substring(0, 2)).toInt();
    
    for (int i = 0; i < 6; i++) {
      commands[i+1] = (strCommand.substring(4*i + 3, 4*i +7)).toInt();
    }
    Braccio.ServoMovement(commands[0], commands[1], commands[2], commands[3], commands[4], commands[5], commands[6]); 
  }
}

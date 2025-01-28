String strCommand;

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
}

void loop()
{
  if (Serial.available()) {
    strCommand = Serial.readStringUntil('\n');
    strCommand.trim();
        
    for (int i = 0; i < strCommand.length(); i += 2) {
      switch (strCommand[i]) {
        case '0': digitalWrite(LED_BUILTIN, LOW);
        case '1': digitalWrite(LED_BUILTIN, HIGH);
      }
      delay(1000);
    }
  }
}

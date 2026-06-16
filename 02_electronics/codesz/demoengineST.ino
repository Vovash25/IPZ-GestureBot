#include <SCServo.h>
SMS_STS st;
void setup()
{
  Serial1.begin(1000000);
  st.pSerial = &Serial1;
  while(!Serial1) {}
}

void loop()
{
  st.WritePos(4, 1000, 1500, 50); // Control the servo with ID 1 to rotate to the position of 1000 at a speed of 1500 and start and stop the acceleration of 50.
  delay(754);

  st.WritePos(8, 20, 1500, 50); // Control the servo with ID 1 to rotate to the position 20 at a speed of 1500 and start and stop the acceleration at 50.
  delay(754);
}

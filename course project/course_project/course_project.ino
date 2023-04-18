#include <Grove_LED_Bar.h>
#include <Servo.h>
// Grove_LED_Bar bar(7, 6, 0, LED_BAR_10); // Clock pin, Data pin, Orientation
#define LIGHT A3
#define TEMP_SENSOR (A0)  // Grove - Temperature Sensor connect to A0
#define TouchPin (4)

String COM_VOLCANO_LEVEL = "COM_VOLCANO_LEVEL";
String ACK_VOLCANO_LEVEL = "ACK_VOLCANO_LEVEL";

Servo myservo;  // create servo object to control a servo
int pos = 0;    // variable to store the servo position

float temp_C;                            // Variable used to store temperature
float temp_F;                            // Variable used to store temperature

void setup(){
  pinMode(TouchPin, INPUT);     // Touch Sensor
  pinMode(TEMP_SENSOR, INPUT);  // Temperature: Configure pin A0 as an INPUT
  Serial.begin(9600);
  myservo.attach(5);            // attaches the servo on pin 5 to the servo object
  pinMode(LIGHT, INPUT);
}

float temperature = read_Temperature(TEMP_SENSOR);
float light = read_Light(LIGHT);


void loop(){
  // if (Serial.available() > 0){  // Check if there is data available to read from the Serial port.
    

  if(digitalRead(TouchPin) == 1){
      float startTime = millis();
      Serial.println("The touch Sensor is being pressed");
      float bowelMovementDuration = measure_duration(startTime,TouchPin);
  }


    // String s_com = (Serial.readStringUntil('\n'));    
    // float temperature = read_Temperature(TEMP_SENSOR);
    // float light = read_Light(LIGHT);
    // Serial.println(temperature);
    // Serial.println(light);

}



/*
 * @brief:  Reads an Analog input. 
 *          Converts the analog voltage value into a Temperature value in degrees Celsius. 
 * @param:  pin - Analog Input pin number
 * @ret:    temperature - Temperature value in degrees Celsius (float).
 */
float read_Temperature(int pin) {
  const int B = 4275;       // B value of the thermistor
  const int R0 = 100000;    // R0 = 100k
  int a = analogRead(pin);  // Integer: 0-1023
  float R = 1023.0 / a - 1.0;
  R = R0 * R;
  float temperature = 1.0 / (log(R / R0) / B + 1 / 298.15) - 273.15;  // convert to temperature via datasheet
  return temperature;
}


/*
 * @brief:  Reads an Analog input. 
 *          Converts the analog voltage value into a Temperature value in degrees Celsius. 
 * @param:  pin - Analog Input pin number
 * @ret:    mapped light
 */
float read_Light(int pin) {
  int analog_value = analogRead(pin);
  // Serial.print("Analog Value = ");
  // Serial.print(analog_value);
  int mapped_value = map(analog_value, 0, 1023, 0, 10);
  // Serial.print("  |  Scaled Value = ");
  // Serial.print(mapped_value);
  return mapped_value;
}


float measure_duration(float startTime, int pin){
  // float interval = millis() - startTime;
  float usageEndTime = startTime;
  float interval = usageEndTime - startTime;
  while(digitalRead(pin) == 1){

    
    usageEndTime = millis();
    interval = usageEndTime - startTime;
    if(interval > 60000){
      Serial.println("[Alert] Sitting more than 10mins");
    }
  }
  
  Serial.println("Duration");
  Serial.println(interval);

  return interval;
}
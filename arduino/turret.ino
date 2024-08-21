#include <Servo.h>
#include <ArduinoBLE.h>

Servo xServo;  // Create a Servo object for X-axis
Servo yServo;  // Create a Servo object for Y-axis

BLEService servoService("180C");  // Custom service

BLECharacteristic directionCharacteristic("2A56", BLERead | BLEWrite, 20);  // Custom characteristic

int xPos = 90;  // Initialize X servo position to center
int yPos = 90;  // Initialize Y servo position to center

const int stepSize = 5;  // Amount to increase/decrease servo position with each key press

void setup() {
  Serial.begin(9600);
  while (!Serial);

  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    while (1);
  }

  xServo.attach(8);  // Attach X servo to pin 8
  yServo.attach(9);  // Attach Y servo to pin 9
  xServo.write(xPos);  // Set X servo to initial position
  yServo.write(yPos);  // Set Y servo to initial position

  BLE.setLocalName("ServoController");
  BLE.setAdvertisedService(servoService);

  servoService.addCharacteristic(directionCharacteristic);
  BLE.addService(servoService);

  BLE.advertise();
  Serial.println("BLE advertising started");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());

    while (central.connected()) {
      if (directionCharacteristic.written()) {
        // Get the value as a string
        String direction = "";
        int length = directionCharacteristic.valueLength();
        for (int i = 0; i < length; i++) {
          direction += (char)directionCharacteristic.value()[i];
        }
        Serial.print("Received command: ");
        Serial.println(direction);

        if (direction == "up") {
          yPos = constrain(yPos - stepSize, 0, 180);  // Decrease Y position
          yServo.write(yPos);
        } else if (direction == "down") {
          yPos = constrain(yPos + stepSize, 0, 180);  // Increase Y position
          yServo.write(yPos);
        } else if (direction == "left") {
          xPos = constrain(xPos - stepSize, 0, 180);  // Decrease X position
          xServo.write(xPos);
        } else if (direction == "right") {
          xPos = constrain(xPos + stepSize, 0, 180);  // Increase X position
          xServo.write(xPos);
        }
      }
    }

    Serial.print("Disconnected from: ");
    Serial.println(central.address());
  }
}
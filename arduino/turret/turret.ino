#include <WiFi.h>
#include <Servo.h>

const char* ssid = "";
const char* password = "";

WiFiServer server(80);

Servo xServo;
Servo yServo;

int xPos = 90;
int yPos = 90;
const int stepSize = 5;

void setup() {
  Serial.begin(115200);

  xServo.attach(8);
  yServo.attach(9);
  xServo.write(xPos);
  yServo.write(yPos);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    Serial.println("New Client Connected");

    while (client.connected()) {
      if (client.available()) {
        char received = client.read();
        Serial.print("Received: ");
        Serial.println(received);

        if (received == 'w') {
          yPos = constrain(yPos - stepSize, 0, 180);
          yServo.write(yPos);
        } else if (received == 's') {
          yPos = constrain(yPos + stepSize, 0, 180);
          yServo.write(yPos);
        } else if (received == 'a') {
          xPos = constrain(xPos - stepSize, 0, 180);
          xServo.write(xPos);
        } else if (received == 'd') {
          xPos = constrain(xPos + stepSize, 0, 180);
          xServo.write(xPos);
        }
      }
    }

    client.stop();
    Serial.println("Client Disconnected");
  }
}
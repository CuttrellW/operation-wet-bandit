#include <WiFi.h>
#include <Servo.h>

const char* ssid = "";
const char* password = "";

WiFiServer server(80);

Servo xServo;
Servo yServo;

// Initial positions (degrees)
int xPos = 135;  // Center position for 270-degree servo
int yPos = 0;

// Servo pulse width range (microseconds)
int minPulseWidth = 500;   // Adjust according to your servo's datasheet
int maxPulseWidth = 2500;  // Adjust according to your servo's datasheet

void setup() {
  Serial.begin(115200);

  // Attach servos with specified pulse width range
  xServo.attach(8, minPulseWidth, maxPulseWidth);
  yServo.attach(9, minPulseWidth, maxPulseWidth);

  // Move servos to initial positions
  xServo.write(xPos);
  yServo.write(yPos);

  // Connect to Wi-Fi network
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

    String request = "";

    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        if (c == '\n') {
          // End of request
          request.trim();  // Remove any leading/trailing whitespace
          Serial.print("Received: ");
          Serial.println(request);

          // Parse positions from the request
          parseAndSetPositions(request, client);

          // Clear the request string for the next message
          request = "";
        } else {
          request += c;
        }
      }
    }

    int xPulseWidth = angleToPulseWidth(135);
    int yPulseWidth = angleToPulseWidth(0);

    // Move servos to the specified positions
    xServo.writeMicroseconds(xPulseWidth);
    yServo.writeMicroseconds(yPulseWidth);

    client.stop();
    Serial.println("Client Disconnected");
  }
}

int angleToPulseWidth(int angle) {
  return map(angle, 0, 270, minPulseWidth, maxPulseWidth);
}

void parseAndSetPositions(String request, WiFiClient& client) {
  // Expected format: "x=<value>&y=<value>"
  int xIndex = request.indexOf("x=");
  int yIndex = request.indexOf("y=");
  

  if (xIndex != -1 && yIndex != -1) {
    int xEndIndex = request.indexOf('&', xIndex);
    String xValueStr = request.substring(xIndex + 2, xEndIndex);
    String yValueStr = request.substring(yIndex + 2);

    int xValue = xValueStr.toInt();
    int yValue = yValueStr.toInt();

    // Constrain values to servo limits
    xPos = constrain(xValue, 0, 270);
    yPos = constrain(yValue, 0, 270);

    // Calculate pulse widths
    int xPulseWidth = angleToPulseWidth(xPos);
    int yPulseWidth = angleToPulseWidth(yPos);

    // Move servos to the specified positions
    xServo.writeMicroseconds(xPulseWidth);
    yServo.writeMicroseconds(yPulseWidth);

    Serial.print("Moving xServo to ");
    Serial.print(xPos);
    Serial.print(" degrees, yServo to ");
    Serial.print(yPos);
    Serial.println(" degrees");

    // Send response to client
    client.println("Servos moved to positions: x=" + String(xPos) + ", y=" + String(yPos));
  } else {
    client.println("Invalid command format. Expected: x=<value>&y=<value>");
  }
}
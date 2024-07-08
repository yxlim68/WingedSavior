#include <WiFi.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <TinyGPS++.h>

const char *SSID = "Telur";
const char *PASSWORD = "123456789";

#define GPS_BAUD 9600
#define RXD2 16
#define TXD2 17

HardwareSerial GPSSerial(2);
TinyGPSPlus gps;

unsigned long timerDelay = 1000; // send wifi data every 1 second
unsigned long lastTimeSent = 0;

const String serverName = "http://192.168.11.34:8766";

String api(String path)
{
  return serverName + path;
}

void setup()
{

  Serial.begin(115200);

  GPSSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);

  Serial.print("Connecting to ");
  Serial.print(SSID);

  WiFi.begin(SSID, PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.println("Conecting...");
  }

  Serial.println("WiFi connected");
  Serial.print("IP: ");
  Serial.print(WiFi.localIP());
  Serial.println("");
}

void loop()
{
  unsigned long now = millis();

  if ((now - lastTimeSent) < timerDelay)
    return;

  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("Wifi disconnect");
    delay(500);
    return;
  }

  JsonDocument locationData;

  locationData["lat"] = 0;
  locationData["lng"] = 0;

  while (GPSSerial.available() > 0)
  {
    gps.encode(GPSSerial.read());
  }

  if (gps.location.isValid())
  {
    locationData["lat"] = gps.location.lat();
    locationData["lng"] = gps.location.lng();
  }

  char result[100];
  serializeJson(locationData, result);

  HTTPClient http;

  String sendPath = "/location";

  String serverPath = api(sendPath);

  http.begin(serverPath.c_str());

  http.addHeader("Content-Type", "application/json");

  Serial.println(result);
  int httpResponseCode = http.POST(result);

  if (httpResponseCode > 0)
  {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
  }
  else
  {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
  }
  // Free resources
  http.end();
  lastTimeSent = now;
}

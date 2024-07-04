// // // #include <TinyGPS++.h>

// // // TinyGPSPlus gps;

// // // HardwareSerial gpsSerial(1);

// // // void setup() {
// // //   Serial.begin(9600);
// // //   Serial2.begin(9600);
// // //   gpsSerial.begin(9600, SERIAL_8N1, 16, 17);
// // //   delay(3000);
// // // }

// // // void updateSerial() {
// // //   delay(500);
// // //   Serial.println(gps.encode(gpsSerial.read()).location.isValid());
// // //   while (Serial.available()) {
// // //     Serial2.write(Serial.read());
// // //   }

// // //   while (Serial2.available()) {
// // //     Serial.write(Serial2.read());
// // //   }

// // //   while (gpsSerial.available()) {
// // //     Serial.println(gpsSerial.read());
// // //   }
// // // }

// // // void loop() {
// // //   updateSerial();
// // // }

// // // esp8266
// // /*
// //  * This ESP8266 NodeMCU code was developed by newbiely.com
// //  *
// //  * This ESP8266 NodeMCU code is made available for public use without any restriction
// //  *
// //  * For comprehensive instructions and wiring diagrams, please visit:
// //  * https://newbiely.com/tutorials/esp8266/esp8266-gps
// //  */

// // // #include <TinyGPS++.h>
// // // #include <SoftwareSerial.h>

// // // const int RX_PIN = 3, TX_PIN = 4;
// // // const uint32_t GPS_BAUD = 9600; //Default baud of NEO-6M is 9600


// // // TinyGPSPlus gps; // The TinyGPS++ object
// // // SoftwareSerial gpsSerial(RX_PIN, TX_PIN); // The serial interface to the GPS device

// // // void setup() {
// // //   Serial.begin(9600);
// // //   gpsSerial.begin(GPS_BAUD);

// // //   Serial.println(F("ESP8266 - GPS module"));
// // // }

// // // void loop() {
// // //   if (gpsSerial.available() > 0) {
// // //     if (gps.encode(gpsSerial.read())) {
// // //       if (gps.location.isValid()) {
// // //         Serial.print(F("- latitude: "));
// // //         Serial.println(gps.location.lat());

// // //         Serial.print(F("- longitude: "));
// // //         Serial.println(gps.location.lng());

// // //         Serial.print(F("- altitude: "));
// // //         if (gps.altitude.isValid())
// // //           Serial.println(gps.altitude.meters());
// // //         else
// // //           Serial.println(F("INVALID"));
// // //       } else {
// // //         Serial.println(F("- location: INVALID"));
// // //       }

// // //       Serial.print(F("- speed: "));
// // //       if (gps.speed.isValid()) {
// // //         Serial.print(gps.speed.kmph());
// // //         Serial.println(F(" km/h"));
// // //       } else {
// // //         Serial.println(F("INVALID"));
// // //       }

// // //       Serial.print(F("- GPS date&time: "));
// // //       if (gps.date.isValid() && gps.time.isValid()) {
// // //         Serial.print(gps.date.year());
// // //         Serial.print(F("-"));
// // //         Serial.print(gps.date.month());
// // //         Serial.print(F("-"));
// // //         Serial.print(gps.date.day());
// // //         Serial.print(F(" "));
// // //         Serial.print(gps.time.hour());
// // //         Serial.print(F(":"));
// // //         Serial.print(gps.time.minute());
// // //         Serial.print(F(":"));
// // //         Serial.println(gps.time.second());
// // //       } else {
// // //         Serial.println(F("INVALID"));
// // //       }

// // //       Serial.println();
// // //     }
// // //   }

// // //   if (millis() > 5000 && gps.charsProcessed() < 10)
// // //     Serial.println(F("No GPS data received: check wiring"));
// // // }

// #include <TinyGPS++.h>
// //#include <SoftwareSerial.h>
// // /*
// //    This sample sketch demonstrates the normal use of a TinyGPS++ (TinyGPSPlus) object.
// //    It requires the use of SoftwareSerial, and assumes that you have a
// //    4800-baud serial GPS device hooked up on pins 4(rx) and 3(tx).
// // */
// // // static const int RXPin = 4, TXPin = 3;
// static const uint32_t GPSBaud = 9600;

// // // The TinyGPS++ object
// TinyGPSPlus gps;

// // // The serial connection to the GPS device
// // //SoftwareSerial ss(RXPin, TXPin);
// // HardwareSerial ss(2);

// // void setup()
// // {
// //   Serial.begin(9600);
// //   ss.begin(GPSBaud, SERIAL_8N1, 16, 17);

// //   Serial.println(F("DeviceExample.ino"));
// //   Serial.println(F("A simple demonstration of TinyGPS++ with an attached GPS module"));
// //   Serial.print(F("Testing TinyGPS++ library v. ")); Serial.println(TinyGPSPlus::libraryVersion());
// //   Serial.println(F("by Mikal Hart"));
// //   Serial.println();
// // }
// //   unsigned int lastErr = 0;
// //   bool start = false;

// // void loop()
// // {
// //   // This sketch displays information every time a new sentence is correctly encoded.
// //   // Serial.println(ss.read());


// //   while (ss.available() > 0)
// //     if (gps.encode(ss.read()))
// //       displayInfo();

// //   if (millis() > 5000 && gps.charsProcessed() < 10)
// //   {
// //     if (millis() - lastErr > 1000) {
// //       lastErr = millis();
// //       Serial.println(F("No GPS detected: check wiring."));
// //     }    
// //   }
// // }

// // void displayInfo()
// // {
// //   Serial.print(F("Location: ")); 
// //   if (gps.location.isValid())
// //   {
// //     Serial.print(gps.location.lat(), 6);
// //     Serial.print(F(","));
// //     Serial.print(gps.location.lng(), 6);
// //   }
// //   else
// //   {
// //     Serial.print(F("INVALID"));
// //   }

// //   Serial.print(F("  Date/Time: "));
// //   if (gps.date.isValid())
// //   {
// //     Serial.print(gps.date.month());
// //     Serial.print(F("/"));
// //     Serial.print(gps.date.day());
// //     Serial.print(F("/"));
// //     Serial.print(gps.date.year());
// //   }
// //   else
// //   {
// //     Serial.print(F("INVALID"));
// //   }

// //   Serial.print(F(" "));
// //   if (gps.time.isValid())
// //   {
// //     // Adjust time to Malaysian Time (UTC +8)
// //     int hour = gps.time.hour() + 8;
// //     if (hour >= 24) {
// //       hour -= 24;
// //     }

// //     if (hour < 10) Serial.print(F("0"));
// //     Serial.print(hour);
// //     Serial.print(F(":"));
// //     if (gps.time.minute() < 10) Serial.print(F("0"));
// //     Serial.print(gps.time.minute());
// //     Serial.print(F(":"));
// //     if (gps.time.second() < 10) Serial.print(F("0"));
// //     Serial.print(gps.time.second());
// //     Serial.print(F("."));
// //     if (gps.time.centisecond() < 10) Serial.print(F("0"));
// //     Serial.print(gps.time.centisecond());
// //   }
// //   else
// //   {
// //     Serial.print(F("INVALID"));
// //   }

// //   Serial.println();
// // }

// // // send http request over wifi

// // #include <WiFi.h>
// // #include <HTTPClient.h>
// // #include <ArduinoJson.h>

// // const char* SSID = "PSIS WiFi";
// // const char* PASSWORD = "";

// // const String serverName = "http://192.168.200.65:8766";

// // String api(String path) {
// //   return serverName + path;
// // }

// // unsigned long lastTime = 0;
// // unsigned long timerDelay = 2000; // every 2 seconds

// // void setup() {
// //   Serial.begin(115200);
// //   WiFi.begin(SSID, PASSWORD);

// //   Serial.print("Connecting");
// //   while( WiFi.status() != WL_CONNECTED) {
// //     delay(500);
// //     Serial.print(".");
// //   }

// //   Serial.println();
// //   Serial.print("Connected to WiFi with ip: ");
// //   Serial.print(WiFi.localIP());
// //   Serial.println("");
// //   Serial.println("Timer set to 2 seconds (timerDelay variable), it will take 5 seconds before publishing the first reading.");
// // }

// // void loop() {
// //   //Send an HTTP POST request every 10 minutes
// //   if ((millis() - lastTime) > timerDelay) {
// //     //Check WiFi connection status
// //     if(WiFi.status()== WL_CONNECTED){
// //       HTTPClient http;

// //       String serverPath = api("/ping");
      

// //       http.begin(serverPath.c_str());

// //       http.addHeader("Content-Type: application/json")

// //       String J
      
      
// //       // Send HTTP GET request
// //       int httpResponseCode = http.GET();
      
// //       if (httpResponseCode>0) {
// //         Serial.print("HTTP Response code: ");
// //         Serial.println(httpResponseCode);
// //         String payload = http.getString();
// //         Serial.println(payload);
// //       }
// //       else {
// //         Serial.print("Error code: ");
// //         Serial.println(httpResponseCode);
// //       }
// //       // Free resources
// //       http.end();
// //     }
// //     else {
// //       Serial.println("WiFi Disconnected");
// //     }
// //     lastTime = millis();
// //   }
// // }

#include <WiFi.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <TinyGPS++.h>


const char* SSID = "PSIS WiFi";
const char* PASSWORD = "";

HardwareSerial GPSSerial(2);
TinyGPSPlus


void setup() {

}

void loop() {

}

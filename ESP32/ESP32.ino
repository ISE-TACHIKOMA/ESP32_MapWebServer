#include <WiFi.h>
#include <WebServer.h>
#include <SPI.h>
#include <SD.h>

// ====== Wi-Fi AP 設定 ======
const char* ap_ssid     = "ESP32_MAP";
const char* ap_password = "12345678";

// ====== Webサーバ ======
WebServer server(80);

// ====== 地図タイルのズーム範囲 ======
const int MIN_ZOOM = 5;
const int MAX_ZOOM = 12;

// ====== 疑似GPSエリア（琵琶湖中心） ======
double currentLat = 35.25;
double currentLon = 136.00;
unsigned long lastUpdateMillis = 0;
const unsigned long UPDATE_INTERVAL_MS = 1000;

double deltaLat = 10.0 / 111000.0;
double deltaLon = 10.0 / 90000.0;

// =====================================
// ★ HTML（Leaflet + オフラインタイル）
// =====================================
const char MAIN_page[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ESP32 Offline Map Demo</title>
<link rel="stylesheet" href="/leaflet/leaflet.css"/>

<style>
  body { margin:0; padding:0; background:#202020; color:white; }
  #map { width:100vw; height:100vh; }
</style>
</head>

<body>
<div id="map"></div>

<script src="/leaflet/leaflet.js"></script>
<script>
var map = L.map('map').setView([35.25, 136.00], 12);

L.tileLayer('/tiles/{z}/{x}/{y}.png', {
    minZoom: 5,
    maxZoom: 12,
    attribution: ''
}).addTo(map);

var marker = L.marker([35.25, 136.00]).addTo(map);

function updatePos() {
  fetch('/position')
    .then(r => r.json())
    .then(p => {
        marker.setLatLng([p.lat, p.lon]);
        map.setView([p.lat, p.lon]);
    });
}

setInterval(updatePos, 1000);
updatePos();
</script>

</body>
</html>
)rawliteral";

// =====================================
// ★ 疑似GPS更新（1秒ごと +10m）
// =====================================
void updateFakeGPS() {
  unsigned long now = millis();
  if (now - lastUpdateMillis < UPDATE_INTERVAL_MS) return;

  lastUpdateMillis = now;

  double dlat = ((double)random(-100,101) / 100.0) * deltaLat;
  double dlon = ((double)random(-100,101) / 100.0) * deltaLon;

  currentLat += dlat;
  currentLon += dlon;
}

// =====================================
// ★ 位置情報を返す (/position)
// =====================================
void handlePosition() {
  unsigned long t = millis()/1000;

  String json = "{";
  json += "\"lat\":"  + String(currentLat, 6) + ",";
  json += "\"lon\":"  + String(currentLon, 6) + ",";
  json += "\"time\":" + String(t);
  json += "}";

  server.send(200, "application/json", json);
}

// =====================================
// ★ タイル返却 (/tiles/z/x/y.png)
// =====================================
void handleTiles() {
  String path = server.uri(); // "/tiles/8/230/112.png"
  File f = SD.open(path);
  if (!f) {
    server.send(404, "text/plain", "Tile not found");
    return;
  }
  server.streamFile(f, "image/png");
  f.close();
}

// =====================================
// ★ Leafletファイル返却 (/leaflet/...)
// =====================================
void handleLeaflet() {
  String path = server.uri(); // "/leaflet/leaflet.js"
  File f = SD.open(path);
  if (!f) {
    server.send(404, "text/plain", "Leaflet file not found");
    return;
  }

  if (path.endsWith(".css")) server.streamFile(f, "text/css");
  else if (path.endsWith(".js")) server.streamFile(f, "application/javascript");
  else if (path.endsWith(".png")) server.streamFile(f, "image/png");
  else server.streamFile(f, "application/octet-stream");

  f.close();
}


// =====================================
// ★ SD初期化
// =====================================
bool initSD() {
  if (!SD.begin(21)) {
    Serial.println("[SD] 初期化失敗");
    return false;
  }
  Serial.println("[SD] 初期化成功");
  return true;
}

// =====================================
// ★ setup
// =====================================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("===== ESP32 Offline Tile Map Demo =====");

  randomSeed(analogRead(0));

  if (!initSD()) {
    Serial.println("[SD] ERROR");
  }

  WiFi.mode(WIFI_AP);
  WiFi.softAP(ap_ssid, ap_password);
  Serial.print("[WiFi] AP IP: ");
  Serial.println(WiFi.softAPIP());

  server.on("/", []() {
    server.send_P(200, "text/html", MAIN_page);
  });

  server.on("/position", handlePosition);

  // タイル
  server.onNotFound([]() {
    String path = server.uri();
    if (path.startsWith("/tiles/")) {
      handleTiles();
    }
    else if (path.startsWith("/leaflet/")) {
      handleLeaflet();
    }
    else {
      server.send(404, "text/plain", "Not found");
    }
  });

  server.begin();
  Serial.println("[HTTP] Webサーバ起動");
}

// =====================================
// ★ loop
// =====================================
void loop() {
  updateFakeGPS();
  server.handleClient();
}

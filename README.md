# ESP32 Offline Map GPS Demo  
ESP32-S3 を使用した **完全オフライン地図表示 + 疑似GPSトラッキング**のデモです。  
Leaflet（JavaScript地図ライブラリ）を **SDカードからローカル配信**するため、  
インターネットが全く不要で、ESP32 単体で地図アプリを構築できます。

スマホ・PC を ESP32 の Wi-Fi に接続するだけで、  
ブラウザで地図を表示し、現在位置（疑似GPS）がリアルタイムで動きます。

---

# ✨ Features

### ✔ 完全オフライン地図（Leaflet を SD から配信）
- Leaflet.js / Leaflet.css / 画像をすべて SD から読み込み
- 地図タイル（PNG）も SD から読み込み

### ✔ ESP32 が Wi-Fi AP になる（インターネット不要）
- SSID: `ESP32_MAP`
- パスワード: `12345678`
- ブラウザで `http://192.168.4.1/` にアクセス

### ✔ 疑似GPSを1秒ごとに更新・地図上に反映
- 琵琶湖中央からスタート
- 1秒ごとに ±10m ランダム移動
- `/position` に JSON で返す

### ✔ SDカードに GPS ログを保存（CSV）
- `gps_log.csv` 形式で緯度・経度・時刻を追記
- 実際の GPS（NEO-6M 等）に置換可能

### ✔ Web UI は Leaflet ベース（ズーム・パン自由）
- OpenStreetMap タイル互換 PNG
- ズーム5〜12をデフォルトで使用

---

# 📂 SD カード構成（必ずこの通りに配置）

```plaintext
/sdcard/
├── leaflet/
│   ├── leaflet.js
│   ├── leaflet.css
│   └── images/
│       ├── marker-icon.png
│       ├── marker-shadow.png
│       ├── layers.png
│       └── layers-2x.png
├── tiles/
│   ├── 5/
│   ├── 6/
│   ├── 7/
│   ├── ...
│   └── 12/
└── gps_log.csv （自動生成されます）
```


## Leaflet の取得方法
Leaflet 公式 ZIP をダウンロードして SD カードへコピーします：

https://leafletjs.com/download.html

必要ファイル：
- leaflet.js  
- leaflet.css  
- images/ フォルダ（アイコン類）

---

# 🌏 地図タイルの生成方法（Python スクリプト）

国土地理院タイルなどから **日本全域タイル（PNG）を自動ダウンロードするスクリプト**：

```python
import os
import math
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

min_lat, max_lat = 24.0, 46.0
min_lon, max_lon = 123.0, 146.0
min_zoom = 5
max_zoom = 12

BASE_DIR = "tiles"
TILE_URL = "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png"
MAX_WORKERS = 8

def latlon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2**zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1/math.cos(lat_rad)) / math.pi)/2 * n)
    return xtile, ytile

def download_tile(z, x, y):
    url = TILE_URL.format(z=z, x=x, y=y)
    save_path = f"{BASE_DIR}/{z}/{x}/{y}.png"
    if os.path.exists(save_path):
        return
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(r.content)

def main():
    for zoom in range(min_zoom, max_zoom + 1):
        min_x, min_y = latlon_to_tile(max_lat, min_lon, zoom)
        max_x, max_y = latlon_to_tile(min_lat, max_lon, zoom)
        tasks = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    tasks.append(executor.submit(download_tile, zoom, x, y))
            for _ in as_completed(tasks):
                pass

if __name__ == "__main__":
    main()

```
# 🧭 ESP32 側スケッチ概要
主要エンドポイント
パス	内容
/	地図ページ（Leaflet）
/position	疑似GPSの緯度経度 JSON
/tiles/...	地図タイル PNG
/leaflet/...	Leaflet.js / CSS / image
疑似GPSの挙動

琵琶湖中央から開始

毎秒 ±10m程度ランダム移動

/position で以下を返す：
```json
{
  "lat": 35.250123,
  "lon": 136.001234,
  "time": 123
}
```

# 💻 使い方
1. ESP32 にスケッチを書き込む

Arduino IDE / PlatformIO でビルドして書き込み。

2. ESP32 に接続
SSID	ESP32_MAP
Password	12345678
3. ブラウザでアクセス
```cpp
http://192.168.4.1
```

# 📸 動作イメージ（スクリーンショット例）
![スクリーンショット](/docs/demo.png)
![スクリーンショット2](/docs/demo2.png)

# 🔧 技術構成
使用ライブラリ

ESP32 WiFi

WebServer

SD (SPI)

Leaflet.js

HTML5 + JavaScript

通信方式

HTTP

JSON

SD ファイルストリーム

# 🔮 拡張案（Future Work）

本物の GPS モジュール（NEO-6M / ZED-F9P 等）へ接続

LoRa / LTE（SIM7080G）で位置共有

海図タイル対応（海上用途）

軌跡の Polyline 表示

地図キャッシュ圧縮（WebP）

複数デバイス同時表示

# 📜 License

MIT License

# 👤 Author

ISE_TACHIKOMA
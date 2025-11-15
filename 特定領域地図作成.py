import math
import requests
from PIL import Image
from io import BytesIO

# ===== 地図領域（ESP32側と合わせる） =====
MIN_LAT = 35.5
MAX_LAT = 35.75
MIN_LON = 140.0
MAX_LON = 140.25

# ===== タイルズーム =====
ZOOM = 12  # 10〜15の間で調整可能

# ===== 出力画像サイズ =====
OUT_W = 800
OUT_H = 600
OUTPUT_FILE = "map.png"

# ===== 国土地理院タイル（標準地図） =====
TILE_URL = "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png"

# -----------------------------------------------------
def latlon_to_pixels(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n * 256
    y = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n * 256
    return (x, y)

# -----------------------------------------------------
print("Calculating tile range...")

x_min, y_max = latlon_to_pixels(MIN_LAT, MIN_LON, ZOOM)
x_max, y_min = latlon_to_pixels(MAX_LAT, MAX_LON, ZOOM)

tile_x_min = int(x_min // 256)
tile_x_max = int(x_max // 256)
tile_y_min = int(y_min // 256)
tile_y_max = int(y_max // 256)

tiles_w = tile_x_max - tile_x_min + 1
tiles_h = tile_y_max - tile_y_min + 1
canvas = Image.new("RGB", (tiles_w * 256, tiles_h * 256))

print("Downloading tiles...")

for ty in range(tile_y_min, tile_y_max + 1):
    for tx in range(tile_x_min, tile_x_max + 1):
        url = TILE_URL.format(z=ZOOM, x=tx, y=ty)
        r = requests.get(url)
        if r.status_code == 200:
            im = Image.open(BytesIO(r.content))
        else:
            print("Missing tile:", url)
            im = Image.new("RGB", (256, 256), (255, 255, 255))

        px = (tx - tile_x_min) * 256
        py = (ty - tile_y_min) * 256
        canvas.paste(im, (px, py))

# -----------------------------------------------------
print("Cropping...")

px_min = int(x_min - tile_x_min * 256)
px_max = int(x_max - tile_x_min * 256)
py_min = int(y_min - tile_y_min * 256)
py_max = int(y_max - tile_y_min * 256)

crop = canvas.crop((px_min, py_min, px_max, py_max))

print("Resizing...")
out = crop.resize((OUT_W, OUT_H), Image.LANCZOS)
out.save(OUTPUT_FILE)
print("Saved:", OUTPUT_FILE)

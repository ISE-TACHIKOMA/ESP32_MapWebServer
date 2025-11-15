import os
import math
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ============================================
# ★ 設定項目
# ============================================

# 日本の範囲（ざっくり）
min_lat, max_lat = 20.0, 46.0
min_lon, max_lon = 122.0, 154.0

min_zoom = 5
max_zoom = 12

# タイル保存先
BASE_DIR = "tiles"

# 国土地理院標準地図タイル
TILE_URL = "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png"

# 1秒あたりの最大リクエスト（マナー）
MAX_WORKERS = 8


# ============================================
# ★ 緯度経度 → タイル番号変換
# ============================================

def latlon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


# ============================================
# ★ タイルダウンロード
# ============================================

def download_tile(z, x, y):
    url = TILE_URL.format(z=z, x=x, y=y)
    save_path = f"{BASE_DIR}/{z}/{x}/{y}.png"

    # すでにDL済みならスキップ
    if os.path.exists(save_path):
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
        else:
            print(f"[SKIP] z={z} x={x} y={y} (status {r.status_code})")
    except Exception as e:
        print(f"[ERROR] {z}/{x}/{y} - {e}")


# ============================================
# ★ メイン処理
# ============================================

def main():
    print("=== 日本全域タイルダウンロード開始 ===")

    for zoom in range(min_zoom, max_zoom + 1):
        print(f"\n--- Zoom {zoom} ---")

        # 緯度経度→タイル範囲変換
        min_x, min_y = latlon_to_tile(max_lat, min_lon, zoom)  # 注意：lat逆
        max_x, max_y = latlon_to_tile(min_lat, max_lon, zoom)

        print(f"タイル範囲: x={min_x}〜{max_x}, y={min_y}〜{max_y}")
        total_tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
        print(f"タイル総数: {total_tiles}")

        # 並列ダウンロード
        tasks = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    tasks.append(executor.submit(download_tile, zoom, x, y))

            for future in as_completed(tasks):
                pass

        print(f"Zoom {zoom} 完了")

    print("\n=== 完了しました ===")
    print("→ SDカードに tiles/ フォルダごと入れれば ESP32 で使用できます")


if __name__ == "__main__":
    main()

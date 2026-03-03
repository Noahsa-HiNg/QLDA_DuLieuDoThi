import requests
from datetime import datetime
import math
import csv
import os
import random
import time
import folium
import json

# ============================================================
# CONFIG TOÀN CỤC - TẤT CẢ THAM SỐ CHỈNH SỬA ĐỀU Ở ĐÂY
# ============================================================

CONFIG = {
    # Cấu hình API TomTom
    "API": {
        # ⚠️ THAY BẰNG API KEY CỦA BẠN
        "TOMTOM_API_KEY": "ixWGJspbZGL07g4DUYYpznMJUn9nXPvC",
        # Mức zoom cho Traffic Flow (zoom càng lớn, segment càng ngắn)
        "FLOW_ZOOM_LEVEL": 10,
        # Timeout (giây) cho mỗi request
        "TIMEOUT_SECONDS": 10,
    },

    # Danh sách điểm cần giám sát ở Đà Nẵng đã được chuyển sang file json
    "MONITORED_POINTS_FILE": "data/MONITORED_POINTS.json",

    # Cấu hình ingestion (thu thập realtime)
    "INGESTION": {
        # Khoảng thời gian giữa 2 lần thu thập (giây)
        "POLL_INTERVAL_SECONDS": 10,
        # Số vòng lặp (None = loop vô hạn đến khi Ctrl + C)
        "MAX_ITERATIONS": 1,
    },

    # Cấu hình I/O
    "IO": {
        # Đường dẫn file CSV output
        "OUTPUT_CSV": "data/real_traffic_data.csv",
        # Đường dẫn file HTML để vẽ bản đồ
        "OUTPUT_MAP_HTML": "data/traffic_map_danang.html",
        "OUTPUT_CSV_EXTENDED": "data/real_traffic_data_extended.csv",
        "EXTENDED_COLUMNS": [
            "timestamp",
            "street_name",
            "vehicle_count",
            "average_speed",
            "congestion_level",
            "lat",
            "lon",
            "free_flow_speed",
            "point_id",
            "description",
        ],
    },
}


# ============================================================
# HẰNG SỐ URL API
# ============================================================

FLOW_BASE_URL_TEMPLATE = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/{zoom}/json"
)

REVERSE_GEOCODE_URL_TEMPLATE = (
    "https://api.tomtom.com/search/2/reverseGeocode/{lat},{lon}.json"
)


# ============================================================
# TIỆN ÍCH CHUNG
# ============================================================

def get_current_timestamp_utc() -> str:
    """Trả về timestamp ISO 8601 theo UTC."""
    return datetime.utcnow().isoformat()


def ensure_parent_dir(path: str) -> None:
    """Đảm bảo thư mục cha của path tồn tại."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def calculate_new_coordinate(lat, lon, brng, distance_km):
    """
    Tính tọa độ mới phát sinh từ một điểm (lat, lon) đi theo hướng brng (độ)
    với khoảng cách distance_km (dùng công thức Haversine/trái đất hình cầu).
    """
    R = 6371.0 # Bán kính trái đất (km)
    brng = math.radians(brng)

    lat1 = math.radians(lat)
    lon1 = math.radians(lon)

    lat2 = math.asin(math.sin(lat1) * math.cos(distance_km / R) +
                     math.cos(lat1) * math.sin(distance_km / R) * math.cos(brng))

    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(distance_km / R) * math.cos(lat1),
                             math.cos(distance_km / R) - math.sin(lat1) * math.sin(lat2))

    return math.degrees(lat2), math.degrees(lon2)


def generate_subpoints_for_route(point_cfg: dict) -> list[dict]:
    """
    Dựa vào điểm gốc ban đầu, hướng đi (route_heading) và chiều dài đoạn đường (route_length_km),
    tạo ra các điểm con cách nhau ngẫu nhiên từ 200m - 400m dọc theo tuyến.
    Nếu điểm không có thông số tuyến, trả về chính nó.
    """
    if "route_length_km" not in point_cfg or "route_heading" not in point_cfg:
        return [point_cfg]
        
    subpoints = []
    total_len = point_cfg["route_length_km"]
    heading = point_cfg["route_heading"]
    start_lat = point_cfg["lat"]
    start_lon = point_cfg["lon"]
    base_id = point_cfg["id"]
    desc = point_cfg["description"]
    
    current_dist = 0.0
    idx = 1
    
    # Điểm gốc
    subpoints.append({
        "id": f"{base_id}_sub{idx}",
        "description": f"{desc} (0m)",
        "lat": start_lat,
        "lon": start_lon
    })
    
    while current_dist < total_len:
        # Nhảy 1 khoảng từ 200m -> 400m
        jump_km = random.uniform(0.2, 0.4)
        current_dist += jump_km
        
        if current_dist > total_len:
            break
            
        idx += 1
        new_lat, new_lon = calculate_new_coordinate(start_lat, start_lon, heading, current_dist)
        
        subpoints.append({
            "id": f"{base_id}_sub{idx}",
            "description": f"{desc} ({int(current_dist * 1000)}m)",
            "lat": round(new_lat, 6),
            "lon": round(new_lon, 6)
        })
        
    return subpoints


# ============================================================
# LAYER 1: API CLIENT (TomTom Traffic & Reverse Geocode)
# ============================================================

def get_traffic_flow(api_key: str, lat: float, lon: float, zoom: int, timeout: int):
    """
    Gọi TomTom Traffic Flow Segment Data API cho một tọa độ (lat, lon).
    Trả về dict flowSegmentData hoặc None nếu lỗi.
    """
    base_url = FLOW_BASE_URL_TEMPLATE.format(zoom=zoom)
    params = {
        "key": api_key,
        "point": f"{lat},{lon}",
        "unit": "KMPH",
    }

    try:
        resp = requests.get(base_url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("flowSegmentData")
    except requests.RequestException as e:
        print(f"[TrafficFlow] Lỗi khi gọi API tại ({lat}, {lon}): {e}")
        return None


def reverse_geocode_street_name(api_key: str, lat: float, lon: float, timeout: int) -> str:
    """
    Dùng TomTom Reverse Geocoding để lấy tên đường gần nhất.
    Nếu lỗi hoặc không có dữ liệu, trả về 'Unknown'.
    """
    url = REVERSE_GEOCODE_URL_TEMPLATE.format(lat=lat, lon=lon)
    params = {
        "key": api_key,
        "radius": 50,  # bán kính tìm kiếm 50m quanh điểm
    }

    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[ReverseGeocode] Lỗi tại ({lat}, {lon}): {e}")
        return "Unknown"

    addresses = data.get("addresses", [])
    if not addresses:
        return "Unknown"

    addr = addresses[0].get("address", {})
    street_name = addr.get("streetName") or addr.get("freeformAddress") or "Unknown"
    return street_name


# ============================================================
# LAYER 2: BUSINESS LOGIC / DOMAIN
# ============================================================

def compute_congestion_level(current_speed, free_flow_speed) -> int:
    """
    Tính mức độ kẹt xe (0-3) dựa trên tỉ lệ current_speed / free_flow_speed.
    0: thông thoáng, 1: hơi đông, 2: đông, 3: kẹt nặng
    """
    if not current_speed or not free_flow_speed or free_flow_speed == 0:
        return 0

    ratio = current_speed / free_flow_speed

    if ratio > 0.8:
        return 0  # thông thoáng
    elif ratio > 0.6:
        return 1  # hơi đông
    elif ratio > 0.4:
        return 2  # đông
    else:
        return 3  # kẹt nặng


def estimate_vehicle_count(congestion_level: int) -> int:
    """
    Giả lập số lượng xe trên đoạn đường dựa vào congestion_level.
    Có thể chỉnh lại range cho phù hợp với thực tế Đà Nẵng.
    """
    if congestion_level == 0:
        return random.randint(5, 15)
    elif congestion_level == 1:
        return random.randint(20, 40)
    elif congestion_level == 2:
        return random.randint(40, 70)
    else:
        return random.randint(80, 150)


def extract_segment_coordinates(flow_segment: dict):
    """
    Trích xuất danh sách toạ độ [(lat1, lon1), (lat2, lon2), ...] từ flowSegmentData.
    """
    coords_container = flow_segment.get("coordinates", {})
    if isinstance(coords_container, dict):
        coord_list = coords_container.get("coordinate", [])
    elif isinstance(coords_container, list):
        coord_list = coords_container
    else:
        coord_list = []

    segment_coords = []
    for c in coord_list:
        la = c.get("latitude")
        lo = c.get("longitude")
        if la is not None and lo is not None:
            segment_coords.append((la, lo))

    return segment_coords


def build_observation(
    point_cfg: dict,
    flow_segment: dict,
    street_name: str,
    timestamp: str,
):
    """
    Gom toàn bộ thông tin của 1 điểm thành 1 dict observation thống nhất.
    Observation bao gồm nhiều field, nhưng CSV writer sẽ chỉ chọn ra 5 cột chuẩn.
    """
    lat = point_cfg["lat"]
    lon = point_cfg["lon"]

    current_speed = flow_segment.get("currentSpeed")
    free_flow_speed = flow_segment.get("freeFlowSpeed")

    congestion_level = compute_congestion_level(current_speed, free_flow_speed)
    vehicle_count = estimate_vehicle_count(congestion_level)
    segment_coords = extract_segment_coordinates(flow_segment)

    observation = {
        # Các field sẽ xuất ra CSV

        "timestamp": timestamp,
        "street_name": street_name,
        "vehicle_count": vehicle_count,
        "average_speed": current_speed,
        "congestion_level": congestion_level,

        # Thông tin mở rộng (không ghi vào CSV chuẩn, nhưng hữu ích cho map/phân tích)
        "lat": lat,
        "lon": lon,
        "free_flow_speed": free_flow_speed,
        "segment_coords": segment_coords,
        "point_id": point_cfg.get("id"),
        "description": point_cfg.get("description"),
    }

    return observation


# ============================================================
# LAYER 3: PERSISTENCE (CSV) & MAP
# ============================================================

def append_traffic_row(csv_path: str, observation: dict) -> None:
    """
    Ghi một dòng vào CSV với các cột:
    timestamp, street_name, vehicle_count, average_speed, congestion_level, latitude, longitude
    """
    file_exists = os.path.isfile(csv_path)
    ensure_parent_dir(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "street_name",
                "vehicle_count",
                "average_speed",
                "congestion_level",
                "latitude",
                "longitude",
            ])

        writer.writerow([
            observation["timestamp"],
            observation["street_name"],
            observation["vehicle_count"],
            observation["average_speed"],
            observation["congestion_level"],
            observation["lat"],
            observation["lon"],
        ])


def build_folium_map(observations: list, output_html: str) -> None:
    """
    Vẽ bản đồ Folium từ danh sách observation.
    Mỗi observation tương ứng với 1 đoạn (segment) với màu theo congestion_level.
    """
    if not observations:
        print("[Map] Không có dữ liệu để vẽ bản đồ.")
        return

    # Lấy điểm đầu làm center
    center_lat = observations[0]["lat"]
    center_lon = observations[0]["lon"]

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    def color_for_level(level: int) -> str:
        return {
            0: "green",
            1: "orange",
            2: "red",
            3: "darkred",
        }.get(level, "gray")

    for obs in observations:
        coords = obs.get("segment_coords") or [(obs["lat"], obs["lon"])]
        color = color_for_level(obs["congestion_level"])

        popup_html = f"""
        <b>{obs['street_name']}</b><br>
        currentSpeed: {obs['average_speed']} km/h<br>
        freeFlowSpeed: {obs.get('free_flow_speed')} km/h<br>
        congestion_level: {obs['congestion_level']}<br>
        vehicles≈{obs['vehicle_count']}<br>
        """

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=6,
            opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{obs['street_name']} - Level {obs['congestion_level']}",
        ).add_to(m)

    ensure_parent_dir(output_html)
    m.save(output_html)
    print(f"[Map] Đã cập nhật bản đồ: {output_html}")


# ============================================================
# LAYER 4: ORCHESTRATION - THU THẬP DỮ LIỆU CHO 1 ĐIỂM
# ============================================================

def collect_point_observation(
    api_config: dict,
    point_cfg: dict,
) -> dict | None:
    """
    Pipeline xử lý cho 1 điểm:
    - Gọi Traffic Flow
    - Gọi Reverse Geocode
    - Tính congestion, vehicle_count
    - Gom thành observation dict
    """
    lat = point_cfg["lat"]
    lon = point_cfg["lon"]

    flow_segment = get_traffic_flow(
        api_key=api_config["TOMTOM_API_KEY"],
        lat=lat,
        lon=lon,
        zoom=api_config["FLOW_ZOOM_LEVEL"],
        timeout=api_config["TIMEOUT_SECONDS"],
    )

    if not flow_segment:
        return None

    street_name = reverse_geocode_street_name(
        api_key=api_config["TOMTOM_API_KEY"],
        lat=lat,
        lon=lon,
        timeout=api_config["TIMEOUT_SECONDS"],
    )

    timestamp = get_current_timestamp_utc()

    observation = build_observation(
        point_cfg=point_cfg,
        flow_segment=flow_segment,
        street_name=street_name,
        timestamp=timestamp,
    )

    return observation


# ============================================================
# LAYER 5: MAIN LOOP - INGESTION REALTIME
# ============================================================

def run_ingestion_loop():
    api_config = CONFIG["API"]
    ingestion_cfg = CONFIG["INGESTION"]
    io_cfg = CONFIG["IO"]
    points_file = CONFIG.get("MONITORED_POINTS_FILE", "data/MONITORED_POINTS.json")

    # Load points
    try:
        with open(points_file, "r", encoding="utf-8") as f:
            points = json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc file giám sát ({points_file}): {e}")
        return

    csv_path = io_cfg["OUTPUT_CSV"]
    map_html = io_cfg["OUTPUT_MAP_HTML"]
    interval = ingestion_cfg["POLL_INTERVAL_SECONDS"]
    max_iter = ingestion_cfg["MAX_ITERATIONS"]

    print("=== BẮT ĐẦU THU THẬP DỮ LIỆU REALTIME TỪ TOMTOM ===")
    print(f"Số điểm giám sát: {len(points)}")
    print(f"Chu kỳ: {interval} giây / lần")
    print(f"File CSV: {csv_path}")

    iteration = 0
    while True:
        iteration += 1
        print(f"\n--- Lần thu thập #{iteration} ---")

        observations_for_map = []

        for base_p in points:
            # Phát sinh các điểm con dọc theo tuyến nếu có yêu cầu (200m-400m)
            subpoints = generate_subpoints_for_route(base_p)
            
            for p in subpoints:
                print(f"Điểm: {p['id']} - {p['description']} "
                      f"({p['lat']}, {p['lon']})")
    
                obs = collect_point_observation(api_config, p)
                if obs is None:
                    print("  → Lỗi khi xử lý điểm này, bỏ qua.")
                    continue
    
                # Ghi CSV
                append_traffic_row(csv_path, obs)
                observations_for_map.append(obs)
    
                print(f"  → street: {obs['street_name']}, "
                      f"speed: {obs['average_speed']} km/h, "
                      f"congestion: {obs['congestion_level']}, "
                      f"vehicles≈{obs['vehicle_count']}")

        # Sau khi xử lý xong tất cả điểm, cập nhật bản đồ
        if observations_for_map:
            build_folium_map(observations_for_map, map_html)

        # Kiểm soát số vòng lặp
        if max_iter is not None and iteration >= max_iter:
            print("Đã đạt số vòng lặp tối đa, dừng chương trình.")
            break

        print(f"Chờ {interval} giây trước lần tiếp theo...")
        time.sleep(interval)


if __name__ == "__main__":
    run_ingestion_loop()

import requests
import folium
from datetime import datetime

# ================== CẤU HÌNH ==================
TOMTOM_API_KEY = "ixWGJspbZGL07g4DUYYpznMJUn9nXPvC"  # TODO: Thay bằng API key thật
FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

# Tọa độ trung tâm Đà Nẵng
CENTER_LAT = 16.061
CENTER_LON = 108.223


def get_traffic_flow(lat: float, lon: float):
    """
    Gọi TomTom Traffic Flow Segment Data API cho một tọa độ (lat, lon).
    Trả về JSON hoặc None nếu lỗi.
    """
    params = {
        "key": TOMTOM_API_KEY,
        "point": f"{lat},{lon}",
        "unit": "KMPH",
    }

    try:
        resp = requests.get(FLOW_URL, params=params, timeout=10)
        print("Status code:", resp.status_code)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print("Lỗi khi gọi TomTom API:", e)
        return None


def calculate_congestion_level(current_speed, free_flow_speed):
    """
    Tính congestion_level = 0..3 dựa trên tỉ lệ tốc độ hiện tại / tốc độ lý tưởng.
    Bạn có thể tinh chỉnh lại ngưỡng nếu muốn.
    """
    if current_speed is None or free_flow_speed in (None, 0):
        return None

    ratio = current_speed / free_flow_speed

    if ratio > 0.8:
        return 0  # thông thoáng
    elif ratio > 0.6:
        return 1  # hơi đông
    elif ratio > 0.4:
        return 2  # đông
    else:
        return 3  # kẹt nặng


def get_congestion_color(level):
    """
    Đổi congestion_level -> màu hiển thị trên bản đồ.
    """
    mapping = {
        0: "green",
        1: "orange",
        2: "red",
        3: "darkred",
    }
    return mapping.get(level, "gray")


def create_map(flow_data, center_lat, center_lon, output_html="traffic_map.html"):
    """
    Tạo bản đồ Folium hiển thị đoạn đường + thông tin kẹt xe.
    """
    flow_segment = flow_data.get("flowSegmentData", {})

    current_speed = flow_segment.get("currentSpeed")
    free_flow_speed = flow_segment.get("freeFlowSpeed")
    current_tt = flow_segment.get("currentTravelTime")
    freeflow_tt = flow_segment.get("freeFlowTravelTime")
    confidence = flow_segment.get("confidence")

    congestion_level = calculate_congestion_level(current_speed, free_flow_speed)
    congestion_color = get_congestion_color(congestion_level)

    # Lấy danh sách điểm của segment
    coords_container = flow_segment.get("coordinates", {})
    if isinstance(coords_container, dict):
        coord_list = coords_container.get("coordinate", [])
    elif isinstance(coords_container, list):
        coord_list = coords_container
    else:
        coord_list = []

    # Nếu không có coords thì dùng tạm đúng tọa độ center
    if not coord_list:
        coord_list = [{"latitude": center_lat, "longitude": center_lon}]

    # Tạo bản đồ
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    # Chuẩn bị polyline từ list tọa độ
    polyline_coords = [
        (c["latitude"], c["longitude"])
        for c in coord_list
        if "latitude" in c and "longitude" in c
    ]

    # Thông tin popup hiển thị
    timestamp = datetime.utcnow().isoformat()
    popup_html = f"""
    <b>Real-time Traffic (TomTom)</b><br>
    Timestamp (UTC): {timestamp}<br>
    currentSpeed: {current_speed} km/h<br>
    freeFlowSpeed: {free_flow_speed} km/h<br>
    currentTravelTime: {current_tt} s<br>
    freeFlowTravelTime: {freeflow_tt} s<br>
    confidence: {confidence}<br>
    congestion_level: {congestion_level}
    """

    # Vẽ đoạn đường (polyline) lên map
    folium.PolyLine(
        locations=polyline_coords,
        color=congestion_color,
        weight=8,
        opacity=0.8,
        tooltip=f"Congestion level: {congestion_level}",
        popup=folium.Popup(popup_html, max_width=300),
    ).add_to(m)

    # Thêm marker tại tâm
    folium.Marker(
        location=[center_lat, center_lon],
        icon=folium.Icon(color="blue", icon="info-sign"),
        tooltip="Tâm Đà Nẵng",
    ).add_to(m)

    # Lưu bản đồ
    m.save(output_html)
    print(f"Đã tạo bản đồ: {output_html}")
    print("→ Mở file này bằng trình duyệt (Chrome/Edge/Firefox) để xem trực quan.")


if __name__ == "__main__":
    print("=== Gọi TomTom Traffic Flow API và vẽ bản đồ ===")
    print(f"Tọa độ: {CENTER_LAT}, {CENTER_LON}")

    data = get_traffic_flow(CENTER_LAT, CENTER_LON)
    if not data:
        print("Không lấy được dữ liệu từ API.")
    else:
        # In nhanh thông tin tóm tắt trên console
        fs = data.get("flowSegmentData", {})
        print("currentSpeed:", fs.get("currentSpeed"), "km/h")
        print("freeFlowSpeed:", fs.get("freeFlowSpeed"), "km/h")
        print("currentTravelTime:", fs.get("currentTravelTime"), "s")
        print("freeFlowTravelTime:", fs.get("freeFlowTravelTime"), "s")
        print("confidence:", fs.get("confidence"))

        # Tạo map trực quan
        create_map(data, CENTER_LAT, CENTER_LON, output_html="traffic_map_danang.html")
import requests
from datetime import datetime
import json
# ================== CONFIG ==================
TOMTOM_API_KEY = "ixWGJspbZGL07g4DUYYpznMJUn9nXPvC"  # TODO: Thay bằng API key thật của bạn

# Tọa độ trung tâm Đà Nẵng (có thể chỉnh sửa sau)
CENTER_LAT = 16.061
CENTER_LON = 108.223

# Endpoint Traffic Flow Segment Data (absolute)
# Docs tham khảo: https://developer.tomtom.com/traffic-api/documentation/traffic-flow/flow-segment-data
FLOW_BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
# Ở đây mình dùng zoom level = 10 (mức base). Sau này có thể chỉnh cao hơn (11-22) để chi tiết hơn.

# ================== FUNCTION GỌI API ==================
def get_traffic_flow(lat: float, lon: float):
    """
    Gọi TomTom Traffic Flow Segment Data API cho một tọa độ (lat, lon).
    Trả về JSON response (dict) hoặc None nếu lỗi.
    """
    params = {
        "key": TOMTOM_API_KEY,
        "point": f"{lat},{lon}",
        "unit": "KMPH",  # Lấy tốc độ theo km/h
    }

    try:
        response = requests.get(FLOW_BASE_URL, params=params, timeout=10)
        response.raise_for_status()  # Ném lỗi nếu HTTP status != 200
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi TomTom API: {e}")
        return None


# ================== MAIN TEST ==================
if __name__ == "__main__":
    print("=== Gọi thử TomTom Traffic Flow API tại Đà Nẵng ===")
    print(f"Tọa độ: {CENTER_LAT}, {CENTER_LON}")

    data = get_traffic_flow(CENTER_LAT, CENTER_LON)
    if data is None:
        print("Không lấy được dữ liệu từ API.")
    else:
        # In toàn bộ JSON (nếu muốn debug)
        # import json
        # print(json.dumps(data, ensure_ascii=False, indent=2))

        # In một số thông tin chính
        timestamp = datetime.utcnow().isoformat()

        flow_segment = data.get("flowSegmentData", {})
        current_speed = flow_segment.get("currentSpeed")
        free_flow_speed = flow_segment.get("freeFlowSpeed")
        current_travel_time = flow_segment.get("currentTravelTime")
        free_flow_travel_time = flow_segment.get("freeFlowTravelTime")
        confidence = flow_segment.get("confidence")

        print(f"Timestamp (UTC): {timestamp}")
        print(f"currentSpeed: {current_speed} km/h")
        print(f"freeFlowSpeed: {free_flow_speed} km/h")
        print(f"currentTravelTime: {current_travel_time} s")
        print(f"freeFlowTravelTime: {free_flow_travel_time} s")
        print(f"confidence: {confidence}")

        # Toạ độ đoạn đường (segment)
        coordinates_container = flow_segment.get("coordinates", {})
        if isinstance(coordinates_container, dict):
           coord_list = coordinates_container.get("coordinate", [])
        elif isinstance(coordinates_container, list):
           coord_list = coordinates_container
        else:
           coord_list = []
        

        print("Raw coordinates_container:")
        print(json.dumps(coordinates_container, ensure_ascii=False, indent=2))


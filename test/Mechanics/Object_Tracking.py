import cv2
import torch
from ultralytics import YOLO
from collections import deque

# Kiểm tra và chọn thiết bị
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load mô hình YOLO
try:
    model = YOLO("vumodel-2.pt").to(device)
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

# Mở file video
video_path = "car1.mp4"
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"Error opening video file: {video_path}")
    exit()

# Hàng đợi ticket
tickets = deque()

def add_ticket(number):
    """Thêm ticket vào hàng đợi."""
    tickets.append(number)

# Vùng check-in
pt1 = (511, 127)  # Điểm trên trái
pt2 = (503, 188)  # Điểm dưới phải

def set_check_in(x, y, w, h):
    """Thiết lập vùng check-in."""
    global pt1, pt2
    pt1 = (x, y)
    pt2 = (x + w, y + h)

# Vùng đích
destx = (211, 127)  # Điểm trên trái
desty = (230, 188)  # Điểm dưới phải

def set_destination(x, y, w, h):
    """Thiết lập vùng đích."""
    global destx, desty
    destx = (x, y)
    desty = (x + w, y + h)

# Dictionary lưu trữ các object đã theo dõi
tracked_ids = {}

# Hàm kiểm tra giao nhau giữa box và vùng
def is_intersect(box, pt1, pt2):
    """Kiểm tra xem box có giao với vùng (pt1, pt2) không."""
    x1, y1, x2, y2 = map(int, box)
    xa1, ya1 = min(pt1[0], pt2[0]), min(pt1[1], pt2[1])
    xa2, ya2 = max(pt1[0], pt2[0]), max(pt1[1], pt2[1])
    return not (x2 < xa1 or x1 > xa2 or y2 < ya1 or y1 > ya2)

# Thêm ticket ban đầu
add_ticket(1)
add_ticket(0)  # Sửa thứ tự để rõ ràng hơn: 0 là hợp lệ, 1 là không hợp lệ

# Vòng lặp xử lý video
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("End of video reached.")
        break

    # Chạy YOLO tracking
    try:
        results = model.track(frame, persist=True)
    except Exception as e:
        print(f"Error during tracking: {e}")
        continue

    # Sao chép frame để vẽ
    annotated_frame = frame.copy()

    # Xử lý bounding boxes
    if results[0].boxes is not None and results[0].boxes.id is not None:
        for box, conf, obj_id in zip(results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.id):
            # Lọc các box có confidence <= 0.8
            if conf <= 0.7:
                continue

            obj_id = int(obj_id)
            x1, y1, x2, y2 = map(int, box)

            # Kiểm tra vùng check-in
            if is_intersect(box, pt1, pt2):
                if obj_id not in tracked_ids and tickets:
                    tracked_ids[obj_id] = tickets.popleft()
                    print(f"Assigned ticket {tracked_ids[obj_id]} to object ID {obj_id}")

            # Kiểm tra vùng đích và ticket không hợp lệ
            if obj_id in tracked_ids and tracked_ids[obj_id] == 1 and is_intersect(box, destx, desty):
                cv2.putText(annotated_frame, "Invalid Ticket", (x1, y1 - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Vẽ bounding box
            color = (0, 0, 255) if obj_id in tracked_ids else (255, 255, 255)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

            # Hiển thị ticket
            if obj_id in tracked_ids:
                cv2.putText(annotated_frame, f"Ticket: {tracked_ids[obj_id]}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Vẽ vùng check-in và đích
    cv2.rectangle(annotated_frame, pt1, pt2, (0, 255, 0), 2)
    cv2.rectangle(annotated_frame, destx, desty, (255, 255, 0), 2)

    # Hiển thị frame
    cv2.imshow("YOLO11 Tracking", annotated_frame)

    # Thoát khi nhấn 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Giải phóng tài nguyên
cap.release()
cv2.destroyAllWindows()
print("Video processing completed.")
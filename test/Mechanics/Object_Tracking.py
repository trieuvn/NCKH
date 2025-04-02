import cv2
import torch
import json
import os
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO
from collections import deque

# Kiểm tra và chọn thiết bị
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
accuracy_limit = 0.75

# Hàm để mở hộp thoại chọn tệp video
def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Chọn tệp video",
        filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path if file_path else None

# Load mô hình YOLO
try:
    model = YOLO("vumodel-2.pt").to(device)
except Exception as e:
    print(f"Error loading model: {e}")
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

# Danh sách vùng đích (sẽ được cập nhật từ PosList)
destination_zones = []

# Dictionary lưu trữ các object đã theo dõi
tracked_ids = {}

# Hàm kiểm tra giao nhau giữa box và vùng
def is_intersect(box, pt1, pt2):
    x1, y1, x2, y2 = map(int, box)
    xa1, ya1 = min(pt1[0], pt2[0]), min(pt1[1], pt2[1])
    xa2, ya2 = max(pt1[0], pt2[0]), max(pt1[1], pt2[1])
    return not (x2 < xa1 or x1 > xa2 or y2 < ya1 or y1 > ya2)

# Hàm kiểm tra xem box có nằm trong vùng tứ giác không
def is_in_quadrilateral(box, quad_points):
    x1, y1, x2, y2 = map(int, box)
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    inside = False
    j = len(quad_points) - 1
    for i in range(len(quad_points)):
        xi, yi = quad_points[i]['x'], quad_points[i]['y']
        xj, yj = quad_points[j]['x'], quad_points[j]['y']
        if ((yi > center_y) != (yj > center_y)) and \
                (center_x < (xj - xi) * (center_y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

# Đọc file PosList
def load_poslist(video_path, poslist_file="PosList.json"):
    global destination_zones
    if not os.path.exists(poslist_file):
        print(f"Warning: {poslist_file} does not exist. Creating empty file.")
        with open(poslist_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        return []
    try:
        with open(poslist_file, 'r', encoding='utf-8') as f:
            poslist_data = json.load(f)
        video_basename = os.path.basename(video_path)
        video_name = os.path.splitext(video_basename)[0]
        exact_matches = []
        basename_matches = []
        substring_matches = []
        for key in poslist_data.keys():
            key_basename = os.path.basename(key)
            key_name = os.path.splitext(key_basename)[0]
            if key_name == video_name:
                exact_matches.append(key)
            elif video_name in key_name or key_name in video_name:
                basename_matches.append(key)
            elif video_name in key:
                substring_matches.append(key)
        if exact_matches:
            key_to_use = exact_matches[0]
            match_type = "exact match"
        elif basename_matches:
            key_to_use = basename_matches[0]
            match_type = "basename match"
        elif substring_matches:
            key_to_use = substring_matches[0]
            match_type = "substring match"
        else:
            print(f"No matching destination zones found for {video_path} in {poslist_file}")
            destination_zones = []
            return []
        destination_zones = poslist_data[key_to_use]
        print(f"Loaded {len(destination_zones)} destination zones from {poslist_file}")
        print(f"Using key: {key_to_use} ({match_type})")
    except Exception as e:
        print(f"Error loading PosList: {str(e)}")
        destination_zones = []
    return destination_zones

# Vẽ vùng đích từ PosList với màu sắc
def draw_destination_zones(frame, detected_boxes):
    """Vẽ các vùng đích lên frame với màu xanh dương nếu trống, đỏ nếu có xe."""
    for quad in destination_zones:
        points = [(point['x'], point['y']) for point in quad]
        has_vehicle = False
        for box in detected_boxes:
            if is_in_quadrilateral(box, quad):
                has_vehicle = True
                break
        color = (255, 0, 0) if not has_vehicle else (0, 0, 255)  # Xanh dương nếu trống, đỏ nếu có xe
        for i in range(len(points)):
            cv2.line(frame, points[i], points[(i + 1) % len(points)], color, 2)

# Chọn và hiển thị file PosList
def open_poslist_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Chọn file PosList",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path if file_path else "PosList.json"

# Tạo giao diện chính với nút mở video
def create_control_window():
    control_window = tk.Tk()
    control_window.title("YOLO Tracking Control")
    control_window.geometry("400x250")
    global video_path, poslist_path
    video_path = tk.StringVar()
    poslist_path = tk.StringVar(value="PosList.json")
    video_frame = tk.LabelFrame(control_window, text="Video", padx=10, pady=10)
    video_frame.pack(fill="x", padx=10, pady=5)
    path_label = tk.Label(video_frame, text="Đường dẫn video:")
    path_label.pack(anchor="w")
    path_display = tk.Label(video_frame, textvariable=video_path, wraplength=350)
    path_display.pack(fill="x", pady=5)
    open_button = tk.Button(video_frame, text="Mở Video", command=lambda: select_video(video_path))
    open_button.pack(pady=5)
    poslist_frame = tk.LabelFrame(control_window, text="PosList", padx=10, pady=10)
    poslist_frame.pack(fill="x", padx=10, pady=5)
    poslist_label = tk.Label(poslist_frame, text="Đường dẫn PosList:")
    poslist_label.pack(anchor="w")
    poslist_display = tk.Label(poslist_frame, textvariable=poslist_path, wraplength=350)
    poslist_display.pack(fill="x", pady=5)
    poslist_button = tk.Button(poslist_frame, text="Chọn PosList", command=lambda: select_poslist(poslist_path))
    poslist_button.pack(pady=5)
    process_button = tk.Button(control_window, text="Bắt đầu Xử Lý", command=lambda: process_selected_video(),
                              bg="#4CAF50", fg="white", height=2)
    process_button.pack(pady=10, fill="x", padx=10)
    control_window.mainloop()

def select_poslist(poslist_path_var):
    selected_path = open_poslist_dialog()
    if selected_path:
        poslist_path_var.set(selected_path)

def select_video(video_path_var):
    selected_path = open_file_dialog()
    if selected_path:
        video_path_var.set(selected_path)

def process_selected_video():
    global video_path, poslist_path
    video_file = video_path.get()
    poslist_file = poslist_path.get()
    if not video_file:
        print("Lỗi: Chưa chọn video.")
        return
    tickets.clear()
    add_ticket(1)
    add_ticket(0)
    tracked_ids.clear()
    load_poslist(video_file, poslist_file)
    process_video(video_file)

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file: {video_path}")
        return
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("End of video reached.")
            break
        try:
            results = model.track(frame, persist=True)
        except Exception as e:
            print(f"Error during tracking: {e}")
            continue
        annotated_frame = frame.copy()
        detected_boxes = []
        if results[0].boxes is not None and results[0].boxes.id is not None:
            for box, conf, obj_id in zip(results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.id):
                if conf <= accuracy_limit:
                    continue
                detected_boxes.append(box)
                obj_id = int(obj_id)
                x1, y1, x2, y2 = map(int, box)
                # Gán ticket khi xe vào vùng check-in
                if is_intersect(box, pt1, pt2):
                    if obj_id not in tracked_ids and tickets:
                        tracked_ids[obj_id] = tickets.popleft()
                        print(f"Assigned ticket {tracked_ids[obj_id]} to object ID {obj_id}")
                # Vẽ bounding box màu trắng
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
                # Hiển thị ticket ID nếu xe đã được gán ticket
                if obj_id in tracked_ids:
                    ticket_text = f"Ticket: {tracked_ids[obj_id]}"
                    cv2.putText(annotated_frame, ticket_text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    # Kiểm tra vùng đích và ticket không hợp lệ
                    for quad in destination_zones:
                        if is_in_quadrilateral(box, quad) and tracked_ids[obj_id] == 1:
                            cv2.putText(annotated_frame, "Invalid Ticket", (x1, y1 - 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                            break
        # Vẽ vùng check-in màu xanh lá
        cv2.rectangle(annotated_frame, pt1, pt2, (0, 255, 0), 2)
        # Vẽ các vùng đích với màu sắc tương ứng
        draw_destination_zones(annotated_frame, detected_boxes)
        # Hiển thị số ticket còn lại
        cv2.putText(annotated_frame, f"Tickets left: {len(tickets)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("YOLO Tracking with PosList", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
    print("Video processing completed.")

if __name__ == "__main__":
    create_control_window()
import cv2

from ultralytics import YOLO

# Load the YOLO11 model
model = YOLO("Models\yolov8mParking.pt")

# Open the video file
video_path = "car1.mp4"
cap = cv2.VideoCapture(video_path)

pt1 = (511, 127)
pt2 = (503, 188)

tracked_ids = set()

#Check giao nhau
def is_intersect(box, pt1, pt2):
    x1, y1, x2, y2 = map(int, box)
    xa1, ya1 = min(pt1[0], pt2[0]), min(pt1[1], pt2[1])
    xa2, ya2 = max(pt1[0], pt2[0]), max(pt1[1], pt2[1])

    return not (x2 < xa1 or x1 > xa2 or y2 < ya1 or y1 > ya2)

# Loop through the video frames
while cap.isOpened():
    # Read a frame from the video
    success, frame = cap.read()

    cv2.rectangle(frame,pt1,pt2,(0,255,0),2)

    if success:
        # Run YOLO11 tracking on the frame, persisting tracks between frames
        results = model.track(frame, persist=True)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # Kiểm tra bounding boxes
        if results[0].boxes is not None and results[0].boxes.id is not None:
            for box, obj_id in zip(results[0].boxes.xyxy, results[0].boxes.id):
                obj_id = int(obj_id)  # ID của object
                x1, y1, x2, y2 = map(int, box)

                # Nếu object đi qua vùng, lưu ID vào danh sách
                if is_intersect(box, pt1, pt2):
                    tracked_ids.add(obj_id)

                # Nếu object đã đi qua, vẽ box màu đỏ
                color = (0, 0, 255) if obj_id in tracked_ids else (255, 255, 255)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)


        # Display the annotated frame
        cv2.imshow("YOLO11 Tracking", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
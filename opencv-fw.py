import cv2
cap = cv2.VideoCapture(2)  # adjust index
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 30)

while True:
    ret, frame = cap.read()
    # frame is grayscale (NIR) or BGR (RGB) depending on filter state
    # Run lightweight pose detection here (MediaPipe, YOLOv8n-pose)
    cv2.imshow("NIR Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
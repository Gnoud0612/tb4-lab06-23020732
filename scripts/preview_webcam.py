import cv2, time

cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FPS, 5)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cv2.namedWindow("Lab 06 - Webcam preview (320x240 / 5 fps)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Lab 06 - Webcam preview (320x240 / 5 fps)", 640, 480)
print("Webcam preview starting; close the window to finish.", flush=True)
count = 0
try:
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Read failed", flush=True)
            break
        if count == 0:
            print("FIRST_REAL_FRAME", frame.shape, flush=True)
        count += 1
        cv2.imshow("Lab 06 - Webcam preview (320x240 / 5 fps)", cv2.flip(frame, 1))
        cv2.waitKey(1)
        if (
            cv2.getWindowProperty(
                "Lab 06 - Webcam preview (320x240 / 5 fps)", cv2.WND_PROP_VISIBLE
            )
            < 1
        ):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Preview frames:", count, flush=True)

import cv2
import numpy as np
import time
import serial

# Initialize serial
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)

# Load calibration
calib_data = np.load('webcam_calibration.npz')
camera_matrix = calib_data['camera_matrix']
dist_coeffs = calib_data['dist_coeff']

# Marker sizes (cm)
MARKER_SIZES = {6: 14.0, 3: 5.0}
TARGET_DISTANCE = 30.0  # cm
DISTANCE_TOLERANCE = 5.0  # ±1cm
# FORWARD_THRESHOLD = 50 #pixels
def estimate_distance(corners, marker_id):
    marker_size = MARKER_SIZES.get(marker_id, 14.0)
    rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_size, camera_matrix, dist_coeffs)
    return tvec[0][0][2]  # Z distance in cm

def detect_markers():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Camera error")
        return
    use_small = False
    aruco_dict_4 = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aruco_dict_6 = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
    parameters = cv2.aruco.DetectorParameters_create()
    last_seen = time.time()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Frame error")
                time.sleep(0.1)
                continue
            current_dict = aruco_dict_6 if use_small else aruco_dict_4
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = cv2.aruco.detectMarkers(gray, current_dict, parameters=parameters)

            if ids is not None:
                last_seen = time.time()
                marker_id = ids[0][0]
                corners = corners[0]
                
                # Calculate errors
                distance = estimate_distance(corners, marker_id)
                if not use_small and distance <= 40:
                    use_small = True
                    print("Switching to small marker")
                
                marker_center = np.mean(corners[0], axis=0)
                error_x = marker_center[0] - frame.shape[1]//2
                
                
                # Determine command
                if abs(distance - TARGET_DISTANCE) <= DISTANCE_TOLERANCE:
                    ser.write(b"STOP\n")
                    print(f"Target distance reached: {distance:.1f}cm")
                else:
                    # Send raw errors for steering
                    command = f"STEER,{error_x:.1f}\n"
                    ser.write(command.encode())
                    print(f"Steering: Xerr: {error_x:.1f}px, Dist: {distance:.1f}cm")
            else:
                if time.time() - last_seen >= 3:
                    ser.write(b"SEARCH\n")
                    print("Searching for marker...")

            #time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        cap.release()
        ser.close()

if __name__ == "__main__":
    detect_markers()

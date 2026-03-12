from EyeTracker import *
from time import perf_counter
import pygame as pg

def functionalityAndTiming():
    cap = cv2.VideoCapture(0)
    
    gazeSize = 20
    tracker = EyeTracker(gazeBufferSize=gazeSize, roiHistorySize=gazeSize*6)

    print("Starting Eye Tracking. Press 'q' to quit.")

    showGray = False
    showInstantGaze = False
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
        
        start = perf_counter()

        # Process the frame through the pipeline
        annotatedFrame, gazeVector = tracker.processFrame(frame, showGray=showGray, showInstantGaze=showInstantGaze)

        elapsed = perf_counter() - start
        cv2.putText(annotatedFrame, f"Frame processed in {elapsed*1000:4.2f} ms", 
                        (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Show the result
        cv2.imshow("IR Eye Tracking", annotatedFrame)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        if key == ord('d'):
            while True:
                if cv2.waitKey(1) & 0xFF == ord('f'):
                    break
        
        if key == ord('m'):
            tracker.pupilThreshold += 1
            print("Pupil Threshold:", tracker.pupilThreshold)
        if key == ord('n'):
            tracker.pupilThreshold -= 1
            print("Pupil Threshold:", tracker.pupilThreshold)
        if key == ord('g'):
            showGray = not showGray
        if key == ord('i'):
            showInstantGaze = not showInstantGaze

def checkGaze():
    import random
    import math
    pg.init()
    width, height = 800, 600
    screen = pg.display.set_mode((width, height))
    pg.display.set_caption("Gaze Calibration")
    clock = pg.time.Clock()

    cap = cv2.VideoCapture(0)
    tracker = EyeTracker(gazeBufferSize=20, roiHistorySize=120)

    state = "CENTER" # CENTER, TL, BR, TRACK
    calibrating = False
    calib_frames = 0
    MAX_CALIB_FRAMES = 30
    accum_gaze = [0.0, 0.0]

    center_gaze = (0, 0)
    tl_gaze = (0, 0)
    br_gaze = (0, 0)

    center_pos = (width // 2, height // 2)
    tl_pos = (50, 50)
    br_pos = (width - 50, height - 50)

    blue_dot_pos = center_pos

    x_scale = 1.0
    y_scale = 1.0
    x_dir = 1
    y_dir = 1
    
    smooth_x = width // 2
    smooth_y = height // 2

    running = True
    print("Starting Pygame visualization. Press 's' to calibrate at the blue dot.")
    while running:
        screen.fill((30, 30, 30))

        ret, frame = cap.read()
        if not ret:
            break
        
        annotatedFrame, gazeVector = tracker.processFrame(frame, showGray=False, showInstantGaze=False)
        cv2.imshow("IR Eye Tracking", annotatedFrame)
        cv2.waitKey(1)
        
        if gazeVector is None:
            gazeVector = (0, 0)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s and not calibrating and state != "TRACK":
                    calibrating = True
                    calib_frames = 0
                    accum_gaze = [0.0, 0.0]
                    print(f"Calibrating {state}...")
                if event.key == pg.K_k and state == "TRACK":
                    blue_dot_pos = (random.randint(width//2-200, width//2+200), random.randint(height//2-160, height//2+160))

        if calibrating:
            accum_gaze[0] += gazeVector[0]
            accum_gaze[1] += gazeVector[1]
            calib_frames += 1

            if calib_frames >= MAX_CALIB_FRAMES:
                calibrating = False
                avg_gaze = (accum_gaze[0] / MAX_CALIB_FRAMES, accum_gaze[1] / MAX_CALIB_FRAMES)
                print(f"{state} calculated as {avg_gaze}")
                
                if state == "CENTER":
                    center_gaze = avg_gaze
                    state = "TL"
                    blue_dot_pos = tl_pos
                elif state == "TL":
                    tl_gaze = avg_gaze
                    state = "BR"
                    blue_dot_pos = br_pos
                elif state == "BR":
                    br_gaze = avg_gaze
                    state = "TRACK"
                    
                    # Calculate magnitude of distance from center to corners
                    avg_x_dist = (abs(tl_gaze[0] - center_gaze[0]) + abs(br_gaze[0] - center_gaze[0])) / 2.0
                    avg_y_dist = (abs(tl_gaze[1] - center_gaze[1]) + abs(br_gaze[1] - center_gaze[1])) / 2.0
                    
                    # Scale is purely a positive magnitude representing (pixels per gaze unit)
                    x_scale = (width / 2.0 - 50) / avg_x_dist if avg_x_dist > 0.01 else 1.0
                    y_scale = (height / 2.0 - 50) / avg_y_dist if avg_y_dist > 0.01 else 1.0
                    
                    # Cleverly extract the coordinate polarity dynamically
                    x_dir = 1 if br_gaze[0] > tl_gaze[0] else -1
                    y_dir = 1 if br_gaze[1] > tl_gaze[1] else -1
                    
                    print(f"Calibration done. Magnitude Scale: ({x_scale:.2f}, {y_scale:.2f}), Polarity: ({x_dir}, {y_dir})")
                    
                    # Automatically move the blue dot once calibration finishes
                    blue_dot_pos = (random.randint(width//2-200, width//2+200), random.randint(height//2-160, height//2+160))

        pg.draw.circle(screen, (0, 0, 255), blue_dot_pos, 10)

        if state == "TRACK":
            # Apply offset from center, flip coordinate axis if needed, then scale
            target_x = (gazeVector[0] - center_gaze[0]) * x_dir * x_scale/1.45 + (width  // 2)
            target_y = (gazeVector[1] - center_gaze[1]) * y_dir * y_scale/1.45 + (height // 2)
            
            # Simple exponential moving average filter for smoothing
            smooth_x = smooth_x * 0.8 + target_x * 0.2
            smooth_y = smooth_y * 0.8 + target_y * 0.2
            
            est_x = max(0, min(width, int(smooth_x)))
            est_y = max(0, min(height, int(smooth_y)))
            
            pg.draw.circle(screen, (255, 0, 0), (est_x, est_y), 5)

        pg.display.flip()
        clock.tick(30)

    cap.release()
    cv2.destroyAllWindows()
    pg.quit()

if __name__ == "__main__":
    # functionalityAndTiming()
    checkGaze()


        
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
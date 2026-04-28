#Modified by Edward Stuckey:
#I'm trying to troubleshoot why the eye tracking sometimes doesn't work.
#and also clean out the redundant camera code + make it properly stop on a keyboard or other program interrupt

# Later modified by Robert Rattray to use refactored AudioManager object as
# member of display object instead of extra thread

import tracemalloc # Memory tracking
import cProfile # Profiler
import threading # multi-threading
import time # Sleeping and time control
import os
import multiprocessing as mp
from multiprocessing import *
from multiprocessing.pool import *
from EyeTracker import *
from display import *
from butterworth import *
from audiodemo_ed_modify import *

gaze_pos = [0,0,0,0]

#wrapped in a container so we can pass by-ref
should_breakout = [False]


def wrap_eye_tracking():
    cam0 = init_and_start_camera(0)
    #cam1 = init_and_start_camera(1)
    eyeFilterSize = 3
    tracker0 = EyeTracker(eyeFilterSize)
    #tracker1 = EyeTracker(eyeFilterSize)
    # dualTracker = DualEyeTracker(gazeBufferSize=eyeFilterSize,
    #                              gazeScaling = 1)
    # Capture the latest frame as a NumPy array
    idx = 0
    while not should_breakout[0]:
        frame0 = cam0.capture_array("main")
        #frame1 = cam1.capture_array("main")
        tracker0.processFrame(frame0)
        #tracker1.processFrame(frame1)
        # result = dualTracker.stepForward(frame0, frame1)
        # gaze_pos[0:3] = np.array(result) / abs(max(result))
        gaze_pos[0:1] = tracker0.normalizedGaze
        gaze_pos[2:3] = tracker0.normalizedGaze
        # gaze_pos[2:3] = tracker1.normalizedGaze
        print(f"{idx:2d} | GazePos: {gaze_pos[0]:.3f}, {gaze_pos[1]:.3f} {gaze_pos[2]:.3f}, {gaze_pos[3]:.3f}")
        idx = (idx+1) % 60

t2 = threading.Thread(target=wrap_eye_tracking, daemon=False)

def main():
    tracemalloc.start()
    t2.start()

    # Note, we are using the convention [x, y]
    """ 
    gaze_vector = [x,y]
    Coordinate plane
    Note: [0,0] is the origin
    (-1,1)    |     (1,1)
              |
              |
    ----------|----------
              |
              |
    (-1,-1)   |     (1,-1)
    Eye-tracking ret
    """
    # if(gaze_pos is None):
    #     gaze_pos = [0,0,0,0]
    display = GazeDisplay(gaze_pos)
    try:
        display.run()
    except:
        print("breakout requested: stopping program")

    memoryUsage = tracemalloc.get_traced_memory()
    print("Current memory usage: ", memoryUsage[0] / 1000000, " megabytes\
          \nPeak memory usage: ", memoryUsage[1] / 1000000, "megabytes.")

# To profile
if __name__ == "__main__":
    # cProfile.run('main()')
    main()
    pygame.quit()
    print("-------------------------main stopped--------------")
    
    #tell the sub-thread to stop its infinite loop
    should_breakout[0] = True
    t2.join()
    sys.exit()
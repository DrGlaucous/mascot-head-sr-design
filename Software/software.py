import tracemalloc # Memory tracking
import cProfile # Profiler
import threading # multi-threading
import time # Sleeping and time control
import multiprocessing as mp
from multiprocessing import *
from multiprocessing.pool import *
from EyeTracker import *
from display import *
from butterworth import *
import pyaudio
import collections
import os
from time import perf_counter
import tkinter as tk
import cv2
# import tkinter as tk
path = cv2.data.haarcascades + 'haarcascade_eye.xml'
eye_cascade = cv2.CascadeClassifier(path)
# Note, call_eye_tracking has a list of booleans, only the first one is important
# It tracks if call_eye_tracking has produced new samples
# This is for display_eyes so it can change its behavior
def call_eye_tracking(list_o_list, index, new_data):
    # There is only one camera on my device
    # This may work better on the Pi with two cameras
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error")
        return
    gazeSize = 20
    tracker = EyeTracker(gazeBufferSize=gazeSize, roiHistorySize=gazeSize*6)
    ret, frame = cap.read()
    if not ret:
        return
    annotatedFrame, gazevector = tracker.processFrame(frame, False, False)
    new_data[0] = True
    list_o_list[index] = gazevector
    return

# Using the list of booleans, new_data, this subsystem can change its behavior
# Note, it sets new_data to false when it is done processing it. 
# Call_eye_tracking's job is to set it to true when it produces new samples
def display_eyes(average_eye_coords_left, average_eye_coords_right, new_data):
    # print("Add display when said subsystem is done")
    # print("New samples? ", new_data[0])
    # if(new_data[0]):
    #     print(average_eye_coords_left)
    #     print(average_eye_coords_right)
    #     new_data[0] = False
    # else:
    #     print("Smoothing animations")
    if(new_data[0]):
        display = GazeDisplay(average_eye_coords_left)
        display.run()
    return

def alter_voice():
    # os.system("python Software\\audiodemo.py")
    return "no"
    # return
# if __name__ == "__main__":
"""
    Research Python XLib
    Create a server for each display
"""
def main():
    tracemalloc.start()
    t3 = threading.Thread(target= alter_voice, args=())
    t3.start()

    # Note, we are using the convention [x, y]
    gaze_pos = [0,0]
    def wrap_eye_tracking():
        cap = cv2.VideoCapture(0)
        tracker = EyeTracker(gazeBufferSize= 20, roiHistorySize=120)        
        while True:
            ret, frame = cap.read()
            if(frame is None):
                gaze_pos[0] = 0
                gaze_pos[1] = 0                    
                return
            tracker.processFrame(frame, showGray=False, showInstantGaze=False)
            gazeVector = tracker.normalizedGaze
            if(gazeVector is None):
                gazeVector = [0,0]  
            # If gaze_pos[0] > rightHalfScreenThreshold, it should be positive
            gaze_pos[0] = (gazeVector[0])
            gaze_pos[1] = (gazeVector[1])
            time.sleep(1/60)

    t2 = threading.Thread(target=wrap_eye_tracking, daemon=True)
    t2.start()
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
    if(gaze_pos is None):
        gaze_pos = [0,0]
    gaze_pos[0] = 0
    gaze_pos[1] = 0
    display = GazeDisplay(gaze_pos)
    display.run()

    memoryUsage = tracemalloc.get_traced_memory()
    print("Current memory usage: ", memoryUsage[0] / 1000000, " megabytes\
          \nPeak memory usage: ", memoryUsage[1] / 1000000, "megabytes.")

# To profile
if __name__ == "__main__":
    cProfile.run('main()')
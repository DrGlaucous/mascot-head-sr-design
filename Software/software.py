import tracemalloc # Memory tracking
import cProfile # Profiler
import threading # multi-threading
import time # Sleeping and time control
import multiprocessing as mp
from multiprocessing import *
from multiprocessing.pool import *

# Note, call_eye_tracking has a list of booleans, only the first one is important
# It tracks if call_eye_tracking has produced new samples
# This is for display_eyes so it can change its behavior
def call_eye_tracking(list_o_list, index, new_data):
    # print("Print add eye-tracking when it is done")
    list_o_list[index] = ['X', 'Y']
    new_data[0] = True
    time.sleep(.1)
    # print("Samples produced")

# Using the list of booleans, new_data, this subsystem can change its behavior
# Note, it sets new_data to false when it is done processing it. 
# Call_eye_tracking's job is to set it to true when it produces new samples
def display_eyes(average_eye_coords_left, average_eye_coords_right, new_data):
    print("Add display when said subsystem is done")
    print("New samples? ", new_data[0])
    if(new_data[0]):
        print(average_eye_coords_left)
        print(average_eye_coords_right)
        new_data[0] = False
    else:
        print("Smoothing animations")
    return

def alter_voice():
    x = 0
    while(x < 5):
        print("Add voice subsystem when it is done")
        x += 1
        time.sleep(0.2)
    # return
# if __name__ == "__main__":
def main():
    tracemalloc.start()
    loop = 0
    while(loop < 2):
        threads = [None, None]
        average_eye_position = [[0,0], [0,0]]
        new_data = [False] # List of one element, just so threads can write to the address

        for eyes in range(len(threads)):
            threads[eyes] = threading.Thread(target= call_eye_tracking, args= (average_eye_position, eyes, new_data))
            threads[eyes].start()

        t3 = threading.Thread(target= alter_voice, args=())
        t3.start()
        # Forces display to run continuously until call_eye_tracking is done
        while(threads[0].is_alive() and threads[1].is_alive()):
            t2 = threading.Thread(target= display_eyes, args=(average_eye_position[0], average_eye_position[1], new_data))
            t2.start()
            time.sleep(0.015)
            # print("Threads stack_size", threading.stack_size())
        for results in range(len(threads)):
            threads[results].join()        
        t2.join()
        t3.join()
        loop += 1
        print("\n")

    memoryUsage = tracemalloc.get_traced_memory()
    print("Current memory usage: ", memoryUsage[0], " bytes\nPeak memory usage: ", memoryUsage[1], " bytes.")

# To profile
if __name__ == "__main__":
    cProfile.run('main()')
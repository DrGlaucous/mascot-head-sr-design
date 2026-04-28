#Modified by Edward Stuckey:
#I had to slightly tweak the main function so that it can be stopped from the caller in the software.py file


import pyaudio                                                                  
import time                                                                     
import collections                                                              
import os                                                                       
import sys                                                                                                                                              
import butterworth                                                              

def audiodemo(should_breakout: list):                 
    LOW_FREQ = 300 
    HIGH_FREQ = 3400
    FORMAT = pyaudio.paInt16                                                        
    CHANNELS = 1                                                                    
    SAMPLE_RATE = 44100                                                             
    # if (os.uname().nodename == "pi"):                                               
    #     SAMPLE_RATE = 48000                                                         
    BUFFER_LENGTH = 1024                                                              
    pa = pyaudio.PyAudio()                                                          
    buffer = collections.deque()                                                    
    silence = b"\x00" * (BUFFER_LENGTH * 2)  # initialize with silence (16‑bit audi)
    buffer.append(silence)                                                          

    # if (len(sys.argv) == 3):                                                        
    #     LOW_FREQ = int(sys.argv[1])                                                 
    #     HIGH_FREQ = int(sys.argv[2])                                                

    myFilter = butterworth.Filter(SAMPLE_RATE, LOW_FREQ, HIGH_FREQ)                 
    pa = pyaudio.PyAudio()                                                          

    def input_callback(in_data, frame_count, time_info, status):                    
        # global buffer     
        # buffer = collections.deque()                                                          
        buffer.append(myFilter.filter(in_data))                                     
        return (None, pyaudio.paContinue)                                           

    def output_callback(in_data, frame_count, time_info, status):                   
        # global buffer           
        # buffer                                                    
        if len(buffer) == 0:                                                        
            return (b"\x00" * (frame_count * 2), pyaudio.paContinue)                
        return (buffer.popleft(), pyaudio.paContinue)                               

    mic_stream = pa.open(                                                           
        format=FORMAT,                                                              
        channels=CHANNELS,                                                          
        rate=SAMPLE_RATE,                                                           
        input=True,                                                                 
        frames_per_buffer=BUFFER_LENGTH,                                            
        stream_callback=input_callback                                              
    )                                                                               

    speaker_stream = pa.open(                                                       
        format=FORMAT,                                                              
        channels=CHANNELS,                                                          
        rate=SAMPLE_RATE,                                                           
        output=True,                                                                
        frames_per_buffer=BUFFER_LENGTH,                                            
        stream_callback=output_callback                                             
    )                                                                               

    mic_stream.start_stream()                                                       
    speaker_stream.start_stream()                                                   
    while mic_stream.is_active() and speaker_stream.is_active() and (should_breakout[0] == False):
        time.sleep(0.1)
    
    mic_stream.stop_stream()
    speaker_stream.stop_stream()


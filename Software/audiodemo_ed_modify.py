#Modified by Edward Stuckey:
#I had to slightly tweak the main function so that it can be stopped from the caller in the software.py file

# Later modified by Robert Rattray:
# Now it's all an object, to follow RAII principle such that stream is stopped in object de-allocation, easier to work with

import pyaudio                                                                  
import time                                                                     
import collections                                                              
import os                                                                       
import sys                                                                                                                                              
import butterworth                                                              

class AudioManager:
    def input_callback(self, in_data, frame_count, time_info, status):                    
        # global buffer     
        # buffer = collections.deque()                                                          
        self.buffer.append(self.myFilters[self.myFilterIndex].filter(in_data))                                     
        return (None, pyaudio.paContinue)                                           

    def output_callback(self, in_data, frame_count, time_info, status):                   
        # global buffer           
        # buffer                                                    
        if len(self.buffer) == 0:                                                        
            return (b"\x00" * (frame_count * 2), pyaudio.paContinue)                
        return (self.buffer.popleft(), pyaudio.paContinue) 
    
    def __init__(self):
        AUDIO_MODES = [
            {"low_freq": 300, "high_freq": 3400, "gain": 1},
            {"low_freq": 800, "high_freq": 3400, "gain": 2},
            {"low_freq": 300, "high_freq": 800, "gain": 16},
        ]                
        FORMAT = pyaudio.paInt16                                                        
        CHANNELS = 1                                                                    
        SAMPLE_RATE = 44100                                                             
        # if (os.uname().nodename == "pi" or os.uname().nodename == "srgroupHost"):                                               
        #     SAMPLE_RATE = 48000                                                         
        BUFFER_LENGTH = 1024  

        self.buffer = collections.deque()                                                    
        silence = b"\x00" * (BUFFER_LENGTH * 2)  # initialize with silence (16‑bit audi)
        self.buffer.append(silence)                                                                                                       

        self.myFilters = [butterworth.Filter(SAMPLE_RATE, x["low_freq"], x["high_freq"], x["gain"]) for x in AUDIO_MODES]
        self.myFilterIndex = 0                 
        self.pa = pyaudio.PyAudio()                                                                           

        self.mic_stream = self.pa.open(                                                           
            format=FORMAT,                                                              
            channels=CHANNELS,                                                          
            rate=SAMPLE_RATE,                                                           
            input=True,                                                                 
            frames_per_buffer=BUFFER_LENGTH,                                            
            stream_callback=self.input_callback                                              
        )                                                                               

        self.speaker_stream = self.pa.open(                                                       
            format=FORMAT,                                                              
            channels=CHANNELS,                                                          
            rate=SAMPLE_RATE,                                                           
            output=True,                                                                
            frames_per_buffer=BUFFER_LENGTH,                                            
            stream_callback=self.output_callback                                             
        )

    def start(self):                                                                               
        self.mic_stream.start_stream()                                                       
        self.speaker_stream.start_stream()

    def changeFilter(self):
        self.myFilterIndex = (self.myFilterIndex + 1) % len(self.myFilters)                                                   
    
    def stop(self):
        self.mic_stream.stop_stream()
        self.speaker_stream.stop_stream()
    
    def __del__(self):
        self.stop()


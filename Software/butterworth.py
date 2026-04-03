import time                                                                     
import numpy as np                                                              
from scipy.signal import butter, sosfilt, sosfilt_zi                            
                                                                                
class Filter:                                                                   
    def __init__(self, sample_rate=44100, low_cut=300, high_cut=3400, order=6): 
        # Normalize cutoff frequencies                                          
        nyquist = 0.5 * sample_rate                                             
        low = low_cut / nyquist                                                 
        high = high_cut / nyquist                                               
        self.my_filter = butter(order, [low, high], btype='band', output='sos') 
        self.zi = sosfilt_zi(self.my_filter)                                    
        self.has_filtered = False                                               
        self.i = 0                                                              
                                                                                
    def filter(self, input: bytes):                                             
        self.i += 1                                                             
        if self.i % 32 == 0:                                                    
            print(f"Filter #{self.i} begins at:{time.time()}")                  
        npversion = np.frombuffer(input, dtype=np.int16).astype(np.float32)     
        npversion = 2 * npversion                                               
                                                                                
        if self.i % 32 == 0:                                                    
            print(f"Max input value: {np.max(npversion)}")                      
                                                                                
#        return npversion.astype(np.int16).tobytes()                            
                                                                                
        if not self.has_filtered:                                               
            self.zi = self.zi * npversion[0]                                    
            self.has_filtered = True                                            
                                                                                
        filtered = npversion                                                    
        filtered, self.zi = sosfilt(self.my_filter, npversion, zi=self.zi)      
        filtered_clipped = np.clip(32 * filtered, -32768, 32767).astype(np.int16)                                                                               
        result = filtered_clipped.tobytes()                                     
                                                                                
        if self.i % 32 == 0:                                                    
            print(f"Filter #{self.i} ends at: {time.time()}")                   
                                                                                
        return result

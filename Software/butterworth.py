import numpy as np
from scipy.signal import butter, sosfilt

class Filter:
    def __init__(self, sample_rate=44100, low_cut=60, high_cut=220, order=6):
        # Normalize cutoff frequencies
        nyquist = 0.5 * sample_rate
        low = low_cut / nyquist
        high = high_cut / nyquist
        self.my_filter = butter(order, [low, high], btype='band', output='sos')
        self.has_filtered = False
    
    def filter(self, input: bytes):
        if not self.has_filtered:
            print(input[:20])
        npversion = np.frombuffer(input, dtype=np.int16)
        filtered = sosfilt(self.my_filter, npversion.astype(np.float32))
        filtered_clipped = np.clip(filtered, -32768, 32767).astype(np.int16)
        result = filtered_clipped.tobytes()
        if not self.has_filtered:
            self.has_filtered = True 
            print(result[:20])
        return result

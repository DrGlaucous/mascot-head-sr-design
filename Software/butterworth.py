import numpy as np
from scipy.signal import butter, sosfilt
from scipy.fft import fft, fftfreq
import random
import math
import time

from librosa.effects import pitch_shift

class Filter:
    def __init__(self, sample_rate=44100, buffer_size=1024, spread=400, target_frequency=180):
        # Desired frequency, and shift from main to be considered
        self.sample_rate = sample_rate
        self.target_frequency = target_frequency
        self.spread = spread
        
        # Number of instances of calibration to occur
        self.calibrations = 256
        self.freqs = fftfreq(buffer_size, 1/sample_rate)
        self.mask = self.freqs > 0

        # Calibration data
        self.totalPower = 0
        self.totalPF = 0

        # Initial Butterworth filter
        low_cut = 200
        high_cut = 1000
        nyquist = 0.5 * self.sample_rate
        low = low_cut / nyquist
        high = high_cut / nyquist

        self.my_filter = butter(6, [low, high], btype='band', output='sos')
    

    def calibrateFilter(self, input: bytes):
        if (self.calibrations == 1024):
            print("Beginning calibration")
        self.calibrations -= 1

        npversion = np.frombuffer(input, dtype=np.int16)
        npversion = sosfilt(self.my_filter, npversion.astype(np.float32))

        fft_vals = fft(npversion.astype(np.float32))
        power_spectrum = np.abs(fft_vals) ** 2
        
        peak_power = np.max(power_spectrum[self.mask])
        peak_idx = np.argmax(power_spectrum[self.mask])
        most_powerful_freq = self.freqs[self.mask][peak_idx]
        
        self.totalPower += peak_power
        self.totalPF += (peak_power * most_powerful_freq)
        print(f"{peak_power} @ {most_powerful_freq}")

        if (self.calibrations == 0):
            most_powerful_freq = self.totalPF / self.totalPower
            low_cut = most_powerful_freq - self.spread / 2
            high_cut = most_powerful_freq + self.spread / 2
            low_cut = 200
            high_cut = 1000
            nyquist = 0.5 * self.sample_rate
            low = low_cut / nyquist
            high = high_cut / nyquist

            self.my_filter = butter(6, [low, high], btype='band', output='sos')
            self.steps = int(4 * (math.log(self.target_frequency) - math.log(most_powerful_freq)) / math.log(2))

            print("Calibration complete!")
            print(f"Primary frequency: {most_powerful_freq}")
            print(f"Steps to target: {self.steps} to {self.target_frequency}")
        
        return input

    
    def butterFilter(self, input: bytes):
        npversion = np.frombuffer(input, dtype=np.int16)
        filtered = sosfilt(self.my_filter, npversion.astype(np.float32))
        filtered_clipped = np.clip(filtered, -32768, 32767)
        shifted = pitch_shift(filtered_clipped, sr=self.sample_rate, n_steps=self.steps)
        return shifted.astype(np.int16).tobytes()


    def filter(self, input: bytes):
        if self.calibrations:
            return self.calibrateFilter(input)
        else:
            return self.butterFilter(input)

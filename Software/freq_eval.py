import matplotlib.pyplot as plt 
import sys
import butterworth # Same module used for the filter running live on the Pi
from scipy.signal import freqz_sos

# Compute frequency response
SAMPLE_RATE = 44100
LOW_FREQ = 60
HIGH_FREQ = 220
if (len(sys.argv) == 3): # Option for custom frequencies here
    LOW_FREQ = int(sys.argv[1])
    HIGH_FREQ = int(sys.argv[2])
b = butterworth.Filter(SAMPLE_RATE, LOW_FREQ, HIGH_FREQ)
w, h = freqz_sos(b.my_filter, worN=2048, fs = SAMPLE_RATE)

# Trim data
ww = w[w < (HIGH_FREQ + 200)]
hh = abs(h[0:len(ww)])

# Plot magnitude response
plt.figure(figsize=(10, 6))
plt.plot(ww, hh)
plt.title(f"Butterworth Band‑Pass Filter ({LOW_FREQ}-{HIGH_FREQ} Hz): Frequency Response")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Gain")
plt.grid(which='both', linestyle='--', linewidth=0.5)
plt.axvline(LOW_FREQ, color='green', linestyle='--')
plt.axvline(HIGH_FREQ, color='green', linestyle='--')
plt.show()
import pyaudio
import time
import collections

import butterworth

FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 44100
BUFFER_LENGTH = 1024

pa = pyaudio.PyAudio()

buffer = collections.deque()
silence = b"\x00" * (BUFFER_LENGTH * 2)  # initialize with silence (16‑bit audio)
buffer.append(silence)

myFilter = butterworth.Filter(SAMPLE_RATE)

firstTime = True

def input_callback(in_data, frame_count, time_info, status):
    global buffer
    global firstTime
    if firstTime:
        print(in_data[:10])
        firstTime = False
    buffer.append(myFilter.filter(in_data))
    # buffer.append(in_data)
    return (None, pyaudio.paContinue)

def output_callback(in_data, frame_count, time_info, status):
    global buffer
    if len(buffer) == 0:
        return (b"\x00" * (frame_count * 2), pyaudio.paContinue)
    return (buffer.popleft(), pyaudio.paContinue)

mic_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    input_device_index=12,
    frames_per_buffer=BUFFER_LENGTH,
    stream_callback=input_callback
)

speaker_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    output=True,
    output_device_index=12,
    frames_per_buffer=BUFFER_LENGTH,
    stream_callback=output_callback
)

mic_stream.start_stream()
speaker_stream.start_stream()

while mic_stream.is_active() and speaker_stream.is_active():
    time.sleep(0.1)

#! /usr/bin/env python
#
# peak_streaming.py
#
# Copyright (c) 2018 by Micron Optics, Inc.  All Rights Reserved
#

import asyncio

import hyperion
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("tkagg")

instrument_ip = "10.0.0.55"
loop = asyncio.get_event_loop()
queue = asyncio.Queue(maxsize=5)
stream_active = True

serial_numbers = []
data = []

# create the streamer object instance
peaks_streamer = hyperion.HCommTCPPeaksStreamer(instrument_ip, loop, queue)


# define a coroutine that pulls data out of the streaming queue and processes it.
async def get_data():
    while True:
        peak_data: hyperion.HACQPeaksData = await queue.get()
        queue.task_done()
        if peak_data["data"]:
            serial_numbers.append(peak_data["data"].header.serial_number)
            data.append(peak_data["data"].header)
        else:
            # If the queue returns None, then the streamer has stopped.
            break


loop.create_task(get_data())

streaming_time = 1  # seconds

print("Streaming data for {} seconds.".format(streaming_time))
# Call stop_streaming after the specified amount of time.

loop.call_later(streaming_time, peaks_streamer.stop_streaming)

loop.run_until_complete(peaks_streamer.stream_data())

assert (np.diff(np.array(serial_numbers)) == 1).all()
print("Serial numbers are contiguous.")
print("serial numbers: ", serial_numbers)

ndata = np.array(data)
print("Data shape: ", ndata.shape)
print("Data: ", ndata)

plt.plot(serial_numbers, ndata[:, 0], label="Peak 1")

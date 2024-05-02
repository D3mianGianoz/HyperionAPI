#! /usr/bin/env python
#
# spectrum_streaming.py
#
# Copyright (c) 2018 by Micron Optics, Inc.  All Rights Reserved
#

import asyncio

import hyperion
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

instrument_ip = "10.0.0.55"

loop = asyncio.get_event_loop()
queue = asyncio.Queue(maxsize=5)
stream_active = True

h1 = hyperion.Hyperion(instrument_ip)

# create the streamer object instance
spectrum_streamer = hyperion.HCommTCPSpectrumStreamer(
    instrument_ip, loop, queue, h1.power_cal
)


serials = []
data = []


# define a coroutine that pulls data out of the streaming queue and processes it
async def get_data():
    while True:
        spectrum_data = await queue.get()
        queue.task_done()
        if spectrum_data["data"]:
            serials.append(spectrum_data["data"].header.serial_number)
            data.append(spectrum_data["data"])
        else:
            # If the queue returns None, then the streamer has stopped.
            break


loop.create_task(get_data())
streaming_time = 1  # seconds
loop.call_later(streaming_time, spectrum_streamer.stop_streaming)
loop.run_until_complete(spectrum_streamer.stream_data())

# Generates 15000 evenly spaced values between 1500 and 1620
wave = np.linspace(1500, 1620, 15000)

assert (np.diff(np.array(serials)) == 1).all()
assert data is not None

ndata = np.array(data)
print(ndata.shape)
print(ndata)


fig, ax = plt.subplots()


def update(ndata: np.ndarray):
    spectra = ndata[3]
    print(spectra.shape, ndata.data.shape)
    # line.plot(wave, spectra)
    ax.plot(wave, spectra)
    return ax


ani = animation.FuncAnimation(fig, update, frames=ndata, interval=1000)

plt.xlabel("Wavelength (nm)")
plt.ylabel("Amplitude (dBm)")
plt.show()


# for spectra in data:
#     print(spectra[3])
#     plt.plot(spectra[3])
#     plt.xlabel("Wavelength (nm)")
#     plt.ylabel("Amplitude (dBm)")
#     plt.show()

import hyperion
import asyncio
import numpy as np

from time import sleep

instrument_ip = '10.0.10.46'





def sensor_streamer(num_sensors, address=instrument_ip):


    serial_numbers = []
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(maxsize=5, loop=loop)


    sensor_streamer = hyperion.HCommTCPSensorStreamer(address, loop, queue)

    async def get_data():
        print('starting acquisition')
        while True:

            sensor_data = await queue.get()
            queue.task_done()
            if sensor_data['data']:
                serial_numbers.append(sensor_data['data'].header.serial_number)
                if serial_numbers[-1] % 10000 == 0:
                    print('.',end='', flush=True)
            else:
                break


    loop.create_task(get_data())

    streaming_time = 30  # seconds

    loop.call_later(streaming_time, sensor_streamer.stop_streaming)

    loop.run_until_complete(sensor_streamer.stream_data())

    print(serial_numbers[-1])

if __name__ == '__main__':

    sensor_streamer(num_sensors=32)
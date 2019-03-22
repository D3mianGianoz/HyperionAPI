

import hyperion
import asyncio
import numpy as np
from queue import Empty

import logging
from logging.config import  dictConfig


logger_config_debug = {'handlers': ['h'],
                   'level': logging.DEBUG}

logger_config_info = {'handlers': ['h'],
                   'level': logging.INFO}

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
        },
    loggers = {
        __name__: logger_config_debug,

        'hyperion': logger_config_debug,
    }
)

dictConfig(logging_config)
logger = logging.getLogger(__name__)

instrument_ip = '192.168.2.5'

sensors = [
        ['sensor_1', 'os7520', 1, 1590.0, 2300.0],
        ['sensor_2', 'os7520', 1, 1610.0, 2300.0],
        ['sensor_3', 'os7510', 2, 1550.0, 66.0],
        ['sensor_4', 'os7510', 2, 1570.0, 66.0]
    ]

def sensor_streamer(test_sensors):

    hyp_inst = hyperion.Hyperion(instrument_ip)

    hyp_inst.remove_sensors()

    for sensor in test_sensors:
        hyp_inst.add_sensor(*sensor)

    sensors = hyp_inst.get_sensor_names()
    logger.debug('Sensors added: {0}'.format(sensors))
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(maxsize=5, loop=loop)
    stream_active = True

    serial_numbers = []
    timestamps = []

    sensor_streamer = hyperion.HCommTCPSensorStreamer(instrument_ip, loop, queue)

    async def get_data():

        while True:

            sensor_data = await queue.get()
            queue.task_done()
            if sensor_data['data']:
                serial_numbers.append(sensor_data['data'].header.serial_number)
                last_data = sensor_data

            else:
                break

        logger.debug('Last data: {0}'.format(last_data['data'].data))

    loop.create_task(get_data())

    streaming_time = 2  # seconds

    loop.call_later(streaming_time, sensor_streamer.stop_streaming)

    loop.run_until_complete(sensor_streamer.stream_data())

    #hyp_inst.remove_sensors()

if __name__ == '__main__':

    sensor_streamer(sensors)
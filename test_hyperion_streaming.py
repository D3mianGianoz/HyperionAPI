import hyperion
import asyncio
import pytest
import numpy as np
from multiprocessing import Process, Queue
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


from time import sleep

instrument_ip = '217.74.248.42'


@pytest.fixture(scope='module')
def test_sensors():
    sensors = [
        ['sensor_1', 'os7510', 1, 1510.0, 66.0],
        ['sensor_2', 'os7510', 1, 1530.0, 66.0],
        ['sensor_3', 'os7510', 2, 1550.0, 66.0],
        ['sensor_4', 'os7510', 2, 1570.0, 66.0]
    ]

    sensors = [
        ['sensor_1', 'os7520', 1, 1590.0, 2300.0],
        ['sensor_2', 'os7520', 1, 1610.0, 2300.0],
        ['sensor_3', 'os7510', 2, 1550.0, 66.0],
        ['sensor_4', 'os7510', 2, 1570.0, 66.0]
    ]

    return sensors



def test_sensor_streamer(test_sensors):

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


            else:
                break


    loop.create_task(get_data())

    streaming_time = 5  # seconds

    loop.call_later(streaming_time, sensor_streamer.stop_streaming)

    loop.run_until_complete(sensor_streamer.stream_data())

    hyp_inst.remove_sensors()

    assert (np.diff(np.array(serial_numbers)) == 1).all()

def test_multiprocess_sensor_streaming(test_sensors):

    output_queue = Queue()

    #hyp_inst = hyperion.Hyperion(instrument_ip)

    #hyp_inst.remove_sensors()

    #for sensor in test_sensors:
    #    hyp_inst.add_sensor(*sensor)


    def run_acquisition():

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        queue = asyncio.Queue(maxsize=500, loop=loop)
        stream_active = True
        serial_numbers = []
        timestamps = []
        sensor_streamer = hyperion.HCommTCPSensorStreamer(instrument_ip, loop, queue)

        async def get_data():
            while True:
                sensor_data = await queue.get()
                queue.task_done()
                if sensor_data['data']:
                    # logger.info('data received')
                    serial_numbers.append(sensor_data['data'].header.serial_number)

                    timestamps.append(sensor_data['timestamp'])
                    last_data = sensor_data
                else:
                    logger.debug('stream stopped')
                    break


        loop.create_task(get_data())

        streaming_time = 1  # seconds

        loop.call_later(streaming_time, sensor_streamer.stop_streaming)

        loop.run_until_complete(sensor_streamer.stream_data())

        output_queue.put(serial_numbers)
        output_queue.put(timestamps)

    acquisition_process = Process(target=run_acquisition)

    acquisition_process.start()
    try:
        serial_numbers_out = output_queue.get(timeout=10)
        timestamps_out = output_queue.get()
    except Empty:
        logger.error('timeout error')
        assert False
    logger.debug('Timestamp values: {0}'.format(timestamps_out[-10:]))
    # hyp_inst.remove_sensors()

    assert (np.diff(np.array(serial_numbers_out)) == 1).all()


def test_peak_streamer():

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(maxsize=5, loop=loop)
    stream_active = True

    serial_numbers = []



    peaks_streamer = hyperion.HCommTCPPeaksStreamer(instrument_ip, loop, queue)

    async def get_data():

        while True:

            peak_data = await queue.get()
            queue.task_done()
            if peak_data['data']:
                serial_numbers.append(peak_data['data'].header.serial_number)
            else:
                break


    loop.create_task(get_data())

    streaming_time = 5 # seconds

    loop.call_later(streaming_time, peaks_streamer.stop_streaming)

    loop.run_until_complete(peaks_streamer.stream_data())
    sn_diffs = np.diff(np.array(serial_numbers))
    assert (sn_diffs == 1).all()


def test_spectrum_streamer():

    hyp_inst = hyperion.Hyperion(instrument_ip)


    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(maxsize=5, loop=loop)
    stream_active = True

    serial_numbers = []

    spectrum_streamer = hyperion.HCommTCPSpectrumStreamer(instrument_ip, loop, queue, hyp_inst.power_cal)

    async def get_data():

        while True:

            spectrum_data = await queue.get()
            queue.task_done()
            if spectrum_data['data']:
                serial_numbers.append(spectrum_data['data'].header.serial_number)
            else:
                break

    loop.create_task(get_data())

    streaming_time = 5  # seconds

    loop.call_later(streaming_time, spectrum_streamer.stop_streaming)

    loop.run_until_complete(spectrum_streamer.stream_data())


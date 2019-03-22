import hyperion
import pytest
from time import sleep

instrument_ip = '217.74.248.42'

def test_hyperion_tcp_comm():

    response = hyperion.HCommTCPClient.hyperion_command(instrument_ip, "#GetSerialNumber")

    assert response.content[:3].decode() == 'HIA'
    assert len(response.content) == 6

def test_hyperion_properties():

    hyp_inst = hyperion.Hyperion(instrument_ip)

    serial_number = hyp_inst.serial_number

    assert len(serial_number) == 6

    library_version = hyp_inst.library_version

    firmware_version = hyp_inst.firmware_version

    fpga_version = hyp_inst.fpga_version

    original_name = hyp_inst.instrument_name

    test_name = 'testname'

    hyp_inst.instrument_name = test_name

    assert hyp_inst.instrument_name == test_name

    hyp_inst.instrument_name = original_name.replace(' ', '_');

    assert hyp_inst.instrument_name == original_name

    assert hyp_inst.is_ready

    assert hyp_inst.channel_count in [1,4,8,16]

    max_peak_counts = hyp_inst.max_peak_count_per_channel

    peak_detection_settings = hyp_inst.available_detection_settings

    assert peak_detection_settings[128].name == '0.25 nm Peak'

    channel_detection_settings = hyp_inst.channel_detection_setting_ids

    active_channels = hyp_inst.active_full_spectrum_channel_numbers

    test_active_channels = range(1, hyp_inst.channel_count + 1)

    hyp_inst.active_full_spectrum_channel_numbers = test_active_channels

    assert (hyp_inst.active_full_spectrum_channel_numbers == test_active_channels).all()

    hyp_inst.active_full_spectrum_channel_numbers = [1]

    assert (hyp_inst.active_full_spectrum_channel_numbers == [1]).all()

    hyp_inst.active_full_spectrum_channel_numbers = active_channels

    available_laser_scan_speeds = hyp_inst.available_laser_scan_speeds

    current_speed = hyp_inst.laser_scan_speed

    hyp_inst.laser_scan_speed = available_laser_scan_speeds[0]

    assert hyp_inst.laser_scan_speed == available_laser_scan_speeds[0]

    hyp_inst.laser_scan_speed = available_laser_scan_speeds[-1]

    assert hyp_inst.laser_scan_speed == available_laser_scan_speeds[-1]

    hyp_inst.laser_scan_speed = current_speed

    active_net_settings = hyp_inst.active_network_settings

    static_net_settings = hyp_inst.static_network_settings

    ip_mode = hyp_inst.network_ip_mode

    if ip_mode == 'STATIC':
        assert active_net_settings == static_net_settings

    test_static_net_settings = hyperion.NetworkSettings('10.0.53.53','255.255.0.0','10.0.0.1')

    hyp_inst.static_network_settings = test_static_net_settings


    sleep(2)

    hyp_inst.network_ip_mode = 'static'

    sleep(2)


    assert hyp_inst.static_network_settings == test_static_net_settings

    hyp_inst.static_network_settings = static_net_settings

    sleep(2)

    hyp_inst.instrument_utc_date_time = hyp_inst.instrument_utc_date_time

    hyp_inst.ntp_enabled = not hyp_inst.ntp_enabled

    hyp_inst.ntp_enabled = not hyp_inst.ntp_enabled

    hyp_inst.ntp_server = hyp_inst.ntp_server

    peaks = hyp_inst.peaks

    channel_peaks = hyp_inst.peaks[1]

    spectra = hyp_inst.spectra

    channel_spectra = hyp_inst.spectra[active_channels[0]]

    assert channel_spectra.size == spectra.spectra_header['num_points']




def test_sensors_api():

    test_sensors = [
        ['sensor_1', 'os7510', 1, 1510.0, 66.0],
        ['sensor_2', 'os7510', 1, 1530.0, 66.0],
        ['sensor_3', 'os7510', 2, 1550.0, 66.0],
        ['sensor_4', 'os7510', 2, 1570.0, 66.0]
    ]

    hyp_inst = hyperion.Hyperion(instrument_ip)

    hyp_inst.remove_sensors()


    for sensor in test_sensors:
        hyp_inst.add_sensor(*sensor)


    sensor_names = hyp_inst.get_sensor_names()

    test_sensor_names = [sensor_config[0] for sensor_config in test_sensors]

    assert sensor_names == test_sensor_names

    hyp_inst.save_sensors()

    hyp_inst.remove_sensors()
    #checking for problem with re-adding sensors
    for sensor in test_sensors:
        hyp_inst.add_sensor(*sensor)

    sensors = hyp_inst.export_sensors()

    for sensor, test_sensor in zip(sensors, test_sensors):

        assert [sensor['name'],
                sensor['model'],
                sensor['channel'],
                sensor['wavelength'],
                sensor['calibration_factor']] == test_sensor


    hyp_inst.remove_sensors()


def test_detection_settings_api():

    hyp_inst = hyperion.Hyperion(instrument_ip)

    detection_setting = hyp_inst.get_detection_setting(128)

    detection_setting.setting_id = 1

    hyp_inst.add_or_update_detection_setting(detection_setting)

    detection_setting.name = 'Test update detection setting'

    hyp_inst.add_or_update_detection_setting(detection_setting)

    new_setting = hyp_inst.get_detection_setting(detection_setting.setting_id)

    assert new_setting.name == detection_setting.name

    hyp_inst.remove_detection_setting(detection_setting.setting_id)

    with pytest.raises(hyperion.HyperionError):
        hyp_inst.get_detection_setting(detection_setting.setting_id)











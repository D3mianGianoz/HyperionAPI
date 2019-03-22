from hyperion import Hyperion, HCommTCPClient, COMMAND_PORT
import asyncio

class AsyncHyperion(object):

    PowerCal = namedtuple('PowerCal', 'offsets scales inverse_scales')

    def __init__(self, address: str, loop = None):

        self._address = address

        self._power_cal = None
        
        self._loop = loop or asyncio.get_event_loop()
        
        self._comm = HCommTCPClient(address, COMMAND_PORT, loop)

    async def _execute_command(self, command: str, argument: str = ''):

        await self._comm.execute_command(command, argument)

    
    async def get_power_cal(self):
        """
        Gets the offset and scale to be used to convert the fixed point spectrum data into dBm units.
        :return: The offset and scale for each channel.
        :rtype: Hyperion.PowerCal
        """
        if self._power_cal is None:

            cal_info = np.frombuffer(await self._execute_command('#GetPowerCalibrationInfo').content, dtype=np.int32)

            offsets = cal_info[::2]
            scales = cal_info[1::2]

            inverse_scales = 1.0/scales

            self._power_cal = Hyperion.PowerCal(offsets, scales, inverse_scales)

        return self._power_cal


    
    async def get_serial_number(self):
        """
        The instrument serial number.
        :type: str
        """

        return await self._execute_command('#GetSerialNumber').content.decode()


    
    async def get_library_version(self):
        """
        The version of this API library.
        :type: str
        """

        return _LIBRARY_VERSION

    
    async def get_firmware_version(self):
        """
        The version of firmware on the instrument.
        :type: str
        """

        return await self._execute_command('#GetFirmwareVersion').content.decode()

    
    async def get_fpga_version(self):
        """
        The version of FPGA code on the instrument.
        :type: str
        """
        return await self._execute_command('#GetFPGAVersion').content.decode()

    
    async def get_instrument_name(self):
        """
        The user programmable name of the instrument (settable).
        :type: str
        """

        return await self._execute_command('#GetInstrumentName').content.decode()

    async def set_instrument_name(self, name: str):

        await self._execute_command('#SetInstrumentName', name)

    
    async def get_is_ready(self):
        """
        True if the instrument is ready for operation, false otherwise.
        :type: bool
        """
        return unpack('B', await self._execute_command('#isready').content)[0] > 0


    
    async def get_channel_count(self):
        """
        The number of channels on the instrument
        :type: int
        """
        return unpack('I', await self._execute_command('#GetDutChannelCount').content)[0]


    
    async def get_max_peak_count_per_channel(self):
        """
        The maximum number of peaks that can be returned on any channel.
        :type: int
        """
        return unpack('I', await self._execute_command('#GetMaximumPeakCountPerDutChannel').content)[0]

    
    async def get_available_detection_settings(self):
        """
        A dictionary of all detection settings presets that are present on the instrument, with keys equal to the
        setting_id.
        :type: list of HPeakDetectionSettings
        """

        detection_settings_data = await self._execute_command('#GetAvailableDetectionSettings').content

        return HPeakDetectionSettings.from_binary_data(detection_settings_data)

    
    async def get_channel_detection_setting_ids(self):
        """
        A list of the detection setting ids that are currently active on each channel.
        :type: List of int
        """
        id_list = []

        ids = await self._execute_command('#GetAllChannelDetectionSettingIds').content

        for id in ids:
            id_list.append(int(id))

        return id_list

    
    async def get_active_full_spectrum_channel_numbers(self):
        """
        An array of the channels for which full spectrum data is acquired. (settable)
        :type: numpy.ndarray of int
        """

        return np.frombuffer(await self._execute_command('#getActiveFullSpectrumDutChannelNumbers').content, dtype=np.int32)


    async def set_active_full_spectrum_channel_numbers(self, channel_numbers):

        channel_string = ''

        for channel in channel_numbers:
            channel_string += '{0} '.format(channel)

        await self._execute_command('#setActiveFullSpectrumDutChannelNumbers', channel_string)

    
    async def get_available_laser_scan_speeds(self):
        """
        An array of the available laser scan speeds that are settable on the instrument

        :type: numpy.ndarray of int
        """

        return np.frombuffer(await self._execute_command('#GetAvailableLaserScanSpeeds').content, dtype=np.int32)

    
    async def get_laser_scan_speed(self):
        """
        The current laser scan speed of the instrument. (settable)

        :type: int
        """

        return unpack('I', await self._execute_command('#GetLaserScanSpeed').content)[0]

    async def set_laser_scan_speed(self, scan_speed: int):

        await self._execute_command('#SetLaserScanSpeed', '{0}'.format(scan_speed))

    
    async def get_active_network_settings(self):
        """
        The network address, netmask, and gateway that are currently active on the instrument.

        :type: NetworkSettings namedtuple
        """
        net_addresses = await self._execute_command('#GetActiveNetworkSettings').content

        address = socket.inet_ntoa(net_addresses[:4])
        mask = socket.inet_ntoa(net_addresses[4:8])
        gateway = socket.inet_ntoa(net_addresses[8:12])

        return NetworkSettings(address, mask, gateway)

    
    async def get_static_network_settings(self):
        """
        The network address, netmask, and gateway that are active when the instrument is in static mode. (settable)

        :type: NetworkSettings namedtuple
        """

        net_addresses = await self._execute_command('#GetStaticNetworkSettings').content

        address = socket.inet_ntoa(net_addresses[:4])
        mask = socket.inet_ntoa(net_addresses[4:8])
        gateway = socket.inet_ntoa(net_addresses[8:12])

        return NetworkSettings(address, mask, gateway)

    async def set_static_network_settings(self, network_settings: NetworkSettings):

        current_settings = self.static_network_settings
        ip_mode = self.network_ip_mode


        argument = '{0} {1} {2}'.format(network_settings.address,
                                        network_settings.netmask,
                                        network_settings.gateway)

        await self._execute_command('#SetStaticNetworkSettings', argument)


        if ip_mode == 'STATIC' and current_settings.address != network_settings.address:
            self._address = network_settings.address




    
    async def get_network_ip_mode(self):
        """
        The network ip configuration mode, can be dhcp or dynamic for DHCP mode, or static for static mode. (settable)
        :type: str
        """

        return await self._execute_command('#GetNetworkIpMode').content.decode()

    async def set_network_ip_mode(self, mode):

        update_ip = False
        if mode in ['Static', 'static', 'STATIC']:
            if self.network_ip_mode in ['dynamic', 'Dynamic', 'DHCP', 'dhcp']:
                update_ip = True
                new_ip = self.static_network_settings.address
            command = '#EnableStaticIpMode'
        elif mode in ['dynamic', 'Dynamic', 'DHCP', 'dhcp']:
            command = '#EnableDynamicIpMode'
        else:
            raise HyperionError('Hyperion Error:  Unknown Network IP Mode requested')

        await self._execute_command(command)

        if update_ip:
            self._address = new_ip

    
    async def get_instrument_utc_date_time(self):
        """
        The UTC time on the instrument.  If set, this will be overwritten by NTP or PTP if enabled.

        :type: datetime.datetime
        """

        date_data = await self._execute_command('#GetInstrumentUtcDateTime').content

        return datetime(*unpack('HHHHHH', date_data))

    async def set_instrument_utc_date_time(self, date_time: datetime):

        await self._execute_command('#SetInstrumentUtcDateTime', date_time.strftime('%Y %m %d %H %M %S'))



    
    async def get_ntp_enabled(self):
        """
        Boolean value indicating the enabled state of the Network Time Protocol for automatic time synchronization.
        (settable)

        :type: bool
        """

        return unpack('I', await self._execute_command('#GetNtpEnabled').content)[0] > 0

    async def set_ntp_enabled(self, enabled: bool):

        if enabled:
            argument = '1'
        else:
            argument = '0'

        await self._execute_command('#SetNtpEnabled', argument)


    
    async def get_ntp_server(self):
        """
        String containing the IP address of the NTP server. (settable)
        :type: str
        """

        return await self._execute_command('#GetNtpServer').content.decode()


    async def set_ntp_server(self, server_address):

        await self._execute_command('#SetNtpServer', server_address)

    
    async def get_ptp_enabled(self):
        """
        Boolean value indicating the enabled state of the precision time protocol.  Note that this cannot be enabled
        at the same time as NTP.  (settable)
        :type: bool
        """
        return unpack('I', await self._execute_command('#GetPtpEnabled').content)[0] > 0

    async def set_ptp_enabled(self, enabled: bool):

        if enabled:
            argument = '1'
        else:
            argument = '0'

        await self._execute_command('#SetPtpEnabled', argument)


    
    async def get_peaks(self) -> HACQPeaksData:
        """
        The measured peak positions in wavelengths
        :type: HACQPeaksData
        """

        return HACQPeaksData(await self._execute_command('#GetPeaks').content)

    
    async def get_spectra(self) -> HACQSpectrumData:
        """
        The measured wavlength spectra for all active channels (see hyperion.active_full_spectrum_channel_numbers)
        :type: HACQSpectrumData
        """

        return HACQSpectrumData(await self._execute_command('#GetSpectrum').content, self.power_cal)

    async def reboot(self):
        """
        Reboots the system after a 2 second delay
        """
        await self._execute_command('#Reboot')

    async def get_detection_setting(self, detection_setting_id: int):
        """
        Get the detection setting corresponding to the provided detection_setting_id
        :param detection_setting_id: The setting Id number for the requested setting.
        :type detection_setting_id: int
        :return: The requested detection setting if it exists.
        :rtype: HPeakDetectionSettings
        """

        detection_settings_data = await self._execute_command('#getDetectionSetting', str(detection_setting_id)).content
        return HPeakDetectionSettings.from_binary_data(detection_settings_data)

    async def add_or_update_detection_setting(self, detection_setting: HPeakDetectionSettings):
        """
        Add a new detection setting, or updates an existing one if one with the same setting_id is already present.
        :param detection_setting: The new detection settings.
        :type detection_setting: HPeakDetectionSettings
        """
        try:
            await self._execute_command('#AddDetectionSetting', detection_setting.pack())
        except HyperionError:
            await self._execute_command('#UpdateDetectionSetting', detection_setting.pack())

    async def remove_detection_setting(self, detection_setting_id: int):
        """
        Removes a user async defined detection setting.  Settings currently in use on a channel cannot be removed.
        :param detection_setting_id: The index of the detection setting to be removed.  Must be in the range 0 to 127.
        :type detection_setting_id: int
        """
        await self._execute_command('#removeDetectionSetting', str(detection_setting_id))

    async def get_channel_detection_setting(self, channel: int):
        """
        Returns the detection setting currently in use on the specified channel
        :param channel: The channel for which the setting will be returned
        :type channel: int
        :return: The requested detection setting.
        :rtype: HPeakDetectionSettings
        """
        id_data = await self._execute_command('#GetChannelDetectionSettingId', str(channel)).content

        setting_data = self.get_detection_setting(unpack('H', id_data)[0])

        return setting_data

    async def set_channel_detection_setting_id(self, channel, detection_setting_id):
        """
        Assign the specified detection setting to the specified channel.
        :param channel: The channel for which the setting is updated.
        :type channel: int
        :param detection_setting_id: The id of the detection setting to use
        :type detection_setting_id: int
        """
        argument = "{0} {1}".format(channel, detection_setting_id)

        await self._execute_command("#SetChannelDetectionSettingID", argument)


    async def set_peak_offsets_in_counts(self, channel, peak_offset_settings):
        """Set the wavelength regions and distances to compensate for time of flight effects in the optical fiber.  Use
        set_peak_offsets_in_wavelength for most applications.

        :param channel: The instrument channel for which the specified compensation values will be set.
        :type int
        :param peak_offset_settings: The peak offset settings for the channel
        :type peak_offset_settings: HPeakOffsets
        :return: None
        """
        arg_string = '{0} {1} '.format(channel, len(peak_offset_settings.boundaries))
        for boundary, delay in zip (peak_offset_settings.boundaries, peak_offset_settings.delays):
            arg_string += '{0} {1} '.format(int(delay), int(boundary))

        await self._execute_command('#SetPeakOffsets', arg_string)

    async def get_peak_offsets(self, channel):
        """Get the peak offsets used for time of flight distance compensation.

        :param channel: The channel for which the offsets will be returned.
        :type channel: int
        :return: An HPeakOffsets named tuple with the boundaries and delays for the specified channel
        :rtype: HPeakOffsets
        """

        result = await self._execute_command('#GetPeakOffsets', str(channel)).content
        num_regions = unpack('H', result[:2])[0]

        boundaries = []
        delays = []
        region_index = 2
        for region in range(num_regions):
            region = result[region_index:region_index + 6]
            delay = unpack('I',region[:4])[0]
            boundary = unpack('H', region[4:6])[0]

            boundaries.append(boundary)
            delays.append(delay)

            region_index += 6

        return HPeakOffsets(boundaries, delays)


    async def set_peak_offsets_in_wavelength(self,
                                       channel,
                                       wavelength_boundaries,
                                       delays = None,
                                       distances = None,
                                       index_of_refraction = 1.452):
        """Set the wavelength regions and distances to compensate for time of flight effects in the optical fiber, using
        the wavelengths and the known distances to the fiber sensor (one-way) in meters.

        :param channel: The instrument channel for which the specified compensation values will be set.
        :param wavelength_boundaries: An iterable of wavelengths that mark boundaries between regions.  The first region
        is assumed to start at the starting wavelength for the instrument, so each wavelength in this list specifies the
        end of the region over which the respective distance compensation will be applied.
        :param delays:  The delays to use on each region, in nanoseconds.  If this is not None, then distances is unused
        :param distances: An iterable of distances, in meters, to use for the compensation.  Each distance corresponds to the
        respective wavelength region specified by the wavelength_boundaries.  This is the one-way distance through the
        the fiber to the sensor.
        :param index_of_refraction: The fiber index of refraction.  async defaults to standard value for SMF28
        :return: The resulting peak offset settings in a HPeakOffsets named tuple.
        :rtype: HPeakOffsets
        """
        count_boundaries = np.asarray(self.convert_wavelengths_to_counts(wavelength_boundaries), dtype=np.int)

        delays = delays or np.asarray(np.round(2*(np.array(distances, dtype=np.float) *
                                      index_of_refraction/SPEED_OF_LIGHT * 1e9)), dtype=np.int)

        peak_offsets = HPeakOffsets(count_boundaries, delays)

        self.set_peak_offsets_in_counts(channel, peak_offsets )

        return peak_offsets


    async def clear_peak_offsets(self, channel = None):
        """Clear the peak offsets for the specified channel.  If channel is None, then clear all peak offsets.

        :param channel: The channel for which offsets are to be cleared.  async default is None.
        :return: None
        """

        if channel is not None:
            await self._execute_command('#ClearPeakOffsets', str(channel))
        else:
            await self._execute_command('#ClearAllPeakOffsets')


    async def convert_wavelengths_to_counts(self, wavelengths, offsets = None):
        """Get the instrument counts value that corresponds to a given wavelength and offset delay

        :param wavelengths: This can either be a single wavelength, or an iterable of wavelengths.  The return value
        will correspond accordingly.
        :param offsets:  This can be None, in which case all offsets are set to zero, or it can be an iterable of
        integer nanoseconds of delay with the same number of elements as the wavelengths parameter.  It async defaults to
        None.
        :return: Either a single count, or a list of counts.
        """

        try:
            num_wavelengths = len(wavelengths)
        except TypeError:
            wavelengths = [wavelengths]
            num_wavelengths = 1

        if offsets is None:
            offsets = np.zeros(len(wavelengths), dtype=np.int)
        elif num_wavelengths == 1:
            offsets  = [offsets]
        counts = []
        for wavelength, offset in zip(wavelengths,offsets):
            arg_string = '{0} {1}'.format(wavelength, offset)
            result = await self._execute_command('#ConvertWavelengthToCount', arg_string).content
            counts.append(unpack('d', result)[0])

        if num_wavelengths == 1:
            return counts[0]
        else:
            return counts

    async def convert_counts_to_wavelengths(self, counts):
        """Get the wavelengths that correspond to the specified instrument counts

        :param counts: Number of sample clock counts since the beginning of the scan.  This can be a single value or an
        iterable.
        :return: The wavelengths corresponding to the counts provided.
        """

        wavelengths = []
        try:
            for count in counts:
                result = await self._execute_command('#ConvertCountToWavelength', str(count)).content
                wavelengths.append(unpack('d', result))
            return wavelengths
        except TypeError:
            result = await self._execute_command('#ConvertCountToWavelength', str(counts)).content
            return unpack('d', result)

    # ******************************************************************************
    # Sensors API
    # ******************************************************************************

    async def add_sensor(self, name, model, channel, wavelength, calibration_factor, distance=0):
        """Add a sensor to the hyperion instrument.  Added sensors will stream data over the sensor streaming port.
        :param name: Sensor name.  This is an arbitrary string provided by user.
        :param model: Sensor model.  This must match the specific model, currently either os7510 or os7520.
        :param channel: Instrument channel on which the sensor is present.  First channel is 1.
        :param wavelength: The wavelength band of the sensor.
        :param calibration_factor: The calibration constant for the sensor.
        :param distance: Fiber length from sensor to interrogator, in meters, integer.
        :return: None
        """
        argument = '{0} {1} {2} {3} {4} {5}'.format(name, model, channel, distance, wavelength,
                                                    calibration_factor)
        await self._execute_command("#AddSensor", argument)

    async def get_sensor_names(self):
        """
        Get the list of user async defined names for sensors currently async defined on the instrument.
        :return: Array of strings containing the sensor names
        """
        response = await self._execute_command('#GetSensorNames')
        if response.message == '':
            return None

        return response.message.split(' ')

    async def export_sensors(self):
        """Returns all configuration data for all sensors that are currently async defined on the instrument.

        :return: Array of dictionaries containing the sensor configuration
        """
        sensor_export = await self._execute_command('#ExportSensors').content

        header_version, num_sensors = unpack('HH', sensor_export[:4])
        sensor_export = sensor_export[4:]
        sensor_configs = []

        for sensor_num in range(num_sensors):
            sensor_config = dict()
            sensor_config['version'], = unpack('H', sensor_export[:2])
            sensor_export = sensor_export[2:]

            sensor_config['id'] = list(bytearray(sensor_export[:16]))
            sensor_export = sensor_export[16:]

            name_length, = unpack('H', sensor_export[:2])

            sensor_export = sensor_export[2:]
            sensor_config['name'] = sensor_export[:name_length].decode()
            sensor_export = sensor_export[name_length:]

            model_length, = unpack('H', sensor_export[:2])
            sensor_export = sensor_export[2:]
            sensor_config['model'] = sensor_export[:model_length].decode()
            sensor_export = sensor_export[model_length:]

            sensor_config['channel'], = unpack('H', sensor_export[:2])
            sensor_config['channel'] += 1
            sensor_export = sensor_export[2:]

            sensor_config['distance'], = unpack('d', sensor_export[:8])

            # drop 2 bytes for reserved field
            sensor_export = sensor_export[10:]

            detail_keys = ('wavelength',
                           'calibration_factor',
                           'rc_gain',
                           'rc_thresholdHigh',
                           'rc_thresholdLow')

            sensor_details = dict(zip(detail_keys, unpack('ddddd', sensor_export[:40])))
            sensor_export = sensor_export[40:]
            sensor_config.update(sensor_details)
            sensor_configs.append(sensor_config)
        return sensor_configs

    async def remove_sensors(self, sensor_names=None):
        """Removes Sensors by name

        :param sensor_names: This can be a single sensor name string or a list of sensor names strings.  If omitted,
        all sensors are removed.
        :return: None
        """

        if sensor_names is None:
            sensor_names = self.get_sensor_names()
        elif type(sensor_names) == str:
            sensor_names = [sensor_names]
        try:
            for name in sensor_names:
                await self._execute_command('#removeSensor', name)

        except TypeError:
            pass

    async def save_sensors(self):
        """Saves all sensors to persistent storage.

        :return: None
        """

        await self._execute_command('#saveSensors')



'''
Basics of 1 wire protocol gotten from Adafruit:
    https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing?view=all
'''

import os
import glob
import time

try:
    from .sensorbase import SensorBase
except SystemError:
    from sensorbase import SensorBase

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
slave_path = '/w1_slave'


class OneWireTemp(SensorBase):
    '''Can be multiple thermo couples'''
    GLOBS = ['28*', '3b*']

    def __init__(self, debug=False):
        super().__init__(self._update_sensor_data)
        self._debug = debug
        self.cache_lifetime = 1

    def configure(self, context):
        super().configure(context)
        self._get_device()

    def _update_sensor_data(self):
        self._temperature = self._read_temp()

    def _get_devices(self):
        device_folder = []
        for g in self.GLOBS:
            device_folder.extend(glob.glob(base_dir + g))

        if device_folder:
            self._devices = device_folder
        else:
            self._devices = None

    def _device_files(self):
        self._get_devices()
        if not self._devices:
            raise IOError("No Devices Connected")
        return [''.join((d, slave_path)) for d in self._devices]

    @staticmethod
    def _read_temp_raw(dfile):
        with open(dfile, 'r') as f:
            return f.readlines()

    @staticmethod
    def _read_temp(dfile, timeout=0.5):
        lines = OneWireTemp._read_temp_raw(dfile)
        start = time.time()
        while lines[0].strip()[-3:] != 'YES':
            if time.time() - start > timeout:
                raise TimeoutError
            time.sleep(0.2)
            lines = OneWireTemp._read_temp_raw(dfile)
        equals_pos = lines[1].find('t=')
        if equals_pos == -1:
            raise IOError

        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

    @staticmethod
    def _get_address(dfile):
        split = os.path.split
        dfile = split(split(dfile)[0])[1]
        return ''.join(dfile.split('-'))

    def _read_temps(self):
        errors = []
        out = {}
        dfiles = self._device_files()
        for d in dfiles:
            try:
                t = self._read_temp(d)
                addr = self._get_address(d)
                out[addr] = t
            except (IOError, TimeoutError) as E:
                errors.append(E)
                if self._debug:
                    raise
        if not out:
            raise IOError(errors)
        return out, errors

    def _update_sensor_data(self):
        self._data = self._read_temps()

    @property
    def temperatures(self, errors=None):
        self._update()
        out, oerrors = self._data
        if errors:
            errors.extend(oerrors)
        return out

    def get_temperatures(self):
        return self.temperatures

if __name__ == '__main__':
    from pprint import pprint
    w = OneWireTemp(True)
    pprint(w._read_temps())



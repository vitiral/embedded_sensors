import time
from raspi_i2c import i2c
import struct

DATA_FORMAT = '!BHB'

I2C_SLAVE = 0x0703
AI418S_ADDR = 0x68
STD_CONFIG = '1{}011{}'.format  # std config, call it with the channel (00, 01, etc)
tobin = '{:02b}'.format

PGA = {
    1: '00',
    2: '01',
    4: '10',
    8: '11'
}


class AI418S(object):
    def __init__(self):
        self.dev = i2c(AI418S_ADDR, 1, I2C_SLAVE)

    def read(self, channel, pga=1, current=True):
        if pga not in PGA: raise ValueError(pga)
        config_str = STD_CONFIG(tobin(channel), PGA[pga])
        config_int = int(config_str, 2)
        config = bytes([config_int])
        #print("Config:", bin(config_int), repr(config))
        self.dev.write(config)
        time.sleep(1)
        data = self.dev.read(4)
        #print("Got", repr(data))
        data = struct.unpack(DATA_FORMAT, data)
        #print("Converted:", data)
        value = data[1] + ((data[0] & 0x03) << 16)
        config = data[2]
        #print("Config:", bin(config), "Data:", value)
        value = (value / 131071) * (2.048 / pga) * (180 / 33)
        if current:
            value = value / 249
        #print("Value:", value)
        return value


if __name__ == '__main__':
    print("running")
    dev = AI418S()
    while True:
        print("Value: ", dev.read(0, 2))


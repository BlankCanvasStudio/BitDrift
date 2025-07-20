#
#
# As a type conversion issue all reads and writes are assumed to be to/from strings
#

import os, glob, random, string
from vehicle.payloads import payload

class MemoryPayload(payload.Payload):
    def __init__(self, memsize, loctable):
        """
        Constructor
        memesize: size of the bogus memory array as single character strings
        loctable: a table of (name, size) values whihch serve as pointers to various
                  locations in the memory.
        """
        self.mem =['0'] * memsize
        self.loctable = loctable

    def __repr__(self):
        """
        __repr__(self):
        Drops contents as a sequence of 32-byte lines as ascii text
        Python strings are immutable, which means that
        I've had to use an array of arbitrary strings (I could use bytearray,
        as the idea that 'text was faster to code' is getting mugged by reality).
        """
        result = ""

        for i in range(0, len(self.mem), 32):
            result += ''.join(self.mem[i:i+32])
            result += '\n'

        return result


    def peek(self, location, length):
        """
        peek: reads from location; the value is returned as a string
        """
        addr = self.locate(location, length)

        return ''.join(self.mem[addr:addr + length])


    def poke(self, location, buffer):
        """
        poke: replaces memory information at a specific location
        """
        addr = self.locate(location, len(buffer))

        for index, value in enumerate(buffer):
            if len(value) > 1:
                raise Exception('Someone is messing with the type of the buffer elements')

            self.mem[addr + index] = value

        # for value in buffer:
        #     if len(value) > 1:
        #         raise Exception('Someone is messing with the type of the buffer elements')
        # 
        # self.mem[addr:addr + index] = buffer

        return len(buffer)


    def locate(self, location, length):
        if isinstance(location, str) and location.isnumeric():
            location = int(location)
            addr = location
        elif type(location) == int:
                addr = location
        elif location in self.loctable:
            addr = self.loctable[location]
        else:
            raise Exception('Address not found')

        # I should fence the buffer overflow, ironically enough, but this is python
        if (addr + length) > len(self.mem):
            raise Exception('Buffer overflow')

        return addr


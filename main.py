import numpy as np
import matplotlib.pyplot as plt

from bin_utils import *
from ihdr import IHDR
from idat import IDAT


class Png:
    def __init__(self, filename):
        self.filename = filename
        self.chunks = {}
        self.idat_chunks = bytes.fromhex("")

    def __str__(self):
        return str({k: chunk.__str__() for k, chunk in self.chunks.items()})

    def read_chunk(self, f):
        length = bytes_to_int(f.read(4))
        chunk_type = f.read(4).decode('utf8')
        chunk_data = f.read(length)
        crc = f.read(4)
        if chunk_type == 'IEND':
            self.chunks['IDAT'] = IDAT(self.idat_chunks, self.chunks['IHDR'])
            return None
        elif chunk_type == 'IHDR':
            self.chunks['IHDR'] = IHDR(chunk_data)
        elif chunk_type == 'PLTE':
            pass
            # image['PLTE'] = {}
            # image['PLTE']['red'] = chunk_data[0]
            # image['PLTE']['green'] = chunk_data[1]
            # image['PLTE']['blue'] = chunk_data[2]
        elif chunk_type == 'IDAT':
            self.idat_chunks += chunk_data
        else:
            print(f"undefined chunk {chunk_type}")
            pass
        self.read_chunk(f)

    def decode_png(self):
        with open(self.filename, 'rb') as f:
            assert bytes.fromhex('89504e470d0a1a0a') == f.read(8)
            self.read_chunk(f)
        return None

    def convert_pixel(self, pixel):
        # pixel_fields = self.chunks['IHDR'].get_pixel_info()['fields']
        return [pixel['red'], pixel['green'], pixel['blue']]

    def show_image(self):
        ihdr = self.chunks['IHDR']
        pixel_data = self.chunks['IDAT'].data
        pixel_matrix = [[self.convert_pixel(pixel) for pixel in row] for row in pixel_data]
        # plt.imshow(np.array(pixel_matrix).reshape((ihdr.width, ihdr.height, 3)))
        plt.imshow(pixel_matrix)
        plt.show()


if __name__ == '__main__':
    png = Png('lena.png')
    png.decode_png()
    png.show_image()

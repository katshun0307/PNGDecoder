from bin_utils import *


class IHDR:

    def __init__(self, chunk_data):
        self.width = bytes_to_int(chunk_data[:4])
        self.height = bytes_to_int(chunk_data[4:8])
        self.bit_depth = chunk_data[8]
        self.color_type = chunk_data[9]
        self.compression_method = chunk_data[10]
        self.filter_method = chunk_data[11]
        self.interlace_method = chunk_data[12]
        self.depth_max = int(2 ** self.bit_depth)
        print("IHDR: ", self.__str__())

    def __str__(self):
        return str({
            'width': self.width,
            'height': self.height,
            'bit_depth': self.bit_depth,
            'color_type': self.color_type,
            'compression_method': self.compression_method,
            'filter_method': self.filter_method,
            'interlace_method': self.interlace_method,
            'depth_max': self.depth_max,
        })

    def get_pixel_info(self):
        if self.color_type == 0:
            pass
        elif self.color_type == 2:
            sample_bytes = int(self.bit_depth / 8)
            return {
                'fields': [{'name': 'red', 'length': sample_bytes}, {'name': 'green', 'length': sample_bytes},
                           {'name': 'blue', 'length': sample_bytes}], 'total_bytes': sample_bytes * 3}
        elif self.color_type == 4:
            sample_bytes = int(self.bit_depth / 8)
            return {'fields': [{'name': 'gray', 'length': sample_bytes}, {'name': 'alpha', 'length': sample_bytes}],
                    'total_bytes': sample_bytes * 2}
        elif self.color_type == 6:
            sample_bytes = int(self.bit_depth / 8)
            return {
                'fields': [{'name': 'red', 'length': sample_bytes}, {'name': 'green', 'length': sample_bytes},
                           {'name': 'blue', 'length': sample_bytes},
                           {'name': 'alpha', 'length': sample_bytes}, ], 'total_bytes': sample_bytes * 4}
        else:
            pass

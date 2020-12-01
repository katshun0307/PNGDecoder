import io
import zlib
import math

from bin_utils import *


class IDAT:
    def __init__(self, chunk_data, ihdr):
        self.chunk_data = chunk_data
        self.ihdr = ihdr
        self.pixel_info = ihdr.get_pixel_info()
        self.dummy_pixel = {field_item['name']: 0 for field_item in self.pixel_info['fields']}
        self.dummy_row = [self.dummy_pixel for _ in range(self.ihdr.width)]
        self.data = self.decode()

    def __str__(self):
        return self.data.__str__()

    # layout methods
    def read_pixel(self, layout, pixel_info):
        pixel = {}
        fields = pixel_info['fields']
        for field_point in fields:
            pixel[field_point['name']] = bytes_to_int(layout.read(field_point['length']))
        return pixel

    def read_row(self, layout, pixel_info):
        pixel_list = []
        filter_code = bytes_to_int(layout.read(1))
        for col in range(self.ihdr.width):
            pixel_list.append(self.read_pixel(layout, pixel_info))
        return {'filter_type': filter_code, 'pixels': pixel_list}

    def read_image_layout(self, decompressed, pixel_info):
        ret = []
        layout = io.BytesIO(decompressed)
        for row in range(self.ihdr.height):
            ret.append(self.read_row(layout, pixel_info))
        return ret

    # filter methods
    def filter_none(self, sample, **_kwargs):
        return sample

    def filter_sub(self, sample, prev, **_kwargs):
        return sample + prev

    def filter_up(self, sample, prior, **_kwargs):
        return sample + prior

    def filter_average(self, sample, prev, prior, **_kwargs):
        return sample + math.floor((prev + prior) / 2)

    def filter_paeth(self, sample, prev, prior, prior_prev):
        return sample + IDAT.paeth_predictor(left=prev, above=prior, upper_left=prior_prev)

    @staticmethod
    def paeth_predictor(left, above, upper_left):
        p = left + above - upper_left
        pa = abs(p - left)
        pb = abs(p - above)
        pc = abs(p - upper_left)
        if pa <= pb and pa <= pc:
            return left
        elif pb <= pc:
            return above
        else:
            return upper_left

    def apply_filter_to_pixel(self, filter, param_pixels):
        ret = {}
        pixel_fields = self.ihdr.pixel_info['fields']
        for field in pixel_fields:
            field_name = field['name']
            params = {kw: param_pixel[field_name]
                      for kw, param_pixel in param_pixels.items()}
            ret[field_name] = filter(**params) % self.ihdr.depth_max
        return ret

    def apply_filter_to_row(self, filter_func, sample_row, prior_row):
        ret = []
        for col, pixel in enumerate(sample_row):
            if col == 0:
                raw_row = self.apply_filter_to_pixel(filter_func,
                                                     {'sample': pixel, 'prev': self.dummy_pixel,
                                                      'prior': prior_row[col], 'prior_prev': self.dummy_pixel})
            else:
                raw_row = (self.apply_filter_to_pixel(filter_func,
                                                      {'sample': pixel, 'prev': ret[col - 1],
                                                       'prior': prior_row[col], 'prior_prev': prior_row[col - 1]}))
            ret.append(raw_row)
        return ret

    def apply_layout_filter(self, layout_data):
        ret = []
        for i, scanline in enumerate(layout_data):
            sample_row = scanline['pixels']
            filter_type = scanline['filter_type']
            filter_func = {0: self.filter_none, 1: self.filter_sub, 2: self.filter_up, 3: self.filter_average,
                           4: self.filter_paeth}
            if i == 0:
                raw_row = self.apply_filter_to_row(filter_func[filter_type], sample_row, prior_row=self.dummy_row)
            else:
                raw_row = self.apply_filter_to_row(filter_func[filter_type], sample_row, prior_row=ret[i - 1])
            ret.append(raw_row)
        return ret

    def add_pixels(self, pixel_list):
        ret = pixel_list[0]
        remain = pixel_list[1:]
        for pixel in remain:
            for k, v in pixel.items():
                ret[k] = (ret[k] + v) % self.ihdr.depth_max
        return ret

    def average_pixels(self, pixel_list):
        n = len(pixel_list)
        total = self.add_pixels(pixel_list)
        ret = {}
        for k, v in total.items():
            ret[k] = v / n
        return ret

    def decode(self):
        pixel_info = self.ihdr.get_pixel_info()
        decompressed_data = zlib.decompress(self.chunk_data)
        layout = self.read_image_layout(decompressed_data, pixel_info)
        pixels_matrix = self.apply_layout_filter(layout)
        print(pixels_matrix[0])
        return pixels_matrix

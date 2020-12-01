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
    def filter_sub(self, sample_row):
        ret = []
        for i, pixel in enumerate(sample_row):
            if i == 0:
                ret.append(pixel)
            else:
                new_pixel = self.add_pixels([pixel, ret[i - 1]])
                ret.append(new_pixel)
        return ret

    def filter_up(self, sample_row, prior):
        ret = []
        for pixel, prior_pixel in zip(sample_row, prior):
            ret.append(self.add_pixels([ret, prior_pixel]))
        return ret

    def filter_average(self, sample_row, prior):
        ret = []
        for i, (pixel, prior_pixel) in enumerate(zip(sample_row, prior)):
            if i == 0:
                ret.append(self.add_pixels([self.average_pixels([prior_pixel, self.dummy_pixel]), pixel]))
            else:
                ret.append(self.add_pixels([self.average_pixels([prior_pixel, ret[i - 1]]), pixel]))
        return ret

    def reverse_paeth_pixel(self, col, pixel, prev, prior):
        ret = pixel
        for k, v in pixel.items():
            if col == 0:
                pixel[k] = (v + IDAT.paeth_predictor(left=0, above=prior[col][k], upper_left=0)) % self.ihdr.depth_max
            else:
                pixel[k] = (v + IDAT.paeth_predictor(left=prev[k], above=prior[col][k],
                                                     upper_left=prior[col - 1][k])) % self.ihdr.depth_max
        return ret

    def filter_paeth(self, row_pixels, prior):
        ret_row = []
        for col, pixel in enumerate(row_pixels):
            if col == 0:
                ret_row.append(self.reverse_paeth_pixel(col, pixel, prev=self.dummy_row, prior=prior))
            else:
                ret_row.append(self.reverse_paeth_pixel(col, pixel, prev=ret_row[col - 1], prior=prior))
        return ret_row

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

    def apply_layout_filter(self, layout_data):
        ret = []
        for i, scanline in enumerate(layout_data):
            sample_row = scanline['pixels']
            filter_type = scanline['filter_type']
            if filter_type == 0:
                raw_row = sample_row
            elif filter_type == 1:
                raw_row = self.filter_sub(sample_row)
            elif filter_type == 2:
                if i == 0:
                    raw_row = self.filter_up(sample_row, prior=self.dummy_row)
                else:
                    raw_row = self.filter_up(sample_row, prior=ret[i - 1])
            elif filter_type == 3:
                if i == 0:
                    raw_row = self.filter_average(sample_row, prior=self.dummy_row)
                else:
                    raw_row = self.filter_average(sample_row, prior=ret[i - 1])
            elif filter_type == 4:
                if i == 0:
                    raw_row = self.filter_paeth(sample_row, prior=self.dummy_row)
                else:
                    raw_row = self.filter_paeth(sample_row, prior=ret[i - 1])
            else:
                raise RuntimeError(f"Undefined filter type {filter_type} in IDAT chunk")
            ret.append(raw_row)
        return ret

    def add_pixels(self, pixel_list):
        ret = pixel_list[0]
        remain = pixel_list[1:]
        for pixel in remain:
            for k, v in pixel.items():
                ret[k] = (ret[k] + v) % self.ihdr.depth_max
        return ret

    @staticmethod
    def average_pixels(pixel_list):
        n = len(pixel_list)
        total = IDAT.add_pixels(pixel_list)
        ret = {}
        for k, v in total.items():
            ret[k] = v / n
        return ret

    def decode(self):
        pixel_info = self.ihdr.get_pixel_info()
        decompressed_data = zlib.decompress(self.chunk_data)
        layout = self.read_image_layout(decompressed_data, pixel_info)
        pixels_matrix = self.apply_layout_filter(layout)
        print(pixels_matrix[3][:20])
        return pixels_matrix

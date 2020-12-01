# util functions for byte manipulation

def bytes_to_int(bytes):
    return int.from_bytes(bytes, byteorder='big')


def bit_string_of_bytes(bytes):
    return str(bin(bytes_to_int(bytes)))[2:]

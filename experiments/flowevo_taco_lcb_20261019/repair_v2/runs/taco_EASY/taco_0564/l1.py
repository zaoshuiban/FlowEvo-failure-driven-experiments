_VALID_SIGNED_8_BIT = {str(i) for i in range(-128, 128)}

def signed_eight_bit_number(number):
    return isinstance(number, str) and number in _VALID_SIGNED_8_BIT
def get_ksa_helpers():
    return {
        'ksa_bit_check': ksa_bit_check,
    }

def ksa_bit_check(mask, pos):
    return bool(int(mask or 0) & 1 << pos)
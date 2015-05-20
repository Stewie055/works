import cython


def isInsideStraight(cards):
    if len(cards) < 4:
        return None
    cdef:
        static long *masks = [0b10111,0b11011,0b11101]
        static long *s_masks = [0b1000000001011,0b1000000001101,0b1000000001110]
        static long cards_bit = 0x00
    for c in cards:
        cards_bit = cards_bit | c.bitmask
    for i in range(9):
        for m in masks:
            if ((cards_bit >> i) & 0b11111)==m:
                return True
    for m in s_masks:
        if (cards_bit & 0b1000000001111) == m:
            return True
    return False



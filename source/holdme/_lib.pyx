## distutils: extra_compile_args = -fopenmp
## distutils: extra_link_args = -fopenmp
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
import os

cimport numpy as np
cimport cython

from libc.stdlib cimport rand, RAND_MAX

cimport hand_eval

from cython.parallel cimport prange

ctypedef np.int64_t INDEX_t
ctypedef np.uint16_t VALUE_t
cdef:
   int NFIVE = 2598960, NSEVEN = 133784560

   int HIGHCARD = 0
   int PAIR = 1 << 26
   int TWOPAIR = 2 << 26
   int TRIP = 3 << 26
   int STRAIGHT = 4 << 26
   int FLUSH  = 5 << 26
   int FULLHOUSE = 6 << 26
   int QUAD = 7 << 26
   int STRAIGHTFLUSH = 8 << 26


cdef struct Prob:
    double pwin
    double plose


cpdef int score5(long c1, long c2, long c3, long c4, long c5) nogil:
    return hand_eval.score5(c1, c2, c3, c4, c5)


cpdef int score7(long c1, long c2, long c3, long c4, long c5, long c6, long c7) nogil:
    return hand_eval.score7(c1, c2, c3, c4, c5, c6, c7)

def allfive():
    result = np.zeros(9, dtype=np.int32)

    cdef:
        long c1, c2, c3, c4, c5
        int i0, i1, i2, i3, i4
        np.int32_t[:] _out = result

    for i0 in range(52):
        c1 = 1L << (i0)
        for i1 in range(i0+1, 52):
            c2 = 1L << (i1)
            for i2 in range(i1+1, 52):
                c3 = 1L << (i2)
                for i3 in range(i2+1, 52):
                    c4 = 1L << (i3)
                    for i4 in range(i3+1, 52):
                        c5 = 1L << (i4)
                        _out[score5(c1, c2, c3, c4, c5) >> 26] += 1

    return result

def allseven():
    result = np.zeros(9, dtype=np.int32)

    cdef:
        long c1, c2, c3, c4, c5, c6, c7
        int i0, i1, i2, i3, i4, i5, i6
        np.int32_t[:] _out = result

    for i0 in range(52):
        c1 = 1L << (i0)
        for i1 in range(i0+1, 52):
            c2 = 1L << (i1)
            for i2 in range(i1+1, 52):
                c3 = 1L << (i2)
                for i3 in range(i2+1, 52):
                    c4 = 1L << (i3)
                    for i4 in range(i3+1, 52):
                        c5 = 1L << (i4)
                        for i5 in range(i4 + 1, 52):
                            c6 = 1L << (i5)
                            for i6 in range(i5 + 1, 52):
                                c7 = 1L << i6
                                _out[score7(c1, c2, c3, c4, c5, c6, c7) >> 26] += 1

    return result


cpdef int score7_from5(long c1, long c2, long c3, long c4, long c5, long c6, long c7) nogil:
    cdef:
        long tmp, result = 0
        int i, k
        long *p = [
                   c1, c2, c3, c4, c5,
                   c1, c2, c3, c4, c6,
                   c1, c2, c3, c4, c7,
                   c1, c2, c3, c5, c6,
                   c1, c2, c3, c5, c7,
                   c1, c2, c3, c6, c7,
                   c1, c2, c4, c5, c6,
                   c1, c2, c4, c5, c7,
                   c1, c2, c4, c6, c7,
                   c1, c2, c5, c6, c7,
                   c1, c3, c4, c5, c6,
                   c1, c3, c4, c5, c7,
                   c1, c3, c4, c6, c7,
                   c1, c3, c5, c6, c7,
                   c1, c4, c5, c6, c7,
                   c2, c3, c4, c5, c6,
                   c2, c3, c4, c5, c7,
                   c2, c3, c4, c6, c7,
                   c2, c3, c5, c6, c7,
                   c2, c4, c5, c6, c7,
                   c3, c4, c5, c6, c7,
                 ]
    for i in range(21):
        k = i * 5
        tmp = score5(p[k], p[k + 1], p[k + 2], p[k + 3], p[k + 4])
        if tmp > result:
            result = tmp

    return result


cdef void shuffle_part(long[:] deck, int n, int m) nogil:

    cdef:
        int i, j, card

    for i in range(m):
        j = i + rand() / (RAND_MAX / (n - i) + 1);
        card = deck[j]
        deck[j] = deck[i]
        deck[i] = card

cdef void _init_deck(long *deck, long taken) nogil:
    cdef:
       int i, j=0
       long c

    for i in range(52):
        c = 1L << i
        if (c & taken) == 0:
            deck[j] = c
            j += 1



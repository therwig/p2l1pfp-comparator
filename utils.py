from math import ceil
import numpy as np

def isZero(hexWordString): return (int(hexWordString,16)==0)
def isZeroOrVtx(hexWordString): return (int(hexWordString,16)==0) or (hexWordString=='0000000000030000')

def getOverlaps(a, b):
    """
    Compare two sets of objects (64b hex strings, longs, etc...)
    """
    a = set(a)
    b = set(b)
    common = a.intersection(b)
    aOnly = a.difference(common)
    bOnly = b.difference(common)
    return (common, aOnly, bOnly)

def Decode96b(word64b_list, drop8bLead=False):
    """
    Convert 96b words like
    111122223333444455556666
    7777888899990000AAAABBBB
    from 64b words like
    3333444455556666
    AAAABBBB11112222
    7777888899990000

    The emulator writes converted tracks
    in the same format as the 96b ones, 
    with a 32b zero-word prepended.
    """
    clki=0
    word96b_list=[]
    while clki < len(word64b_list):
        words64 = word64b_list[clki:clki+3]
        word1 = words64[1][8:16] + words64[0]
        word2 = words64[2] + words64[1][0:8] 
        word96b_list.append( word1[8:] if drop8bLead else word1 )
        word96b_list.append( word2[8:] if drop8bLead else word2 )
        clki += 3
    return np.array(word96b_list)

from math import ceil
import numpy as np

class InType:
    tk=0
    em=1
    ca=2
    mu=3
    n=4 # number of types
class OutType: #TODO
    ch=0
    ne=1
    mu=2
    n=3 # number of types

def isZero(hexWordString): return (int(hexWordString,16)==0)
def isZeroOrVtx(hexWordString): return (int(hexWordString,16)==0) or (hexWordString=='0030000000000000')

def GetPassFail(a):
    vals, counts = np.unique(a, return_counts=True)
    d = dict(zip(vals.astype(bool), counts))
    if True not in d: d[True]=0
    if False not in d: d[False]=0
    return d

def getOverlaps(a, b):
    """
    Compare two sets of objects (64b hex strings, longs, etc...)
    """
    # print(type(a))
    # print(b)
    a = set(a.flatten())
    b = set(b.flatten())
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

# bits to 
def SelectBits(x, nbits, shift):
    return ((2**nbits-1 << shift) & x) >> shift

def BitsToInt(x,nbits):
    if x < 2**(nbits-1): return x
    else: return x - 2**nbits

def SelectBitsInt(x, nbits, shift):
    return BitsToInt(SelectBits(x, nbits, shift),nbits)

# These are the 64b, converted inputs
def GetPtEtaPhi(x, inType):
    if not type(x) is int:
        x = int(x,16)
    if inType == InType.tk or inType == InType.mu:
        pt   =  SelectBitsInt(x,16, 0)
        pte  =  SelectBitsInt(x,16,16)
        eta  =  SelectBitsInt(x,10,32)
        phi  =  SelectBitsInt(x,10,42)
        z0   =  SelectBitsInt(x,10,52)
        qual =  SelectBitsInt(x, 1,62)
        return pt, eta, phi
    # TODO: should be SelectBitsInt ?
    if inType == InType.ca:
        pt   =  SelectBitsInt(x,16, 0)
        empt =  SelectBitsInt(x,16,16)
        eta  =  SelectBitsInt(x,10,32)
        phi  =  SelectBitsInt(x,10,42)
        isEM =  SelectBitsInt(x, 1,52)
        return pt, eta, phi
    if inType == InType.em:
        pt   =  SelectBitsInt(x,16, 0)
        pte  =  SelectBitsInt(x,16,16)
        eta  =  SelectBitsInt(x,10,32)#-2**10 # allow negative
        phi  =  SelectBitsInt(x,10,42)
        return pt, eta, phi

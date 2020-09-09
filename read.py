import numpy as np

def ReadTextFile(fname, asInts=False):
    nrows=0
    ncols=0
    lines=[]
    with open(fname,'r') as f:
        for l in f:
            words = l.split()
            if nrows == 0: 
                ncols = len(words)
            elif ncols != len(words):
                print('found {} words instead of {}'%(len(words),ncols))
            # strip 0x
            if asInts:
                words = [int(w[2:],16) for w in words]
            else:
                words = [w[2:] for w in words]
            lines.append(words)
            nrows += 1
    #return (lines, nrows, ncols)
    return lines


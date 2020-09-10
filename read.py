#import numpy as np
from glob import glob

def ReadTextFile(fname, asInts=False, has0x=True):
    nrows=0
    ncols=0
    lines=[]
    with open(fname,'r') as f:
        for l in f:
            words = l.split()
            if nrows == 0: 
                ncols = len(words)
            elif ncols != len(words):
                print('found {} words (columns) instead of {}'.format(len(words),ncols))
            # strip 0x
            if asInts:
                words = [int(w[2:],16) for w in words]
                if has0x==False: print('not implemented')
            else:
                words = [w[2:].upper() for w in words]
            lines.append(words)
            nrows += 1
    #return (lines, nrows, ncols)
    print('Finished reading file {} with {} columns and {} rows'.format(fname,ncols,nrows))
    return lines

def ReadAcrossFiles(file_wildcard, asInts=False, has0x=False):
    '''
    Here data 'columns' (links or similar) are spread across files
    Organize into same format as 'ReadTextFile'
    That is: lines[nrows][nlines]
    
    file_template is specified like
    /path/to/sim_HLS_input_object_*.dat
    '''
    nrows=0
    ncols = len(glob(file_wildcard))
    cols=[]
    for i in range(ncols):
        # enforce this naming convention, to e.g. avoid missing links
        fname = file_wildcard.replace('*',str(i))
        col=[]
        f=open(fname,'r')
        for _l in f:
            l=_l.rstrip()
            col.append(int(l,16) if asInts else l[2:].upper())
            if has0x: print('not implemented')
        f.close()
        if nrows==0: nrows=len(col)
        elif nrows != len(col):
            print('found {} words (rows) instead of {}'.format(len(cols),nrows))
        cols.append(col)
    #transpose the data to use a common format
    rows=[]
    for irow in range(nrows):
        row=[]
        for icol in range(ncols):
            row.append( cols[icol][irow] )
        rows.append( row )
    print('Finished reading files {} with {} columns and {} rows'.format(file_wildcard,ncols,nrows))
    return rows

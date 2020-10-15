#import numpy as np
from glob import glob
import numpy as np

def Remove0x(word): 
    return word[2:] if word.startswith('0x') else word

def ReadTextFile(logging, fname, asInts=False, has0x=True, hasValid=False):
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
            chop=0 + 1*(hasValid)
            # print(words)
            words = [ Remove0x(w).upper() for w in words ]
            # print(words)
            if asInts: words = [int(w,16) for w in words]
            lines.append(words)
            nrows += 1
    log = 'Finished reading file {} with {} columns and {} rows'.format(fname,ncols,nrows)
    # get the second word since first is a counter
    log += ' Word size: {} bits, {} hex chars'.format(4*len(lines[0][1]),len(lines[0][1]))
    logging.debug(log) #'Finished reading files {} with {} columns and {} rows'.format(file_wildcard,ncols,nrows))
    return np.array(lines)

def ReadAcrossFiles(logging, file_wildcard, asInts=False, has0x=False, hasValid=False):
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
    nstrip=2*(has0x)+1*(hasValid)
    for i in range(ncols):
        # enforce this naming convention, to e.g. avoid missing links
        fname = file_wildcard.replace('*',str(i))
        col=[]
        f=open(fname,'r')
        for _l in f:
            l=_l.rstrip()[nstrip:]
            col.append(int(l,16) if asInts else l.upper())
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
    log='Finished reading files {} with {} columns and {} rows.'.format(file_wildcard,ncols,nrows)
    log += ' Word size: {} bits, {} hex chars'.format(4*len(rows[0][0]),len(rows[0][0]))
    logging.debug(log) #'Finished reading files {} with {} columns and {} rows'.format(file_wildcard,ncols,nrows))
    return np.array(rows)

def ReadConversionTB(logging, path):
    ins=[]
    with open(path+"/word_test_input.txt",'r') as f:
        for l in f:
            word = l.rstrip().upper()
            # remove 0x if necessary
            if len(word) == 24+2: word = word[2:]
            ins.append(word)
    outs=[]
    with open(path+"/word_test_output.txt",'r') as f:
        for l in f:
            word = l.rstrip().upper()
            # remove 0x if necessary
            if len(word) == 16+2: word = word[2:]
            outs.append(word)

    if len(ins) != len(outs):
        logging.error('mismatch in number of tracks pre- and post-conversion')
        return {}
    else:
        d = {a:b for (a,b) in zip(ins,outs)}
        logging.debug('Successully read {} track conversion pairs from {}. dict size {}'.format(len(ins),path,len(d)))
        return d



#!/usr/bin/env python
import logging
from parameters import *
from read import ReadTextFile, ReadAcrossFiles, ReadConversionTB
from utils import isZero, getOverlaps, Decode96b
import numpy as np

def run():
    logging.basicConfig(#filename='compare.log', filemode='w',
                        format='%(levelname)s: %(message)s', level=logging.INFO)
    logging.info('='*72)

    ##
    ## Read emulator information
    ##    
    emulator_dir  = "example_data/emulator"
    emulator_lines_in_raw = ReadTextFile(logging, emulator_dir+'/inputs.txt')
    emulator_lines_in_cvt = ReadTextFile(logging, emulator_dir+'/inputs_converted.txt')
    emulator_lines_region = ReadTextFile(logging, emulator_dir+'/output.txt')
    emulator_lines_layer1 = ReadTextFile(logging, emulator_dir+'/layer1.txt')
    
    # Read inputs, and check the number of events present
    em_inputs = emulator_lines_in_raw
    em_inputs = em_inputs[:,1:] # first column is an index
    if REVERSED_INPUTS: em_inputs = np.flip(em_inputs, 1)
    # from tmux_full_create_test.cpp:
    #   nlines = NCLK_PER_BX*((NTEST*TMUX_OUT)+(TMUX_IN-TMUX_OUT))
    nevents = int((len(em_inputs)/NCLK_PER_BX - (TMUX_IN-TMUX_OUT))/TMUX_OUT)
    nEvents=nevents
    logging.info('Reading emulator inputs from folder: {}'.format(emulator_dir))
    logging.info('  read inputs with {} events'.format(nevents))

    # Read converted inputs, expect same number of lines
    em_inputs_cvt = emulator_lines_in_cvt
    em_inputs_cvt = em_inputs_cvt[:,1:]
    if REVERSED_INPUTS: em_inputs_cvt = np.flip(em_inputs_cvt, 1)
    if len(em_inputs_cvt) != len(em_inputs): 
        logging.error('converted inputs failed to match raw')
    
    # TODO: record the input objects present for each event
    # ...
    # (implement readers, decoders...)
    
    # Read regionized objects
    em_region = emulator_lines_region
    nevents = int(len(em_region)/NREGIONS)
    logging.info('  read regionized inputs with {} events'.format(nevents))
    em_region = em_region[:,1:]
    # truncate and shape into events
    em_region = (em_region[:NREGIONS*nevents]).reshape(nevents,NREGIONS,-1)
    
    # Read PF outputs
    em_layer1 = emulator_lines_layer1
    nevents = int(len(em_layer1)/NREGIONS)
    logging.info('  read PF layer-1 outputs with {} events'.format(nevents))
    em_layer1 = (em_layer1[:NREGIONS*nEvents]).reshape(nEvents,NREGIONS,-1)

    
    ##
    ## Read simulation information
    ##
    
    simulator_dir = "example_data/simulation"
    sim_region = ReadAcrossFiles(logging, simulator_dir+'/sim_HLS_input_object_*.dat')
    max_events = int(len(sim_region)/NREGIONS)
    logging.info('Reading simulation inputs from folder: {}'.format(simulator_dir))
    logging.info('  read simulation regionized inputs with at most {} events'.format(max_events))
    sim_region = (sim_region[:NREGIONS*nEvents]).reshape(nEvents,NREGIONS,-1)
    
    sim_layer1 = ReadAcrossFiles(logging, simulator_dir+'/sim_output_fiber_*.dat')
    max_events = int(len(sim_layer1)/NREGIONS)
    logging.info('  read simulation layer-1 outputs with at most {} events'.format(max_events))
    sim_layer1 = (sim_layer1[:NREGIONS*nEvents]).reshape(nEvents,NREGIONS,-1)
    
    
    
    ########################################################################
    # Now that all information is read in, can begin making comparisons
    ########################################################################    
    
    ##
    ## Verify track conversion
    ##
    logging.info('='*72)
    logging.info('Commencing conversion checks...')
    tk_conv_dict = ReadConversionTB(logging, "example_data/conversion")
    
    em_inputs_evts=[]
    em_inputs_cvt_evts=[]
    for ei in range(nEvents):
        link_off = (ei%3) * 32
        clk_off = ei * TMUX_OUT*NCLK_PER_BX
        evt = em_inputs[clk_off:clk_off+TMUX_IN*NCLK_PER_BX, link_off:link_off+32]
        evt_cvt = em_inputs_cvt[clk_off:clk_off+TMUX_IN*NCLK_PER_BX, link_off:link_off+32]
        em_inputs_evts.append(evt)
        em_inputs_cvt_evts.append(evt_cvt)
    
    em_inputs_evts = np.array( em_inputs_evts )
    em_inputs_t = em_inputs_evts[:,:,LINK_BOUNDARIES[0]:LINK_BOUNDARIES[1]]
    em_inputs_e = em_inputs_evts[:,:,LINK_BOUNDARIES[1]:LINK_BOUNDARIES[2]]
    em_inputs_c = em_inputs_evts[:,:,LINK_BOUNDARIES[2]:LINK_BOUNDARIES[3]]
    em_inputs_m = em_inputs_evts[:,:,LINK_BOUNDARIES[3]:LINK_BOUNDARIES[4]]
    em_inputs_cvt_evts = np.array( em_inputs_cvt_evts )
    em_inputs_cvt_t = em_inputs_cvt_evts[:,:,LINK_BOUNDARIES[0]:LINK_BOUNDARIES[1]]


    # check the conversion
    n_mismatch=0
    for ei in range(nEvents):
        for li in range(NLINKS_PER_TRACK):
            # read link words into 96b chunks
            tks = Decode96b(em_inputs_t[ei,:,li])
            tksConv = Decode96b(em_inputs_cvt_t[ei,:,li], drop8bLead=True)
            for itk, tk in enumerate(tks):
                if isZero(tk): continue
                if not tk in tk_conv_dict:
                    logging.warning('Not in dict!!', tk, tk_conv_dict[tk], tksConv[itk])
                    n_mismatch += 1
    if n_mismatch: 
        logging.warning('Found {} mis-matches in track conversion step!'.format(n_mismatch))
    else:
        logging.info('Conversion checks passed without any mismatches')

    # print( em_inputs_evts.shape ) #evt, clk, link
    # print( em_inputs_cvt_evts.shape ) #evt, clk, link
    # print( em_inputs_t[0,:,:].shape )
    # print( em_inputs_t[0,:,0][:15] )
    # print( Decode96b(em_inputs_t[0,:,0])[:10] )
    
        
    ##
    ## Compare regionized objects
    ##
    logging.info('='*72)
    logging.info('Commencing regionizer checks...')
    em_region_t = em_region[:,:,:NTRACK]
    em_region_e = em_region[:,:,NTRACK:NTRACK+NEMCALO]
    em_region_c = em_region[:,:,NTRACK+NEMCALO:NTRACK+NEMCALO+NCALO]
    em_region_m = em_region[:,:,NTRACK+NEMCALO+NCALO:NTRACK+NEMCALO+NCALO+NMU]
    em_region_vtx = em_region[:,:,-1]
    em_region_objs = [em_region_t, em_region_e, em_region_c, em_region_m]
    sim_region_e = sim_region[:,:,:NEMCALO]
    sim_region_c = sim_region[:,:,NEMCALO:NEMCALO+NCALO]
    sim_region_t = sim_region[:,:,NEMCALO+NCALO:NEMCALO+NCALO+NTRACK]
    sim_region_m = sim_region[:,:,NEMCALO+NCALO+NTRACK:NEMCALO+NCALO+NTRACK+NMU]
    sim_region_objs = [sim_region_t, sim_region_e, sim_region_c, sim_region_m]
    
    match = np.zeros( (nEvents,NREGIONS,4) )
    # print(em_[0].shape)
    # print(em_region_t[0].shape)
    #exit(0)
    for ei in range(nEvents):
        for ri in range(NREGIONS):
            # iterate object types
            for oi in range(4):
                common, emOnly, simOnly = getOverlaps(em_region_objs[oi][ei,ri], sim_region_objs[oi][ei,ri])
                # print(em_region_objs[oi][ei,ri], sim_region_objs[oi][ei,ri])
                # print( common, emOnly, simOnly )
                #exit(0)
                match[ei, ri, oi] = (len(emOnly) + len(simOnly) == 0)
                #print(ei, ri, oi, match[ei, ri, oi])
                if ei==0 and ri==0 and oi==1:
                    print(em_region_objs[oi][ei,ri], sim_region_objs[oi][ei,ri])
                    print( common, emOnly, simOnly )
                    exit(0)
    
    exit(0)
    # print( match[0,:,0] )
    # print( match[0,:,1] )
    # print( match[0,:,2] )
    # print( match[0,:,3] )
    # exit(00)
    print( match[:,:,0] )
    print( match[:,:,1] )
    print( match[:,:,2] )
    print( match[:,:,3] )
    
    # print( em_region_t.shape )
    # print( em_region_e.shape )
    # print( em_region_c.shape )
    # print( em_region_m.shape )
    
    # print( sim_region_t.shape )
    # print( sim_region_e.shape )
    # print( sim_region_c.shape )
    # print( sim_region_m.shape )
    
    #print( np.stack( [em_region_t,em_region_e] ).shape )
    exit(0)
    
    
    sim_region_events=[]
    for ei in range(nEvents):
        evt=[]
        for ri in range(NREGIONS):
            clki = ri+ei*NREGIONS
            evt.append( sim_region[ei][ri] )
        sim_region_events.append(evt)
    
    for i in range(len(sim_region)):
        regs = sim_region[i]
        nonzeros = [r!='00000000000000' for r in regs]
        nonzero = [i for i, j in enumerate(nonzeros) if j]
        nzeros = len(regs) - sum(nonzeros)
        nevt = int(i/NREGIONS)
        print( i,  nevt, nzeros, len(regs), nzeros==len(regs), nonzero )
        if nevt>=6 and (nzeros!=len(regs)): print( regs )


def main():
    # logger = logging.getLogger(__name__)

    # c_handler = logging.StreamHandler()
    # f_handler = logging.FileHandler('compare.log')
    # #c_handler.setLevel(logging.INFO)
    # f_handler.setLevel(logging.DEBUG)
    
    # # Create formatters and add it to handlers
    # c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    # f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # c_handler.setFormatter(c_format)
    # f_handler.setFormatter(f_format)
    
    # # Add handlers to the logger
    # logger.addHandler(c_handler)
    # logger.addHandler(f_handler)
    # # logger.warning('This is a warning')
    # # logger.error('This is an error')

    run()

if __name__ == '__main__':
    main()

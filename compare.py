#!/usr/bin/env python
import logging
import optparse
from parameters import *
from write import *
from read import ReadTextFile, ReadAcrossFiles, ReadConversionTB
from utils import GetPassFail, isZero, isZeroOrVtx, getOverlaps, Decode96b, InType
import numpy as np


def linkType(ilink):
    i=ilink%32
    if i >= LINK_BOUNDARIES[0] and i<LINK_BOUNDARIES[1]: return 'tk'
    if i >= LINK_BOUNDARIES[1] and i<LINK_BOUNDARIES[2]: return 'em'
    if i >= LINK_BOUNDARIES[2] and i<LINK_BOUNDARIES[3]: return 'ca'
    if i >= LINK_BOUNDARIES[3] and i<LINK_BOUNDARIES[4]: return 'mu'
    return "{}?".format(ilink)
    return "link {} (={}%32): linkType error".format(i,ilink)

def hlsInputType(i, sim=True):
    if not sim: return "TODO"
    if i >= SIM_HLS_INPUT_BOUNDARIES[0] and i<SIM_HLS_INPUT_BOUNDARIES[1]: return 'em'
    if i >= SIM_HLS_INPUT_BOUNDARIES[1] and i<SIM_HLS_INPUT_BOUNDARIES[2]: return 'ca'
    if i >= SIM_HLS_INPUT_BOUNDARIES[2] and i<SIM_HLS_INPUT_BOUNDARIES[3]: return 'tk'
    if i >= SIM_HLS_INPUT_BOUNDARIES[3] and i<SIM_HLS_INPUT_BOUNDARIES[4]: return 'mu'
    return "{}?".format(i)

def run(opts, args):
    logging.basicConfig(#filename='compare.log', filemode='w',
                        format='%(levelname)s: %(message)s', 
                        level=logging.DEBUG if opts.verbose else logging.INFO)
    logging.info('='*72)

    ##
    ## Read emulator information
    ##    
    emulator_dir  = "example_data/emulator"
    logging.info('Reading emulator inputs from folder: {}'.format(emulator_dir))
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

    # print('inputs', em_inputs[2,13])
    # print('outputs', em_region[0,:,23])
    # print('outputs', em_region[0,2,23])
    # print('outputs', em_region[0,11,23])
    # exit(0)
    
    ##
    ## Read simulation information
    ##
    
    #
    # Sim inputs (before conversion)
    simulator_dir = "example_data/simulation"
    logging.info('Reading simulation inputs from folder: {}'.format(simulator_dir))
    sim_inputs = ReadAcrossFiles(logging, simulator_dir+'/sim_input_fiber_*.dat',hasValid=True)
    # keep track of the input 'locations' for easier lookup when debugging
    sim_input_lookup = {}
    for clk, words in enumerate(sim_inputs):
        for ilink, word in enumerate(words):
            if isZero(word): continue
            if not word in sim_input_lookup:
                sim_input_lookup[word] = set()
            sim_input_lookup[word].add( (clk,ilink) )
    # print(sim_inputs[:,95-9])
    # print(sim_inputs[:,9])
    #
    # Regionized inputs
    sim_region = ReadAcrossFiles(logging, simulator_dir+'/sim_HLS_input_object_*.dat')
    max_events = int(len(sim_region)/NREGIONS)
    logging.info('  read simulation regionized inputs with at most {} events'.format(max_events))
    sim_region_overflow = sim_region[NREGIONS*nEvents:]
    sim_region = (sim_region[:NREGIONS*nEvents]).reshape(nEvents,NREGIONS,-1)
    print(sim_region.shape)
    # print(sim_region)

    #
    # Layer-1 outputs
    sim_layer1 = ReadAcrossFiles(logging, simulator_dir+'/sim_output_fiber_*.dat')
    max_events = int(len(sim_layer1)/NREGIONS)
    logging.info('  read simulation layer-1 outputs with at most {} events'.format(max_events))
    print(sim_layer1.shape)
    sim_layer1_overflow = sim_layer1[NREGIONS*nEvents:]
    sim_layer1 = (sim_layer1[:NREGIONS*nEvents]).reshape(nEvents,NREGIONS,-1)

    
    ########################################################################
    # Now that all information is read in, can begin making comparisons
    ########################################################################
    
    ##
    ## Verify track conversion
    ##
    logging.info('='*72)
    logging.info('[Conversion] Commencing conversion checks...')
    tk_conv_dict = ReadConversionTB(logging, "example_data/conversion")
    tk_deconv_dict = {} # potentially 1-to-n
    for k,v in tk_conv_dict.items():
        if v in tk_deconv_dict: 
            tk_deconv_dict[v].add(k)
        else:
            tk_deconv_dict[v]=set([k])

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
                    logging.warning('[Conversion] Not in dict!!', tk, tk_conv_dict[tk], tksConv[itk])
                    n_mismatch += 1
    if n_mismatch: 
        logging.warning('[Conversion] Found {} mis-matches in track conversion step!'.format(n_mismatch))
    else:
        logging.info('[Conversion] Conversion checks passed without any mismatches')

    ##
    ## Check overflow objects from sim
    ##
    logging.info('[Regionizer Overflow] Commencing regionizer overflow checks...')

    # nEvents consistency check
    non_zero_words=[]
    for clk in range(len(sim_region_overflow)):
        for ilink, word in enumerate(sim_region_overflow[clk]):
            if not isZeroOrVtx(word):
                non_zero_words.append( (word, clk, ilink) )
                warn = 'Unexpected non-0 on clock {} and link {} ({}): {}'.format(clk+NREGIONS*nEvents,ilink, hlsInputType(ilink), word)
                # Match the missing regionized objects with their input objects for easier debugging
                word_before_cvt = word # get word before conversion
                if linkType(ilink)=='tk': word_before_cvt = tk_deconv_dict[word] if (word in tk_deconv_dict) else None
                # check if we can find where it appears on the input links
                #TODO FIXME
                # if word_before_cvt and (word_before_cvt in sim_input_lookup):
                #     matches = sim_input_lookup[word_before_cvt]
                #     warn += "  --> matches sim input word {}".format(word_before_cvt)
                #     warn += " appearing on (link,clk) = " + ", ".join(["{}".format(m) for m in matches])
                # else: warn += '  --> no sim inputs appear to match'
                logging.warning(warn)
    logging.info('[Regionizer Overflow] Found {} words in regionized sim inputs after clock {}'.format(len(non_zero_words),NREGIONS*nEvents))

    logging.info('[HLS output overflow] Commencing output overflow checks...')
    # nEvents consistency check
    non_zero_words=[]
    for clk in range(len(sim_layer1_overflow)):
        for ilink, word in enumerate(sim_layer1_overflow[clk]):
            if not isZeroOrVtx(word):
                non_zero_words.append( (word, clk, ilink) )
                warn = 'Unexpected non-0 output on clock {} and link {}: {}'.format(clk+NREGIONS*nEvents,ilink, word)
                logging.warning(warn)
    logging.info('[HLS output overflow] Found {} words in regionized sim inputs after clock {}'.format(len(non_zero_words),NREGIONS*nEvents))


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

    #print(sim_region_t)
    for ei,_ in enumerate(sim_region_t):
        for ri,_ in enumerate(sim_region_t[ei]):
            for li,_ in enumerate(sim_region_t[ei][ri]):
                if sim_region_t[ei][ri][li]=='7EFEDBC8000B0009':
                    pass
                    #print( ei,ri,li, sim_region_t[ei][ri][li])

    match = np.zeros( (nEvents,NREGIONS,4) )
    em_only = {}
    sim_only = {}
    # print(em_[0].shape)
    # print(em_region_t[0].shape)

    # print(em_region_objs[0][0,0])
    # print(sim_region_objs[0][0,0])

    #exit(0)
    for ei in range(nEvents):
        for ri in range(NREGIONS):
            # iterate object types
            for oi in range(4):
                common, emOnly, simOnly = getOverlaps(em_region_objs[oi][ei,ri], sim_region_objs[oi][ei,ri])
                match[ei, ri, oi] = (len(emOnly) + len(simOnly) == 0)
                em_only[(ei, ri, oi)] = emOnly
                sim_only[(ei, ri, oi)] = simOnly

    print( "Total matches?", GetPassFail(match) )
    print( "Track matches?", GetPassFail(match[:,:,0]) )
    print( "EM matches?", GetPassFail(match[:,:,1]) )
    print( "Calo matches?", GetPassFail(match[:,:,2]) )
    print( "Muon matches?", GetPassFail(match[:,:,3]) )
    
    reportDir="reports/"
    WriteRegionizerReport(em_region_objs, sim_region_objs, reportDir, sim_input_lookup, tk_deconv_dict)

    WriteCounts(reportDir+"counts_em.txt", em_region_objs)
    WriteCounts(reportDir+"counts_sim.txt", sim_region_objs)

    WriteForTTree(reportDir+"tree_sim.txt", sim_region_objs)
    WriteForTTree(reportDir+"tree_em.txt", em_region_objs)


    # print("EM")
    # print(em_region_objs[1][0,:])
    # print("SIM")
    # print(sim_region_objs[1][0,:])

    # print(sim_region_c)

    # isMatch, counts = np.unique(match, return_counts=True)
    # print (isMatch)
    # print (counts)
    #exit(0)
    # print( match[0,:,0] )
    # print( match[0,:,1] )
    # print( match[0,:,2] )
    # print( match[0,:,3] )
    # exit(00)
    # print( match[:,:,0] )
    # print( match[:,:,1] )
    # print( match[:,:,2] )
    # print( match[:,:,3] )
    
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


def main(opts, args):
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

    run(opts, args)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-v',"--verbose", action='store_true', help="print debug messages")
    (opts, args) = parser.parse_args()

    main(opts, args)

# parameters from firmware (auto-generate?)

# tmux_create_test.h
# ------------------
NLINKS_PER_TRACK = 9
NLINKS_PER_CALO = 10
NLINKS_PER_EMCALO = 10
NLINKS_PER_MU = 2

#NCLK_PER_BX = 8 # 320 mhz
NCLK_PER_BX = 9 # 360 mhz
NLINKS_APX_GEN0 = 96


# firmware/data.h
# ---------------
TMUX_IN = 18
TMUX_OUT = 6

# max objects for pf+puppi input 
NTRACK = 22
NCALO = 15
NEMCALO = 13
NMU = 2
mp7DataLength = NTRACK+NCALO+NEMCALO+NMU

MP7_NCHANN = 144 
# typedef ap_uint<32> MP7DataWord
# 64b output words are MP7_NCHANN/2


# tmux_full_create_test.cpp
# -------------------------
outputOrder = [0,2,1,3,11,4,12,5,13,6,14,7,15,8,16,9,17,10]
NETA_SMALL = 2
NPHI_SMALL = 9
NREGIONS = (NETA_SMALL*NPHI_SMALL)


# User-specified
# --------------
REVERSED_INPUTS = True #96 input links

LINK_BOUNDARIES = [0, NLINKS_PER_TRACK, NLINKS_PER_TRACK+NLINKS_PER_EMCALO,
                   NLINKS_PER_TRACK+NLINKS_PER_EMCALO+NLINKS_PER_CALO,
                   NLINKS_PER_TRACK+NLINKS_PER_EMCALO+NLINKS_PER_CALO+NLINKS_PER_MU]
EM_HLS_INPUT_BOUNDARIES = [0, NTRACK, NTRACK+NEMCALO, NTRACK+NEMCALO+NCALO,
                          NTRACK+NEMCALO+NCALO+NMU]
SIM_HLS_INPUT_BOUNDARIES = [0, NEMCALO, NEMCALO+NCALO, NEMCALO+NCALO+NTRACK,
                           NEMCALO+NCALO+NTRACK+NMU]

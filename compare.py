from parameters import *
from read import ReadTextFile,ReadAcrossFiles

##
## Read emulator information
##

emulator_dir  = "example_data/emulator"
emulator_lines_in_raw = ReadTextFile(emulator_dir+'/inputs.txt')
emulator_lines_in_cvt = ReadTextFile(emulator_dir+'/inputs_converted.txt')
emulator_lines_region = ReadTextFile(emulator_dir+'/output.txt')
emulator_lines_layer1 = ReadTextFile(emulator_dir+'/layer1.txt')

# Read inputs, and check the number of events present
em_inputs = emulator_lines_in_raw
# from tmux_full_create_test.cpp
#   nlines = NCLK_PER_BX*((NTEST*TMUX_OUT)+(TMUX_IN-TMUX_OUT))
nevents = int((len(em_inputs)/NCLK_PER_BX - (TMUX_IN-TMUX_OUT))/TMUX_OUT)
print('Inputs contain {} events'.format(nevents))

# Read converted inputs, expect same number of lines
em_inputs_cvt = emulator_lines_in_cvt
if len(em_inputs_cvt) != len(em_inputs): 
    print('converted inputs failed to match raw')

# TODO: record the input objects present for each event
# ...
# (implement readers, decoders...)

# Read regionized objects
em_region = emulator_lines_region
nevents = int(len(em_region)/NREGIONS)
print('Regionized inputs contain {} events'.format(nevents))

# Read PF outputs
em_layer1 = emulator_lines_layer1
nevents = int(len(em_layer1)/NREGIONS)
print('Layer-1 outputs contain {} events'.format(nevents))



##
## Read simulation information
##

simulator_dir = "example_data/simulation"
sim_region = ReadAcrossFiles(simulator_dir+'/sim_HLS_input_object_*.dat')
max_events = int(len(sim_region)/NREGIONS)
print('Simulation regionized inputs contains at most {} events'.format(max_events))

sim_layer1 = ReadAcrossFiles(simulator_dir+'/sim_output_fiber_*.dat')
max_events = int(len(sim_region)/NREGIONS)
print('Simulation layer1 outputs contains at most {} events'.format(max_events))


##
## Compare regionized objects
##

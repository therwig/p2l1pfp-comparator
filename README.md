# p2l1pfp-comparator
A repository to hold scripts to compare outputs of L1PF emulator with simulated FW


Steps for comparison
1. Raw inputs
2. Converted inputs
3. Regionized inputs
4. HLS outputs (sorted puppis)


# Emulator

## Step 1 - Raw inputs
Inputs are read in 96 links, across 3 link groups of 32.
Links are (9 tk, 10 calo, 10 emcalo, 2 mu).
\# of inputs depends on #clocks per BX (8 for 320mhz inputs)
event inputs then last TMUX factor (18) * clk/bx = 144.
(Column ordering may be reversed due to FW routing.)

## Step 2 - Converted inputs
Written with same arrangement as raw inputs.
Currently only tracks are converted.
The 96b words are substituted w/ 64b converted word 
plus a 32b zero word.

## Step 3 - Regionized inputs
Each event is spread across 18 rows (1 per TM region)
and (22+15+13+2) columns (#s are per-obj maximums).
Order i : tk, em, calo, mu (see link_min, link_max)
All objects are the 64b word representations.

## Step 4 - HLS outputs
Each event is 18 rows (1 per region, same order as inputs)
and columns are the 72 hls output data-words.


# FW Simulation

## Step 1 - Raw inputs
Generated directly from the emulator step 1 inputs, so not read here.
FWIW: Columns arranged into `sim_input_fiber_[0 to 95].dat`.

## Step 2 - Converted inputs
Not presently recorded.

## Step 3 - Regionized inputs
Objects arranged across `sim_HLS_input_object_[0 to 51].dat`.

## Step 4 - HLS outputs
HLS outputs arranged across `sim_output_fiber_[0 to 46-ish(?)].dat`.


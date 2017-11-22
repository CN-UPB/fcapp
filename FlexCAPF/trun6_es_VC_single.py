from __future__ import division
import sys
import math
import random
from cp_flex_es import *
import time
from seeds import sim_seeds

# bash input
main_filename = str(sys.argv[1])
beta = float(sys.argv[2])
filename = str(sys.argv[3])
seed_index = int(sys.argv[4])
out_index = int(sys.argv[5])
flow_num = int(sys.argv[6])

random.seed(sim_seeds[seed_index])
cpg = CPFlex(filename,evalscen="generic")
cpg.clearFlows()
cpg.addFlow(amount=flow_num)
cpg.VCRatio *= beta

tstart = time.time()
cpg.cpgreedy()
tend = time.time()
trun = tend - tstart

foutmain = open(main_filename, "a")
foutmain.write(str(out_index) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state \
		+ " " + str(cpg.getAverageCLCload()) + " " + str(cpg.getAverageLinkUsage()) + " \n")
foutmain.close()

print str(out_index) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state
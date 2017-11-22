from __future__ import division
import sys
import math
import random
from cp_flex_fcfs import *
import time
from seeds import sim_seeds

# bash input
test = int(sys.argv[1])

nodes = {51: 36, 52: 100, 53: 36, 54: 100} 
topo = {51: "mesh", 52: "mesh", 53: "ring", 54: "ring"}
no_networks = {51: 50, 52: 50, 53: 50, 54: 50}
flowcountraise = {51: 25, 52: 50, 53: 25, 54: 50}  
raise_iterations = 40
Instances_path = 'Instances'
Results_path = 'Results/CoMP'
scenario = "Flex_fcfs"

main_filename = Results_path + '/_Results_test_' + str(test) + '_' + scenario + '.dat'

foutmain = open(main_filename, "w")
foutmain.write(str(nodes[test]) + " " + str(no_networks[test]) + " " + str(flowcountraise[test]) + " " + scenario + " " + str(topo[test]) + " \n")
foutmain.close()

for i in range(0,raise_iterations):
	for network in range(1, no_networks[test] + 1):
		filename = Instances_path + '/Test_' + str(test) + '/Network_' + str(network) + '.dat'
		random.seed(sim_seeds[network-1])
		out_index = i * no_networks[test] + network
		cpg = CPFlex(filename,evalscen="CoMP")
		
		cpg.clearFlows()
		cpg.addFlow(amount=(i+1)*flowcountraise[test])

		tstart = time.time()
		cpg.cpgreedy()
		tend = time.time()
		trun = tend - tstart
		
		foutmain = open(main_filename, "a")
		foutmain.write(str(out_index) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state \
				+ " " + str(cpg.getAverageCLCload()) + " " + str(cpg.getAverageLinkUsage()) + " \n")
		foutmain.close()
		
		print str(out_index) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state
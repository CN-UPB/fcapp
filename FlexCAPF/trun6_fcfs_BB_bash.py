from __future__ import division
import sys
import math
import random
from cp_flex_fcfs import *
import time
from seeds import sim_seeds

# bash input
test = int(sys.argv[1])
bbprob = float(sys.argv[2])
lbb = float(sys.argv[3])

nodes = {51: 36, 52: 100, 53: 36, 54: 100} 
topo = {51: "mesh", 52: "mesh", 53: "ring", 54: "ring"}
no_networks = {51: 50, 52: 50, 53: 50, 54: 50}
flowcountraise = {51: 200, 52: 200, 53: 200, 54: 200}  
raise_iterations = int(6000/200)
Instances_path = 'Instances'
Results_path = 'Results/BB'
scenario = "Flex_fcfs_BB_" + str(bbprob) + "_" + str(1000*lbb) 

main_filename = Results_path + '/_Results_test_' + str(test) + '_' + scenario + '.dat'

foutmain = open(main_filename, "w")
foutmain.write(str(nodes[test]) + " " + str(no_networks[test]) + " " + str(flowcountraise[test]) + " " + scenario + " " + str(topo[test]) + " \n")
foutmain.close()

for i in range(0,raise_iterations):
	for network in range(1, no_networks[test] + 1):
		filename = Instances_path + '/Test_' + str(test) + '/Network_' + str(network) + '.dat'
		random.seed(sim_seeds[network-1])
		out_index = i * no_networks[test] + network
		cpg = CPFlex(filename,evalscen="generic")
		cpg.considerBBconnections = True
		cpg.clearFlows()
		cpg.addFlow(amount=(i+1)*flowcountraise[test])
		
		for k in range(0,int(math.ceil(len(cpg.cn.V)/10))): 
			t = random.choice(list(set(cpg.cn.V) - set(cpg.cn.T)))
			cpg.cn.T.append(t)
			cpg.cn.G.node[t]['TAPcontrol'] = []
			cpg.cn.no_T += 1
		
		for f in cpg.cn.F:
			ftmp = random.random()   
			if ftmp < bbprob:
				cpg.cn.F_BB.append(f)
				cpg.cn.fdata[f]['toBB'] = 1
			else:
				cpg.cn.fdata[f]['toBB'] = 0
				
		cpg.cn.L_BB = lbb

		tstart = time.time()
		cpg.cpgreedy()
		tend = time.time()
		trun = tend - tstart
		
		foutmain = open(main_filename, "a")
		foutmain.write(str(out_index) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state \
				+ " " + str(cpg.getAverageCLCload()) + " " + str(cpg.getAverageLinkUsage()) + " \n")
		foutmain.close()
		
		print str(out_index) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state
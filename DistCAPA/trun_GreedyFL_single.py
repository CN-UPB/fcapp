from __future__ import division
import sys, os, time, math, random
from lib import crowd_network as CN
from ComplexNetworkSim import NetworkSimulation
import GreedyFL_Flows
import Manager
from lib import cp_flex_fcfs
from Simulation_GreedyFL import *
from seeds import sim_seeds
import networkx as nx
from subprocess import Popen, list2cmdline

#commands.append(['python','trun_GreedyFL_single.py',main_filename,LLlimit,filename,seed_index,out_index,flow_num])

# bash input
main_filename = str(sys.argv[1])
LLlimit = float(sys.argv[2])
filename = str(sys.argv[3])
seed_index = int(sys.argv[4])
out_index = int(sys.argv[5])
flow_num = int(sys.argv[6])

random.seed(sim_seeds[seed_index])
cpg = cp_flex_fcfs.CPFlex(filename,evalscen="generic")
cpg.clearFlows()
cpg.addFlow(amount=flow_num)
cn = cpg.cn.copy()
cn.cleanup()
sim = Simulation_GreedyFL(cn)
sim.LLlimit = LLlimit
steps_per_run = 10
sim.MAX_SIMULATION_TIME = steps_per_run

num_iters = 0
num_no_change = 0
totalruntime = [0.0 for v in cn.V]
lastCLCs = len(cn.C)+1
lastSat = 0

while True:
	num_iters += 1
	sim.run()
	for node in sim.globalSharedParameters['runtime'].keys():
		totalruntime[node] += sim.globalSharedParameters['runtime'][node]
	if sim.state == 'Solved' and len(sim.CLCs) >= lastCLCs and len(sim.Satisfied) <= lastSat:
		num_no_change += 1
		if num_no_change >= 10:
			num_iters -= 10
			break
	else:
		num_no_change = 0
	lastCLCs = len(sim.CLCs)
	lastSat = len(sim.Satisfied)
	
sim.validityCheck(log=True,fix=False)
			
runtime = str(sum(i for i in totalruntime))
maxruntime = str(max(totalruntime))

state = sim.state
clcs = str(len(sim.CLCs))
nodesat = str(len(sim.Controlled))
flows = str(len(cn.F))
flowssat = str(len(sim.Satisfied))
clcload = str(sim.getAverageCLCload())
clcpathlen = str(sim.getAverageCLCpathlength())
clcctrlratio = str(sim.CLCcontrolRatio())

foutmain = open(main_filename, "a")
foutmain.write(str(out_index) + ' ' + clcs + ' ' + nodesat + ' ' + flows + ' ' + flowssat + ' ' + clcload + ' ' + clcpathlen + ' ' \
	+ clcctrlratio + ' ' + runtime + ' ' + maxruntime + ' ' + state + ' ' + str(num_iters*steps_per_run) + '\n')
foutmain.close()
			
print str(out_index) + ' ' + clcs + ' ' + nodesat + ' ' + flows + ' ' + flowssat  + ' ' + runtime + ' ' + maxruntime + ' ' + state + ' ' + str(num_iters*steps_per_run)
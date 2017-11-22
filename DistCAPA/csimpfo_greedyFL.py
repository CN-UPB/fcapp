from __future__ import division
import sys, math, random, time, pdb
from math import exp,sqrt,pow
from lib import cp_flex_fcfs
from Simulation_GreedyFL import *
from seeds import sim_seeds

def loadlevel(i): # time i is provided in seconds
	i = (i/3600) * 24 % 24 # switch from seconds to day time but scale 24 hours to 1 hour
	if i <= 3:
		return 0.9*(-1/27*pow(i,2)+1)
	elif i <= 6:
		return 0.9*(1/27*pow(i-6,2)+1/3)
	elif i <= 15:
		return 0.9*(1/243*pow(i-6,2)+1/3)
	else:
		return 0.9*(-1/243*pow(i-24,2)+1)
		
# bash input
network = str(sys.argv[1])
LLlimit = float(sys.argv[2])
seed_index = int(sys.argv[3])
		
# input settings
filename = 'TestData/Network_' + network + '.dat'
random.seed(sim_seeds[seed_index])

# simulation settings
sim_duration = 2*3600	

# initialize GreedyFL
cpf = cp_flex_fcfs.CPFlex(filename)
cpf.clearFlows()
cpf.cn.flowDurationMode = "expo"
no_nodes = len(cpf.cn.V)
cnCopy = cpf.cn.copy()
greedyFL = Simulation_GreedyFL(cnCopy)
greedyFL.LLlimit = LLlimit

results_path = 'Results/dist_sim'
results_filename = results_path + '/simres_dist_' + str(network) + '_' + str(LLlimit) + '_' + str(seed_index) + '.dat'

foutmain = open(results_filename, "w")
foutmain.write("time #flows #Satisfied #CLCs #CLCDiff #nodeDiff #flowDiff CLCpathlength CLCload controlRatio runtime runtimeNodes steps \n")
foutmain.close()

t = -3600.0
lastRun = t
tlast = t
tnext = t
fremhelp = {}
lambdamax = max([loadlevel(i) for i in range(0,sim_duration)])*no_nodes
cleanupDist = {}
flowsAdded = 0
flowsRemoved = 0
time_per_step = 0.005 # assuming 5 milliseconds per executed DistCAPA step
steps = 0

while t < sim_duration:
	t += random.expovariate(lambdamax)
	c = random.random()
	if c < loadlevel(t)*no_nodes/lambdamax:
		tnext = t
		steps = int(round((tnext-tlast)/time_per_step))
			
		if steps > 0:
			greedyFL.updateTime(tlast,addNewFlow=True)
		
			if tlast >= -60.0: 
				greedyFL.MAX_SIMULATION_TIME = steps
				oldCLCs = list(greedyFL.CLCs)
				oldControls = [list(greedyFL.cn.G.node[n]['CLCs']) for n in greedyFL.cn.V]
				oldSats = {}
				for f in greedyFL.cn.F:
					oldSats[f] = greedyFL.cn.fdata[f]['CLC']
				start = time.time()
				greedyFL.run()
				runtime = time.time() - start
				runtime2 = sum(greedyFL.globalSharedParameters['runtime'][i] for i in greedyFL.cn.V)
				
				clcDiff = len(set(greedyFL.CLCs).symmetric_difference(set(oldCLCs)))
				if t > 0 and (clcDiff > 0 or lastRun < 0):
					nrCLCs = len(greedyFL.CLCs)
					nrFlowsSat = len(greedyFL.Satisfied)
					nrFlows = len(greedyFL.cn.F)
					CLCMeanLoad = greedyFL.getAverageCLCload()
					averageCLCPathLength = greedyFL.getAverageCLCpathlength()
					ctrlratio = greedyFL.CLCcontrolRatio()
					nodeDiff = sum(len(set(greedyFL.cn.G.node[n]['CLCs']).symmetric_difference(set(oldControls[n]))) for n in greedyFL.cn.V)
					flowDiff = sum(int(greedyFL.cn.fdata[f]['CLC'] <> oldSats[f]) for f in greedyFL.cn.F)
					output = str(t) + ' ' + str(nrFlows) + ' ' + str(nrFlowsSat) + ' ' + str(nrCLCs) + ' ' + str(clcDiff) + ' ' + str(nodeDiff) \
					+ ' ' + str(flowDiff) + ' ' + str(averageCLCPathLength) + ' ' + str(CLCMeanLoad) + ' ' + str(ctrlratio) + ' ' + str(runtime) + ' ' + str(runtime2) + ' ' + str(steps) + '\n'
					print output
					foutmain = open(results_filename, "a")
					foutmain.write(output)
					foutmain.close()
					lastRun = t
					
			tlast = t
from __future__ import division
import sys, math, random, time, pdb
from math import exp,sqrt,pow
from cp_flex_fcfs import *
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

def output(cpf,trun=None):
	print "State: " + cpf.state
	if cpf.state == "NOT SOLVED":
		print "Remaining nodes: " + str([i for i in cpf.cn.V if not i in cpf.Controlled])
	print "CRCs: " + str(len(cpf.CRCs)) 
	print str(cpf.CRCs)
	print "CLCs: " + str(len(cpf.CLCs)) + " (out of " + str(len(cpf.cn.C)) + " available)"
	print str(cpf.CLCs)
	print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
	if trun is not None:
		print "Runtime: " + str(trun) + " seconds"
		
def slimoutput(cpf,trun=None):
	if cpf.state == "NOT SOLVED":
		print "State: " + cpf.state + ", Remaining nodes: " + str(len([i for i in cpf.cn.V if not i in cpf.Controlled])) + " out of " + str(len(cpf.cn.V))
	else: 
		print "State: " + cpf.state
	print "CRCs: " + str(len(cpf.CRCs)) + ", CLCs: " + str(len(cpf.CLCs)) + " (out of " + str(len(cpf.cn.C)) + " available), Control ratio: " + str(cpf.CLCcontrolRatio()) \
			+ ", Average load: " + str(cpf.getAverageCLCload())
	print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
	if trun is not None:
		print "Runtime: " + str(trun) + " seconds"
		
def simstep(cpf,calctime):
	tmpCLCs = list(cpf.CLCs)
	tstart = time.time()
	cpf.cpgreedy()
	tend = time.time()
	trun = tend-tstart
	nodeDiff = cpf.newCLCcontrols
	flowDiff = cpf.newFlowSats
		
	CLCDiff = len(set(cpf.CLCs).symmetric_difference(set(tmpCLCs)))

	if display_output:
		print "Time: " + str(calctime)
		slimoutput(cpf,trun)
		print "\n"
	
	if results_output and t >= 0:
		foutmain = open(results_filename, "a")
		foutmain.write(str(calctime) + " " + str(len(cpf.cn.F)) + " " + str(len(cpf.Satisfied)) + " " + str(len(cpf.CLCs)) + " " + str(CLCDiff) + " " + str(nodeDiff) + " " + str(flowDiff)  \
						+ " " + str(cpf.getAverageCLCpathlength()) + " "  + str(cpf.getAverageCLCload()) + " "  + str(cpf.CLCcontrolRatio()) + " " + str(trun) + " \n")
		foutmain.close() 
		
# bash input
network = str(sys.argv[1])
seed_index = int(sys.argv[2])
		
# input settings
filename = 'Network_' + network + '.dat'
random.seed(sim_seeds[seed_index])

# simulation settings
sim_duration = 2*3600	
display_output = True
results_output = True

# initialize CPFlex
cpf = CPFlex(filename,evalscen="generic")
cpf.flexOperation = True
cpf.clearFlows()
no_nodes = len(cpf.cn.V)
d_LL = 0.9
cpf.L_lowload = d_LL
cpf.T_lowload = 60.0
cpf.cn.flowDurationMode = "expo"
cpf.cn.b_CRC = 0
cpf.cn.l_CRC = 1e6
cpf.cn.p_CRC = 0

results_path = 'Results/flex_for_dist'
results_filename = results_path + '/simres_fcfs_' + str(network) + '_' + str(seed_index) + '.dat'

if results_output:
	foutmain = open(results_filename, "w")
	foutmain.write("time #flows #Satisfied #CLCs #CLCDiff #nodeDiff #flowDiff CLCpathlength CLCload controlRatio runtime \n")
	foutmain.close()

t = -3600.0
tlast = t
perform_simstep = False
lastdisp = -3600.0
calctime = -3600.0
llalarm = False
lambdamax = max([loadlevel(i) for i in range(0,sim_duration)])*no_nodes

while t < sim_duration:
	t += random.expovariate(lambdamax)
	c = random.random()
	if c < loadlevel(t)*no_nodes/lambdamax:
		
		tlast = t	
		cpf.updateTime(t,addNewFlow=True)
	
		if cpf.state <> "Solved": # for reality purpose in case of a CLC or CRC failure, should currently not happen
			perform_simstep = True
			reason = 1

		if len(cpf.cn.F) > len(cpf.Satisfied) and len(cpf.cn.C) > len(cpf.CLCs) + len(cpf.banlist):
			perform_simstep = True
			reason = 2
			
		if cpf.LL_execution == True:
			perform_simstep = True
			reason = 3
			
		if perform_simstep and t >= -10: 
			print "Reason: " + str(reason) + ", t = " + str(t)
			calctime = t
			lastdisp = t
			tmplenCLCs = len(cpf.CLCs)
			
			if t >= 0:
				print "Simstep of " + str(network) + '_' + str(cpf.flowRearrangement) + '_' + str(seed_index)
				simstep(cpf,calctime)
			else:
				cpf.cpgreedy()
				print "Using " + str(len(cpf.CLCs)) + " CLCs out of " + str(len(cpf.cn.C))
			if reason == 2 and len(cpf.cn.F) > len(cpf.Satisfied):
				btmp = list(set(cpf.cn.F) - set(cpf.Satisfied))
				for f in btmp:
					cpf.remFlow(f)
			# if reason == 3 and len(cpf.CLCs) >= tmplenCLCs:
				# cpf.L_lowload -= 0.05
			# else:
				# cpf.L_lowload = d_LL
			perform_simstep = False
			
		if t - lastdisp > 300:
			print "Current t: " + str(t)
			lastdisp = t	
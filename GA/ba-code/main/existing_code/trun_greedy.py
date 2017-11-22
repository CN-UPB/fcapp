from __future__ import division
import time

from fcpf_greedy import *

import os
try:
	user_paths = os.environ['PYTHONPATH'].split(os.pathsep)
	print(user_paths)
	print("fooo")
except KeyError:
	user_paths = []
	print("errorr")

test = 22
nodes = 100
no_instances = 4000
instperflowcount = 100
flowcountraise = 100
scenario = "greedy"
Instances_path = 'Instances'

foutmain = open(Instances_path + '/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
foutmain.write(str(nodes) + " " + str(instperflowcount) + " " + str(flowcountraise) + " " + scenario + " \n")
foutmain.close()

for network in range(1,no_instances + 1):
	filename = Instances_path + '/Test_' + str(test) + '/Network_' + str(network) + '.dat'
	cpg = CPGreedy(filename)

	tstart = time.time()
	cpg.cpgreedy()
	tend = time.time()
	trun = tend - tstart
	
	foutmain = open(Instances_path + '/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
	foutmain.write(str(network) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state + " \n")
	foutmain.close()
	
	print(str(network) + " " + str(len(cpg.CRCs)) + " " + str(len(cpg.CLCs)) + " " + str(len(cpg.Satisfied)) + " " + str(trun) + " " + cpg.state)
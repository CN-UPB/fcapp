from __future__ import division
import sys
import math
import random
from cp_flex_fcfs import *
import time
from seeds import sim_seeds
from subprocess import Popen, list2cmdline

def exec_commands(cmds,max_task):
	if not cmds: return # empty list

	def done(p):
		return p.poll() is not None
	def success(p):
		return p.returncode == 0
	def fail():
		sys.exit(1)

	processes = []
	while True:
		while cmds and len(processes) < max_task:
			task = cmds.pop(0)
			print list2cmdline(task)
			processes.append(Popen(task))

		for p in processes:
			if done(p):
				if success(p):
					processes.remove(p)
				#else:
					#fail()

		if not processes and not cmds:
			break
		else:
			time.sleep(0.05)

# bash input
num_task = int(sys.argv[1])

nodes = {51: 36, 52: 100, 53: 36, 54: 100} 
topo = {51: "mesh", 52: "mesh", 53: "ring", 54: "ring"}
no_networks = {51: 50, 52: 50, 53: 50, 54: 50}
flowcountraise = {51: 200, 52: 200, 53: 200, 54: 200}  
raise_iterations = {"Flex_fcfs": int(10000/200), "Flex_es": int(6000/200)}
script_file = {"Flex_fcfs": 'trun6_fcfs_VC_single.py', "Flex_es": 'trun6_es_VC_single.py'}
Instances_path = 'Instances'
Results_path = 'Results/VCstudy'

tests = [51,53]
betas = [0.5*i for i in range(1,11)]
commands = []

resume = False

if resume == False:
	for test in tests:
		for beta in betas:
			for version in ["Flex_fcfs","Flex_es"]:
				scenario = version + "_" + str(beta)
				main_filename = Results_path + '/_Results_test_' + str(test) + '_' + scenario + '.dat'
				foutmain = open(main_filename, "w")
				foutmain.write(str(nodes[test]) + " " + str(no_networks[test]) + " " + str(flowcountraise[test]) + " " + scenario + " " + str(topo[test]) + " \n")
				foutmain.close()

				for i in range(0,raise_iterations[version]):
					for network in range(1, no_networks[test] + 1):
						filename = Instances_path + '/Test_' + str(test) + '/Network_' + str(network) + '.dat'
						seed_index = network-1
						out_index = i * no_networks[test] + network
						flow_num = (i+1)*flowcountraise[test]
						
						commands.append(['python',script_file[version],str(main_filename),str(beta),str(filename),str(seed_index),str(out_index),str(flow_num)])
else:
	for test in tests:
		for beta in betas:
			for version in ["Flex_fcfs","Flex_es"]:
				scenario = version + "_" + str(beta)
				already_run = []
				main_filename = Results_path + '/_Results_test_' + str(test) + '_' + scenario + '.dat'
				fin = open(main_filename, "r")
				tmp = fin.readline()
				while True:
					tmp = fin.readline().split(" ")
					try:
						already_run.append(int(tmp[0]))
					except:
						break

				for i in range(0,raise_iterations[version]):
					for network in range(1, no_networks[test] + 1):
						filename = Instances_path + '/Test_' + str(test) + '/Network_' + str(network) + '.dat'
						seed_index = network-1
						out_index = i * no_networks[test] + network
						flow_num = (i+1)*flowcountraise[test]
						
						if not out_index in already_run:
							commands.append(['python',script_file[version],str(main_filename),str(beta),str(filename),str(seed_index),str(out_index),str(flow_num)])

weight = script_file = {'trun6_fcfs_VC_single.py': 0.6, 'trun6_es_VC_single.py': 1.0}						
commands.sort(key=lambda cmd: weight[cmd[1]]*int(cmd[6]))

exec_commands(commands,num_task)
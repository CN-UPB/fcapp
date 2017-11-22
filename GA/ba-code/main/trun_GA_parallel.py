from __future__ import division
import sys, os, time, math, random
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
			fout = open(task[1],"a")
			print list2cmdline(task[0])
			processes.append(Popen(task[0],stdout=fout))

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

Results_path = '../../ba-results/'

commands = []

scenario = "default"
for flows in range(100,1001,100):
	for repr in ["greedy", "ga2", "ga3"]:
		config = "representation=" + str(repr) + ",numFlows=" + str(flows)
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(flows) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])
			
scenario = "population"
for mu in range(10,101,10):
	for repr in ["ga2", "ga3"]:
		config = "representation=" + str(repr) + ",mu=" + str(mu) + ",numFlows=1000"
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(mu) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])

scenario = "tsize"
for ts in range(1,11):
	for repr in ["ga2", "ga3"]:
		config = "representation=" + str(repr) + ",tsize=" + str(ts) + ",numFlows=1000"
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(ts) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])

scenario = "crossover"
for pc in [0.05*i for i in range(0,21)]:
	for repr in ["ga2", "ga3"]:
		config = "representation=" + str(repr) + ",cxpb=" + str(pc) + ",numFlows=1000"
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(pc) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])

scenario = "floworder"
for flows in range(100,1001,100):
	for repr in ["ga2", "ga3"]:
		for fo in ["leastDemanding", "mostDemanding", "random"]:
			config = "representation=" + str(repr) + ",flowOrder=" + str(fo) + ",numFlows=" + str(flows)
			main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(fo) + '_' + str(flows) + '.dat'
			foutmain = open(main_filename, "w")
			foutmain.write("Settings: " + config + "\n")
			foutmain.close()

			for network in range(0,50):			
				commands.append([['python','maina.py',str(network),config],main_filename])
				
for flows in range(100,1001,100):
	for repr in ["ga2b"]:
		config = "representation=" + str(repr) + ",numFlows=" + str(flows)
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(flows) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])

scenario = "beta"
for beta in [0.5*i for i in range(0,21)]:
	for repr in ["ga3"]:
		config = "representation=" + str(repr) + ",vcFactor=" + str(beta) + ",numFlows=1000"
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(beta) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])	
			
scenario = "final"
for flows in range(100,3001,100):
	for repr in ["greedy", "ga2", "ga3", "ga3b"]:
		config = "representation=" + str(repr) + ",numFlows=" + str(flows)
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(flows) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])
			
scenario = "default"
for flows in range(100,1001,100):
	for repr in ["ga1"]:
		config = "representation=" + str(repr) + ",numFlows=" + str(flows)
		main_filename = Results_path + scenario + '/' + scenario + '_' + str(repr) + '_' + str(flows) + '.dat'
		foutmain = open(main_filename, "w")
		foutmain.write("Settings: " + config + "\n")
		foutmain.close()

		for network in range(0,50):			
			commands.append([['python','maina.py',str(network),config],main_filename])

				
exec_commands(commands,num_task)
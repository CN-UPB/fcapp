from __future__ import division
import sys, os, time, math, random
from subprocess import Popen, list2cmdline

def exec_commands(cmds,max_task,min_task_per_type=0):
	if not cmds: return # empty list

	def done(p):
		return p.poll() is not None
	def success(p):
		return p.returncode == 0
	def fail():
		sys.exit(1)

	processes = []
	proc_trac = []
	type_count = {}
	for t in cmds:
		type = t[1]+t[2]
		if not type in type_count:
			type_count[type] = 0
		
	while True:
		while cmds and len(processes) < max_task:
			next_task = 0
			min_val = max_task + 1
			for t in type_count:
				if type_count[t] < min_val:
					min_val = type_count[t]
					t_min = t
			if type_count[t_min] < min_task_per_type:
				if len([c for c in cmds if c[1] + c[2] == t_min]) > 0:
					for i in range(0,len(cmds)):
						if cmds[i][1] + cmds[i][2] == t_min:
							next_task = i
							break
				else:
					del type_count[t_min]
						
			task = cmds.pop(next_task)
			print list2cmdline(task)
			processes.append(Popen(task))
			type = task[1]+task[2]
			proc_trac.append((processes[-1].pid,type))
			type_count[type] += 1

		for p in processes:
			if done(p):
				for t in proc_trac:
					if t[0] == p.pid:
						if t[1] in type_count:
							type_count[t[1]] -= 1
						proc_trac.remove(t)
						break
				processes.remove(p)

		if not processes and not cmds:
			break
		else:
			time.sleep(0.05)

# bash input
num_task = int(sys.argv[1])

nodes = {101: 4, 102: 9, 91: 4, 92: 9} 
instperflowcount = {101: 50, 102: 50, 91: 50, 92: 50}
flowcountraise = {101: 25, 102: 25, 91: 10, 92: 10}  
no_networks = {101: 3000, 102: 1000, 91: 2500, 92: 1500} 

resume = True

commands = []

if resume == False:
	for test in [101,102]:
		for scenario in ["es", "fcfs", "fcfs_BB_0.0", "fcfs_BB_2.5", "fcfs_BB_5.0"]:
			main_filename = 'Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat'
			foutmain = open(main_filename, "w")
			foutmain.write(str(nodes[test]) + " " + str(instperflowcount[test]) + " " + str(flowcountraise[test]) + " " + scenario + " \n")
			foutmain.close()

		for network in range(1, no_networks[test] + 1):	
			if (test == 101 and network <= 1600) or test == 102:
				commands.append(['python','crun_es_single.py',str(test),str(network)])
			if (test == 101 and network <= 1200) or (test == 102 and network <= 600):
				for lbb in [0.0,0.0025,0.005]:
					commands.append(['python','crun_fcfs_BB_single.py',str(test),str(network),str(lbb)])
			commands.append(['python','crun_fcfs_single.py',str(test),str(network)])
				
	for test in [91,92]:
		for scenario in ["es"]:
			main_filename = 'Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat'
			foutmain = open(main_filename, "w")
			foutmain.write(str(nodes[test]) + " " + str(instperflowcount[test]) + " " + str(flowcountraise[test]) + " " + scenario + " \n")
			foutmain.close()

		for network in range(1, no_networks[test] + 1):		
			commands.append(['python','crun_es_single.py',str(test),str(network)])
else:
	for test in [91,92,101,102]:
		scenario = "es"
		already_run = []
		main_filename = 'Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat'
		fin = open(main_filename, "r")
		tmp = fin.readline()
		while True:
			tmp = fin.readline().split(" ")
			try:
				already_run.append(int(tmp[0]))
			except:
				break
		for network in range(1, no_networks[test] + 1):		
			if not network in already_run:
				if test in [91,92,102] or (test == 101 and network <= 1600):
					commands.append(['python','crun_es_single.py',str(test),str(network)])
				
	for test in [101,102]:
		scenario = "fcfs"
		already_run = []
		main_filename = 'Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat'
		fin = open(main_filename, "r")
		tmp = fin.readline()
		while True:
			tmp = fin.readline().split(" ")
			try:
				already_run.append(int(tmp[0]))
			except:
				break
		for network in range(1, no_networks[test] + 1):		
			if not network in already_run:
				commands.append(['python','crun_fcfs_single.py',str(test),str(network)])
		for lbb in [0.0,0.0025,0.005]:
			scenario = "fcfs_BB_" + str(1000*lbb)
			already_run = []
			main_filename = 'Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat'
			fin = open(main_filename, "r")
			tmp = fin.readline()
			while True:
				tmp = fin.readline().split(" ")
				try:
					already_run.append(int(tmp[0]))
				except:
					break
			for network in range(1, no_networks[test] + 1):		
				if not network in already_run:
					if (test == 101 and network <= 1200) or (test == 102 and network <= 600):
						commands.append(['python','crun_fcfs_BB_single.py',str(test),str(network),str(lbb)])
	
				
commands.sort(key=lambda cmd: nodes[int(cmd[2])] * flowcountraise[int(cmd[2])] * int(math.ceil(int(cmd[3]) / instperflowcount[int(cmd[2])])) ) # sort by nodes * flows

exec_commands(commands,num_task,min_task_per_type=2)
from __future__ import division
import os
import time

from coopr.pyomo import *
from coopr.opt import *
from fcpf_ilp import model


solver = 'gurobi'
solver_io = 'python'
stream_solver = True

opt = SolverFactory(solver,solver_io=solver_io)
opt.options['MIPGap'] = 0.0
opt.options['Threads'] = 1
opt.options['timelimit'] = 36000
opt.options['PSDTol'] = 0.0

if opt is None:
	print("")
	print("ERROR: Unable to create solver plugin for %s "\
		"using the %s interface" % (solver, solver_io))
	print("")
	exit(1)

test = 20
nodes = 16
no_instances = 2000
instperflowcount = 100
flowcountraise = 10
scenario = "ilp"
individual_results = False

if individual_results:
	if not os.path.exists(os.path.dirname("Instances/Test_" + str(test) + "/Individual_Results/foo.dat")):
		os.makedirs(os.path.dirname("Instances/Test_" + str(test) + "/Individual_Results/foo.dat"))

foutmain = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
foutmain.write(str(nodes) + " " + str(instperflowcount) + " " + str(flowcountraise) + " " + scenario + " \n")
foutmain.close()

for network in range(1, no_instances + 1):
	instance = model.create('Instances/Test_' + str(test) + '/Network_' + str(network) + '.dat')

	try:		
		tstart = time.time()
		results = opt.solve(instance, tee=True)
		tend = time.time()

		instance.load(results)
		
		foutmain = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
		foutmain.write(str(network) + " " + str(getattr(instance, 'NumCRCs')[None].value) \
										+ " " + str(getattr(instance, 'NumCLCs')[None].value) \
										+ " " + str(getattr(instance, 'NumSats')[None].value) \
										+ " " + str(tend - tstart) + "\n")
		foutmain.close()
		
		if individual_results:
			fout = open('Instances/Test_' + str(test) + '/Individual_Results/Results_' + str(network) + '_' + scenario + '.dat', "w")
			
			for v in instance.active_components(Var):
				fout.write(str(v) + "\n")
				varobject = getattr(instance, v)
				for index in varobject:
					fout.write("   " + str(index) + " " + str(varobject[index].value) + "\n")
				fout.write("\n")
	except:
		foutmain = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
		foutmain.write(str(network) + " timelimit \n")
		foutmain.close()
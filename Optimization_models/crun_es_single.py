from __future__ import division 
from pyomo.environ import *
from pyomo.opt import *
import sys, os
import time
from cp_crowd_es import model

solver = 'gurobi'
solver_io = 'python'
stream_solver = True

opt = SolverFactory(solver,solver_io=solver_io)
opt.options['MIPGapAbs'] = 0.5 # equals optimal because the objective function has integer values
opt.options['Threads'] = 1
opt.options['MIPFocus'] = 1
opt.options['TimeLimit'] = 3600
opt.options['PSDTol'] = 0.0
#opt.options['NumericFocus'] = 1
opt.options['PreQLinearize'] = -1

if opt is None:
	print("")
	print("ERROR: Unable to create solver plugin for %s "\
		"using the %s interface" % (solver, solver_io))
	print("")
	exit(1)
	
# bash input
test = int(sys.argv[1])
network = int(sys.argv[2])

scenario = "es"

instance = model.create_instance('Instances/Test_' + str(test) + '/Network_' + str(network) + '.dat')
getattr(instance, "bigM").set_value(1e6)

# trying to load heuristic results to help optimization model
try:
	fin = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_Flex_' + scenario + '.dat', "r")
	tmp = fin.readline()
	while True:
		tmp = fin.readline().split(" ")
		if int(tmp[0]) == network:
			getattr(instance, "CRCbound").set_value(int(tmp[1]))
			getattr(instance, "CLCbound").set_value(int(tmp[2]))
			getattr(instance, "SATbound").set_value(int(tmp[3]))
			break
	fin.close()
except:
	pass

try:	
	tstart = time.time()
	results = opt.solve(instance)#, tee=True)
	tend = time.time()
	
	foutmain = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
	foutmain.write(str(network) + " " + str(getattr(instance, 'NumCRCs')[None].value) \
									+ " " + str(getattr(instance, 'NumCLCs')[None].value) \
									+ " " + str(getattr(instance, 'NumSats')[None].value) \
									+ " " + str(tend - tstart) + "\n")
	foutmain.close()
except:
	opt.options['PSDTol'] = 1e-6
	try:
		tstart = time.time()
		results = opt.solve(instance)#, tee=True)
		tend = time.time()
		
		foutmain = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
		foutmain.write(str(network) + " " + str(getattr(instance, 'NumCRCs')[None].value) \
										+ " " + str(getattr(instance, 'NumCLCs')[None].value) \
										+ " " + str(getattr(instance, 'NumSats')[None].value) \
										+ " " + str(tend - tstart) + "\n")
		foutmain.close()
	except:
		opt.options['PreQLinearize'] = 1
		try:
			tstart = time.time()
			results = opt.solve(instance)#, tee=True)
			tend = time.time()
			
			foutmain = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
			foutmain.write(str(network) + " " + str(getattr(instance, 'NumCRCs')[None].value) \
											+ " " + str(getattr(instance, 'NumCLCs')[None].value) \
											+ " " + str(getattr(instance, 'NumSats')[None].value) \
											+ " " + str(tend - tstart) + "\n")
			foutmain.close()
		except:
			foutmain = open('Instances/Test_' + str(test) + '/_Results_test_' + str(test) + '_' + scenario + '.dat', "a")
			foutmain.write(str(network) + " failed \n")
			foutmain.close()
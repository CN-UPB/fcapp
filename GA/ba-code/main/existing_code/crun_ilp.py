from __future__ import division
import time

import coopr.environ
from coopr.pyomo import *
from coopr.opt import *
from fcpf_ilp import model

print("START crun_ilp")

filename = '../../res/cpp/f/f2.dat'

solver = 'gurobi'
solver_io = 'python'
stream_solver = True
individual_results = False

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

instance = model.create(filename)

tstart = time.time()
results = opt.solve(instance, tee=True)
tend = time.time()

instance.load(results)

print("CRCs used: " + str(getattr(instance, 'NumCRCs')[None].value))
print("CLCs used: " + str(getattr(instance, 'NumCLCs')[None].value))
print("Flows satisfied: " + str(getattr(instance, 'NumSats')[None].value))
print("Runtime: " + str(tend - tstart))

if individual_results:
	fout = open('Results_' + filename, "w")
	
	for v in instance.active_components(Var):
		fout.write(str(v) + "\n")
		varobject = getattr(instance, v)
		for index in varobject:
			fout.write("   " + str(index) + " " + str(varobject[index].value) + "\n")
		fout.write("\n")

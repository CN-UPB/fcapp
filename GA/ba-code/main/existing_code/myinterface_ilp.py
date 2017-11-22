from __future__ import division
import time

#import coopr.environ
from coopr.pyomo import *

from coopr.opt import *
from fcpf_ilp import model

def run_ilp(filename):
	"""returns gurobi optimization instance"""
	print("START run_ilp")

	solver = 'gurobi'
	solver_io = 'python'

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

	instance = model.create(str(filename))

	tstart = time.time()
	results = opt.solve(instance, tee=True)
	tend = time.time()

	instance.load(results)

	print("CRCs used: " + str(getattr(instance, 'NumCRCs')[None].value))
	print("CLCs used: " + str(getattr(instance, 'NumCLCs')[None].value))
	print("Flows satisfied: " + str(getattr(instance, 'NumSats')[None].value))
	print("Runtime: " + str(tend - tstart))

	return instance
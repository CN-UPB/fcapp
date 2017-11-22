from __future__ import (absolute_import, division, print_function)
import cProfile
import os
import time
from existing_code import myinterface
from mycode import validator
from mycode.cpp_equal_share import *
import traceback
from mycode.utilf import println
import util

def test_ga(cn):
	ces = CppEqualShare(cn)
	ces.run()
	best_individual = ces._ga_runner.get_best_individual()
	best_individual.revaluate()
	#println(ces.cn.to_string(verbose=True))
	result_str = "dt: {}, fit: {}, ind: {}, info: {}".format(ces._ga_runner.elapsed_time, best_individual.fitness, best_individual,
															 ces.cn.to_string(verbose=False).replace("\n", "|"))
	println(result_str)
	#validator.validate_cpp_network(ces.cn, check_redundancy=False)

def test_greedy(cn, mesh_filename,ldf=False):
	start_of_computation = time.clock()
	cpg = myinterface.run_greedy(filename=mesh_filename,use_least_demanding=ldf)
	elapsed_time = time.clock() - start_of_computation
	# println(util.print_cpg(cpg))
	cn.copy_fcpg_solution(cpg.cn)
	# println(cn.to_string(verbose=True))
	T.assertEqual(cn.V, set(cpg.cn.V))
	T.assertIsNotNone(cn.G.graph["l_CLC"])
	ind = Individual2(cn)
	ind.set_fitness_values(cn.compute_fitness_values())
	result_str = "dt: {}, fit: {}, ind: {}, info: {}".format(elapsed_time, ind.fitness, ind,
															 cn.to_string(verbose=False).replace("\n", "|"))
	println(result_str)
	validator.validate_cpp_network(cn, check_redundancy=False)


def f():
	#input = "representation=greedy,flowOrder=random,numFlows=100,mu=5,fitness4th=min,vcFactor=1.2"
	#sys.argv = ["./run", "8", input]
	assert len(sys.argv) == 3
	#print(sys.argv)
	#exit(1)

	config_dic = util.set_settings()
	cn, mesh_filename = util.create_cn(config_dic)
	if config.REPRESENTATION == "greedy":
		test_greedy(cn, mesh_filename,ldf=True)
	else:
		test_ga(cn)

if __name__ == "__main__":
	f()

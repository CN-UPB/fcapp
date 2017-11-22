from __future__ import division
from existing_code.fcpf_greedy import CPGreedy


def run_greedy(filename, controller_prob=None, use_least_demanding=False):
	"""returns CPGreedy"""
	cpg = CPGreedy(filename=filename, flowOption="LeastDemanding" if use_least_demanding else "MostDemanding",
				   modify_controllers=controller_prob is not None, contrProb=controller_prob)
	cpg.cpgreedy()
	return cpg

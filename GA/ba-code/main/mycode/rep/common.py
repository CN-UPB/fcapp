from __future__ import (absolute_import, division, print_function)


def remove_duplicate_individuals(individuals):
	x = sorted(individuals, key=lambda it: it.fitness)
	filtered_inds = [x[0]] + [x[it] for it in range(1, len(individuals))
							  if x[it] != x[it - 1]]
	return filtered_inds

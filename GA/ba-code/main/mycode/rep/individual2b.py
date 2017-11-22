from __future__ import (absolute_import, division, print_function)
from array import array
import copy
import random

from mycode import mydeap
from mycode.rep.fitness import Fitness
from mycode.settings import config


# print("using REPR-C = reprb + fperm order")
from mycode.rep.individual_base import IndividualBase

class Individual2b(IndividualBase):
	"""
	REPR C:
	Represents an individual. has a fitness.
	each individual specifies which crcs and clcs are to be used and fperm for flow processing order
	evaluation tries in that order to fulfil all requirements by using shortest possible paths.
	assignments crcs to clcs are made first, then clc-bs, then flows.
	within each of the first two groups, shortest satisfaction is done first.
	"""

	def __init__(self, cn):
		super(Individual2b, self).__init__()
		self.cn = cn
		self.fitness = Fitness()
		self.crcs = array('B', (False for _ in self.cn.C))
		self.clcs = array('B', (False for _ in self.cn.C))
		self.fperm = [i for i in xrange(len(self.cn.F))]

	def __str__(self):
		return "{}, {}, {}".format(self.fitness, str(self.crcs.tolist()), str(self.clcs.tolist()))

	def short_str(self):
		return str(self)

	def __deepcopy__(self, memo):
		"""Replace the basic deepcopy function with a faster one."""
		cls = self.__class__
		result = cls.__new__(cls)
		result.cn = self.cn
		result.fitness = copy.deepcopy(self.fitness, memo)
		result.crcs = copy.deepcopy(self.crcs, memo)
		result.clcs = copy.deepcopy(self.clcs, memo)
		result.fperm = copy.deepcopy(self.fperm, memo)
		return result

	@classmethod
	def create_random(cls, cn):
		self = cls(cn)
		for i in xrange(len(self.crcs)):
			self.crcs[i] = random.random() < .2
		for i in xrange(len(self.clcs)):
			self.clcs[i] = random.random() < .5
		random.shuffle(self.fperm)
		use_least_demanding_flow_first = random.random() < .5
		self.fperm.sort(reverse=not use_least_demanding_flow_first,
						key=lambda it: self.cn.flows[it].p_flow)
		if random.random() < .6:
			self.fperm.sort(key=lambda it: -len(self.cn.flows[it].nodes))
		return self

	def set_fitness_values(self, values):
		self.fitness.values = values

	def _get_controller_id_set(self, c_array):
		ids = set()
		for i in xrange(len(c_array)):
			if c_array[i]:
				ids.add(self.cn.C_list[i])
		return ids

	def _evaluate(self):
		self.cn.restore_backup()
		crc_set, clc_set = map(self._get_controller_id_set, (self.crcs, self.clcs))
		self.cn.route_crc_controls(crc_set, clc_set)
		self.cn.route_clc_controls(clc_set)
		self.cn.route_flow_satisfactions(clc_set, self.fperm)
		self.set_fitness_values(self.cn.compute_fitness_values())

	@staticmethod
	def mate(ind1, ind2):
		'copies uniformly randomly half of the genes from one parent, half of the other parent'
		child = Individual2b(ind1.cn)
		if random.random() < .5:
			for i in xrange(len(child.crcs)):
				child.crcs[i] = ind1.crcs[i] or ind2.crcs[i]
			for i in xrange(len(child.clcs)):
				child.clcs[i] = ind1.clcs[i] or ind2.clcs[i]
		else:
			for i in xrange(len(child.crcs)):
				child.crcs[i] = ind1.crcs[i] and ind2.crcs[i]
			for i in xrange(len(child.clcs)):
				child.clcs[i] = ind1.clcs[i] and ind2.clcs[i]
		child.fperm = mydeap.cx_alternating_position(ind1.fperm, ind2.fperm)
		return child

	@staticmethod
	def mutate(ind):
		child = copy.deepcopy(ind)
		num_unsatisfied_flows = child.fitness.unsatisfied_flows
		child.fitness.invalidate()
		mydeap.mutShuffleIndexes(child.fperm, config.MUTR)
		attr = child.crcs
		if random.random() < .9:
			attr = child.clcs
		if num_unsatisfied_flows > 0:
			if sum(attr) != len(attr):
				index = random.choice([i for i, v in enumerate(attr) if not v])
				attr[index] = not attr[index]
			return child

		if sum(attr) <= 1:
			return child
		n_max = min(sum(attr), sum(1 - it for it in attr) + 1, 5)
		n = random.choice(range(1, n_max + 1))
		flips = random.sample([i for i, v in enumerate(attr) if v], n)
		flips.extend(random.sample([i for i, v in enumerate(attr) if not v], n - 1))
		for i in flips:
			attr[i] = not attr[i]
		return child

	def __ne__(self, other):
		return not self == other

	def __eq__(self, other):
		return self.clcs == other.clcs and self.crcs == other.crcs

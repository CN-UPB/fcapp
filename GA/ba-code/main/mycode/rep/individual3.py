from __future__ import (absolute_import, division, print_function)
import copy
import random

from mycode import mydeap
from mycode.rep.fitness import Fitness
from mycode.settings import config

#print("using REPR-E (clc permutations + greedy run)")

from mycode.rep.individual_base import IndividualBase

class Individual3(IndividualBase):

	def __init__(self, cn):
		super(Individual3, self).__init__()
		self.cn = cn
		self.fitness = Fitness()
		self.clc_perm = list(cn.C)
		random.shuffle(self.clc_perm)

	def __str__(self):
		return "{}, {}".format(self.fitness, str(self.clc_perm))

	def short_str(self):
		return str(self)

	def __deepcopy__(self, memo):
		"""Replace the basic deepcopy function with a faster one."""
		cls = self.__class__
		result = cls.__new__(cls)
		result.cn = self.cn
		result.fitness = copy.deepcopy(self.fitness, memo)
		result.clc_perm = copy.deepcopy(self.clc_perm, memo)
		return result

	@classmethod
	def create_random(cls, cn):
		self = cls(cn)
		return self

	def set_fitness_values(self, values):
		self.fitness.values = values

	def _evaluate(self):
		self.cn.greedy_runner.run_greedy(self)
		self.set_fitness_values(self.cn.compute_fitness_values())

	@staticmethod
	def mate(ind1, ind2):
		'copies uniformly randomly half of the genes from one parent, half of the other parent'
		child = Individual3(ind1.cn)
		child.clc_perm = mydeap.cx_alternating_position(ind1.clc_perm, ind2.clc_perm)
		return child

	@staticmethod
	def mutate(ind):
		child = copy.deepcopy(ind)
		child.fitness.invalidate()
		mydeap.mutShuffleIndexes(child.clc_perm, config.MUTR)
		return child

	def __ne__(self, other):
		return not self == other

	def __eq__(self, other):
		return self.clc_perm == other.clc_perm

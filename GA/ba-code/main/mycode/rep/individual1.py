from __future__ import (absolute_import, division, print_function)
from array import array
from collections import Counter
import copy
import random

from mycode import utilf
from mycode.rep.fitness import Fitness
from mycode.settings import config


# print("using REPR-A (pure GA, supervision/control/satisfaction assignments)")

from mycode.rep.individual_base import IndividualBase

class Individual1(IndividualBase):
	"""
	Represents an individual. has a fitness.
	each individual is an contains the crc for each controller (-1 if none),
	the clc for each node (-1 if none), and the clc for each flow satisfaction (-1 if none)
	evaluation tries in that order to fulfil all these requirements by using shortest possible paths.
	"""

	def __init__(self, cn):
		super(Individual1, self).__init__()
		self.cn = cn
		self.fitness = Fitness()
		self.crcs = array('h', (-1 for _ in self.cn.C))
		self.clcs = array('h', (-1 for _ in self.cn.V))
		self.sats = array('i', (-1 for _ in self.cn.F))

		#: 582.626907, fit: (0,0,6,0.000),6.00 array
		#12: GEN: 159
		#12: dt: 860.63946, fit: (0,0,6,0.000),6.00 list
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
		result.sats = copy.deepcopy(self.sats, memo)
		return result

	@classmethod
	def create_random(cls, cn):
		self = cls(cn)
		for i in xrange(len(self.crcs)):
			self.crcs[i] = random.choice(self.cn.C_list)
		for i in xrange(len(self.clcs)):
			self.clcs[i] = random.choice(self.cn.C_list)
		for i in xrange(len(self.sats)):
			self.sats[i] = random.choice(self.cn.C_list)
		return self

	def set_fitness_values(self, values):
		self.fitness.values = values

	def _evaluate(self):
		self.cn.restore_backup()
		self.cn._route_assignment_requests(self.crcs, self.cn._route_crc_request)
		self.cn._route_assignment_requests(self.clcs, self.cn._route_clc_request)
		self.cn._route_assignment_requests(self.sats, self.cn._route_sat_request)
		self.set_fitness_values(self.cn.compute_fitness_values())

	@staticmethod
	def mate(ind1, ind2):
		'copies uniformly randomly half of the genes from one parent, half of the other parent'
		ind3 = Individual1(ind1.cn)
		crc_usage, clc_usage = Counter(), Counter()
		for attr_name, usage in zip(["crcs", "clcs", "sats"], [crc_usage, clc_usage, clc_usage]):
			a, b = getattr(ind1, attr_name), getattr(ind2, attr_name)
			for i in xrange(len(a)):
				usage[a[i]] += 1
				usage[b[i]] += 1
		for attr_name, usage in zip(["crcs", "clcs", "sats"], [crc_usage, clc_usage, clc_usage]):
			a, b, c = getattr(ind1, attr_name), getattr(ind2, attr_name), getattr(ind3, attr_name)
			for i in xrange(len(a)):
				x, y = a[i], b[i]
				if ind1.fitness.unsatisfied_flows == 0 and ind2.fitness.unsatisfied_flows == 0:
					pass  # x, y = y, x
				c[i] = y
				if random.random() > .5:  # usage[a[i]] / (usage[a[i]] + usage[b[i]]):
					c[i] = x
		return ind3

	@staticmethod
	def mutate(ind):
		child = copy.deepcopy(ind)

		if child.fitness.control_violations > 0 or random.random() < .2:
			child._mut1()
		if child.fitness.unsatisfied_flows > 0 or random.random() < .4:
			child._mut2()
		if child.fitness.control_violations + child.fitness.unsatisfied_flows == 0:
			child._mut3()
		child.fitness.invalidate()
		return child

	def _mut1(self):
		for attr in self.crcs, self.clcs:
			for i in xrange(len(attr)):
				if random.random() < config.MUTR:
					attr[i] = random.choice(self.cn.C_list)

	def _mut2(self):
		for i in xrange(len(self.sats)):
			if random.random() < config.MUTR:
				self.sats[i] = random.choice(self.cn.C_list)

	def _mut3(self):
		disable_crc = random.random() < .3
		attrs_to_look_at = [self.clcs, self.sats]  # shutdown only clc
		if disable_crc:  # shutdown only crc
			attrs_to_look_at = [self.crcs]
		controller_usage = Counter({-1: 0})
		for attr in attrs_to_look_at:
			for i in attr:
				controller_usage[i] += 1
		if -1 in controller_usage:
			del controller_usage[-1]
		usage_list = sorted((k for k, v in controller_usage.iteritems() if v > 0), key=controller_usage.get)
		if len(usage_list) <= 1:
			return
		new_unused_controllers = utilf.exponential_multi_selection(usage_list, use_prob=.8, stop_prob=.2)
		if len(new_unused_controllers) == 0:
			new_unused_controllers = [usage_list[0]]
		if not disable_crc:
			for it in new_unused_controllers:
				self.crcs[self.cn.C_indices[it]] = -1
		old_unused_controllers = tuple(self.cn.C - set(usage_list))
		if len(old_unused_controllers) < len(new_unused_controllers) - 1:
			return
		new_used_controllers = random.sample(old_unused_controllers, len(new_unused_controllers) - 1)
		available_controllers = tuple(set(new_used_controllers) | set(usage_list) - set(new_unused_controllers))
		for attr in attrs_to_look_at:
			for i in xrange(len(attr)):
				if attr[i] in new_unused_controllers:
					attr[i] = random.choice(available_controllers)

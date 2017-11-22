from __future__ import (absolute_import, division, print_function)
import traceback
import sys

from . import utilc, ga
from mycode.rep.individual3b import Individual3b
from mycode.utilf import println
from .settings import *
from .constants import *
from mycode.rep import common
from mycode.rep.fitness import Fitness
from mycode import mydeap, utilf
from mycode.rep.individual1 import Individual1
from mycode.rep.individual2 import Individual2
from mycode.rep.individual2b import Individual2b
from mycode.rep.individual3 import Individual3
from mycode.rep.individual3c import Individual3c

class CppEqualShare(object):
	# region init
	def __init__(self, cn):

		self.cn = cn
		self.cn._create_backup()
		self.individual_cls = {"ga1": Individual1, "ga2": Individual2, "ga2b": Individual2b, "ga3": Individual3,
							   "ga3b": Individual3b, "ga3c": Individual3c}[config.REPRESENTATION]
		self.individual_cls.cn = self.cn
		Fitness.set_weights(self.cn.C, self.cn.F)

		self._init_deap()
		self._ga_runner = ga.Runner(self.toolbox)

	def _init_deap(self):
		self.toolbox = mydeap.Toolbox()
		self.toolbox.register("individual", lambda: self.individual_cls.create_random(self.cn))
		self.toolbox.register("population", mydeap.initRepeat, list, self.toolbox.individual)
		self.toolbox.register("evaluate", lambda ind: ind.evaluate())
		self.toolbox.register("mate", self._mate)
		self.toolbox.register("mutate", self._mutate)
		self.toolbox.register("local_optimization", FNONE)
		self.toolbox.register("callback", self._callback)
		self.toolbox.register("termination", utilc.Terminator(config.TERMINATION_MAX_COUNTER).termination)
		self.toolbox.register("select_survivors", self._select_survivors)
		if config.PARENT_SELECTION == "tournament":
			self.toolbox.register("select_parents", mydeap.selTournament, tournsize=config.TSIZE)
		else:
			assert False, "todo"
			self.toolbox.register("select_parents", mydeap.selRoulette)

	# endregion

	def run(self):
		try:
			self._ga_runner.run()
		except Exception, err:
			print(utilf.h2("caught exception, quitting application now"), file=sys.stderr)
			traceback.print_exc()
			sys.exit()
			print(utilf.h1("BEST INDIVIDUAL SO FAR, BEFORE PREMATURE TERMINATION:"))
			best_ind = self._ga_runner.get_best_individual()
			best_ind.evaluate()
			from mycode import validator
			validator.validate_cpp_network(self.cn)
			sys.exit()

	# region operations
	def _mutate(self, individual):
		child = self.individual_cls.mutate(individual)
		assert not child.fitness.valid
		return child

	def _mate(self, ind1, ind2):
		child = self.individual_cls.mate(ind1, ind2)
		assert not child.fitness.valid
		return child

	def _select_survivors(self, population, offspring):
		if config.SURVIVOR_SELECTION == "best":
			all_individuals = population + offspring
			filtered_individuals = common.remove_duplicate_individuals(all_individuals)
			# for i in xrange(1, len(filtered_individuals)):
			# 	assert filtered_individuals[i].fitness.score >= filtered_individuals[i - 1].fitness.score
			population[:] = filtered_individuals[:config.MU]
		elif config.SURVIVOR_SELECTION == "tournament":
			mydeap.select_survivors_by_negative_tournament(population, offspring, tournsize=config.TSIZE)
		else:
			assert False

	# endregion
	# region misc

	def _callback(self, population, generation):
		if PRINT_GEN:
			println("GEN: " + str(generation))
			for i in population[:1]:
				println(i.short_str())

	# endregion

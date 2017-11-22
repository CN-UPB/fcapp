import time
import random
from mycode.utilf import println

from settings import config
from constants import *


class Runner(object):
	"""
	For all genetic operations, the individuals will be deep-copied before applying the operation.
	The toolbox should be provided with selection, mutation and crossover operations.
	Mutation is assumed to modify the individual in-place.
	Crossover is assumed to return the one child, weather or not the parents were modified is irrelevant.
	"""

	def __init__(self, toolbox):
		self.current_generation = 0
		self.toolbox = toolbox
		self._population = None

		def evaluate_invalid_individuals(population):
			invalid_inds = [ind for ind in population if not ind.fitness.valid]
			for ind in invalid_inds:
				ind.evaluate()
			return invalid_inds

		self.toolbox.register("evaluate_invalid_individuals", evaluate_invalid_individuals)

	def run(self):
		start_of_computation = time.clock()
		self._population = self.toolbox.population(n=config.MU)
		random.shuffle(self._population)

		self.evolve()
		self.elapsed_time = time.clock() - start_of_computation

	def evolve(self):

		self.toolbox.evaluate_invalid_individuals(self._population)

		def create_offspring():
			selected_parents = self.toolbox.select_parents(self._population, config.MU)
			# selected_parents = population # todo test
			offspring = []
			for _ in xrange(config.LAMBDA):
				op_choice = random.random()
				if op_choice < config.CXPB:  # Apply crossover
					ind1, ind2 = random.sample(selected_parents, 2)
					child = self.toolbox.mate(ind1, ind2)
					offspring.append(child)
				else:  # Apply mutation
					ind = random.choice(selected_parents)
					child = self.toolbox.mutate(ind)
					offspring.append(child)
			return offspring

		for gen in range(1, config.NGEN + 1):
			self.current_generation = gen
			offspring = create_offspring()

			self.toolbox.evaluate_invalid_individuals(offspring)
			self.toolbox.select_survivors(self._population, offspring)
			self.toolbox.callback(self._population, gen)

			if self.toolbox.termination(self._population):
				break

	def get_best_individual(self):
		return min(self._population, key=lambda it: it.fitness)

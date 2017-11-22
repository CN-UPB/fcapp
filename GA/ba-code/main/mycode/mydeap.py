from copy import deepcopy
from functools import partial
import random


class Toolbox(object):
	"""A toolbox for evolution that contains the evolutionary operators. At
    first the toolbox contains a :meth:`~deap.toolbox.clone` method that
    duplicates any element it is passed as argument, this method defaults to
    the :func:`copy.deepcopy` function. and a :meth:`~deap.toolbox.map`
    method that applies the function given as first argument to every items
    of the iterables given as next arguments, this method defaults to the
    :func:`map` function. You may populate the toolbox with any other
    function by using the :meth:`~deap.base.Toolbox.register` method.

    Concrete usages of the toolbox are shown for initialization in the
    :ref:`creating-types` tutorial and for tools container in the
    :ref:`next-step` tutorial.
    """

	def __init__(self):
		self.register("clone", deepcopy)
		self.register("map", map)

	def register(self, alias, function, *args, **kargs):
		pfunc = partial(function, *args, **kargs)
		pfunc.__name__ = alias
		pfunc.__doc__ = function.__doc__

		if hasattr(function, "__dict__") and not isinstance(function, type):
			# Some functions don't have a dictionary, in these cases
			# simply don't copy it. Moreover, if the function is actually
			# a class, we do not want to copy the dictionary.
			pfunc.__dict__.update(function.__dict__.copy())

		setattr(self, alias, pfunc)

	def unregister(self, alias):
		"""Unregister *alias* from the toolbox.

		:param alias: The name of the operator to remove from the toolbox.
		"""
		delattr(self, alias)

	def decorate(self, alias, *decorators):
		"""Decorate *alias* with the specified *decorators*, *alias*
		has to be a registered function in the current toolbox.

		:param alias: The name of the operator to decorate.
		:param decorator: One or more function decorator. If multiple
						  decorators are provided they will be applied in
						  order, with the last decorator decorating all the
						  others.

		.. note::
			Decorate a function using the toolbox makes it unpicklable, and
			will produce an error on pickling. Although this limitation is not
			relevant in most cases, it may have an impact on distributed
			environments like multiprocessing.
			A function can still be decorated manually before it is added to
			the toolbox (using the @ notation) in order to be picklable.
		"""
		pfunc = getattr(self, alias)
		function, args, kargs = pfunc.func, pfunc.args, pfunc.keywords
		for decorator in decorators:
			function = decorator(function)
		self.register(alias, function, *args, **kargs)


######################################
# GA Mutations                       #
######################################

def mutGaussian(seq, mu, sigma):
	for i in xrange(len(seq)):
		seq[i] += random.gauss(mu=mu, sigma=sigma)



def mutPolynomialBounded(individual, eta, low, up, indpb):
	"""Polynomial mutation as implemented in original NSGA-II algorithm in
	C by Deb.

	:param individual: :term:`Sequence <sequence>` individual to be mutated.
	:param eta: Crowding degree of the mutation. A high eta will produce
				a mutant resembling its parent, while a small eta will
				produce a solution much more different.
	:param low: A value or a :term:`python:sequence` of values that
				is the lower bound of the search space.
	:param up: A value or a :term:`python:sequence` of values that
			   is the upper bound of the search space.
	:returns: A tuple of one individual.
	"""
	size = len(individual)
	if not isinstance(low, Sequence):
		low = repeat(low, size)
	elif len(low) < size:
		raise IndexError("low must be at least the size of individual: %d < %d" % (len(low), size))
	if not isinstance(up, Sequence):
		up = repeat(up, size)
	elif len(up) < size:
		raise IndexError("up must be at least the size of individual: %d < %d" % (len(up), size))

	for i, xl, xu in zip(xrange(size), low, up):
		if random.random() <= indpb:
			x = individual[i]
			delta_1 = (x - xl) / (xu - xl)
			delta_2 = (xu - x) / (xu - xl)
			rand = random.random()
			mut_pow = 1.0 / (eta + 1.)

			if rand < 0.5:
				xy = 1.0 - delta_1
				val = 2.0 * rand + (1.0 - 2.0 * rand) * xy ** (eta + 1)
				delta_q = val ** mut_pow - 1.0
			else:
				xy = 1.0 - delta_2
				val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * xy ** (eta + 1)
				delta_q = 1.0 - val ** mut_pow

			x = x + delta_q * (xu - xl)
			x = min(max(x, xl), xu)
			individual[i] = x
	return individual,


def mutShuffleIndexes(individual, indpb):
	"""Shuffle the attributes of the input individual and return the mutant.
	The *individual* is expected to be a :term:`sequence`. The *indpb* argument is the
	probability of each attribute to be moved. Usually this mutation is applied on
	vector of indices.

	:param individual: Individual to be mutated.
	:param indpb: Independent probability for each attribute to be exchanged to
				  another position.
	:returns: A tuple of one individual.

	This function uses the :func:`~random.random` and :func:`~random.randint`
	functions from the python base :mod:`random` module.
	"""
	size = len(individual)
	for i in xrange(size):
		if random.random() < indpb:
			swap_indx = random.randint(0, size - 2)
			if swap_indx >= i:
				swap_indx += 1
			individual[i], individual[swap_indx] = \
				individual[swap_indx], individual[i]

	return individual,


def mutFlipBit(individual, indpb):
	"""Flip the value of the attributes of the input individual and return the
	mutant. The *individual* is expected to be a :term:`sequence` and the values of the
	attributes shall stay valid after the ``not`` operator is called on them.
	The *indpb* argument is the probability of each attribute to be
	flipped. This mutation is usually applied on boolean individuals.

	:param individual: Individual to be mutated.
	:param indpb: Independent probability for each attribute to be flipped.
	:returns: A tuple of one individual.

	This function uses the :func:`~random.random` function from the python base
	:mod:`random` module.
	"""
	for i in xrange(len(individual)):
		if random.random() < indpb:
			individual[i] = type(individual[i])(not individual[i])

	return individual,


def mutUniformInt(individual, low, up, indpb):
	"""Mutate an individual by replacing attributes, with probability *indpb*,
	by a integer uniformly drawn between *low* and *up* inclusively.

	:param individual: :term:`Sequence <sequence>` individual to be mutated.
	:param low: The lower bound or a :term:`python:sequence` of
				of lower bounds of the range from wich to draw the new
				integer.
	:param up: The upper bound or a :term:`python:sequence` of
			   of upper bounds of the range from wich to draw the new
			   integer.
	:param indpb: Independent probability for each attribute to be mutated.
	:returns: A tuple of one individual.
	"""
	size = len(individual)
	if not isinstance(low, Sequence):
		low = repeat(low, size)
	elif len(low) < size:
		raise IndexError("low must be at least the size of individual: %d < %d" % (len(low), size))
	if not isinstance(up, Sequence):
		up = repeat(up, size)
	elif len(up) < size:
		raise IndexError("up must be at least the size of individual: %d < %d" % (len(up), size))

	for i, xl, xu in zip(xrange(size), low, up):
		if random.random() < indpb:
			individual[i] = random.randint(xl, xu)

	return individual,


def selRandom(individuals, k):
	"""Select *k* individuals at random from the input *individuals* with
	replacement. The list returned contains references to the input
	*individuals*.

	:param individuals: A list of individuals to select from.
	:param k: The number of individuals to select.
	:returns: A list of selected individuals.

	This function uses the :func:`~random.choice` function from the
	python base :mod:`random` module.
	"""
	return [random.choice(individuals) for i in xrange(k)]


def selBest(individuals, k):
	"""Select the *k* best individuals among the input *individuals*. The
	list returned contains references to the input *individuals*.

	:param individuals: A list of individuals to select from.
	:param k: The number of individuals to select.
	:returns: A list containing the k best individuals.
	"""
	return sorted(individuals, key=attrgetter("fitness"), reverse=True)[:k]


def selWorst(individuals, k):
	"""Select the *k* worst individuals among the input *individuals*. The
	list returned contains references to the input *individuals*.

	:param individuals: A list of individuals to select from.
	:param k: The number of individuals to select.
	:returns: A list containing the k worst individuals.
	"""
	return sorted(individuals, key=attrgetter("fitness"))[:k]


def selTournament(individuals, k, tournsize):
	"""Select *k* individuals from the input *individuals* using *k*
	tournaments of *tournsize* individuals. The list returned contains
	references to the input *individuals*.

	:param individuals: A list of individuals to select from.
	:param k: The number of individuals to select.
	:param tournsize: The number of individuals participating in each tournament.
	:returns: A list of selected individuals.

	This function uses the :func:`~random.choice` function from the python base
	:mod:`random` module.
	"""
	chosen = []
	for i in xrange(k):
		aspirants = selRandom(individuals, tournsize)
		chosen.append(max(aspirants, key=lambda it: it.fitness))
	return chosen


def selRoulette(individuals, k):
	"""Select *k* individuals from the input *individuals* using *k*
	spins of a roulette. The selection is made by looking only at the first
	objective of each individual. The list returned contains references to
	the input *individuals*.

	:param individuals: A list of individuals to select from.
	:param k: The number of individuals to select.
	:returns: A list of selected individuals.

	This function uses the :func:`~random.random` function from the python base
	:mod:`random` module.

	.. warning::
	   The roulette selection by definition cannot be used for minimization
	   or when the fitness can be smaller or equal to 0.
	"""
	s_inds = sorted(individuals, key=attrgetter("fitness"), reverse=True)
	sum_fits = sum(ind.fitness.values[0] for ind in individuals)

	chosen = []
	for i in xrange(k):
		u = random.random() * sum_fits
		sum_ = 0
		for ind in s_inds:
			sum_ += ind.fitness.values[0]
			if sum_ > u:
				chosen.append(ind)
				break

	return chosen


def initRepeat(container, func, n):
	return container(func() for _ in xrange(n))


# MY things ========================


def negative_tournament(individuals, tournsize):
	therange = range(len(individuals))
	aspirants = [random.choice(therange) for _ in range(tournsize)]
	return max(aspirants, key=lambda x: individuals[x].fitness)


def select_survivors_by_negative_tournament(population, offspring, tournsize):
	random.shuffle(offspring)
	for ind in offspring:
		to_be_replaced = negative_tournament(population, tournsize)
		population[to_be_replaced] = ind


def cx_alternating_position(ind1, ind2):
	assert len(ind1) == len(ind2)
	from utilc import OrderedSet
	child = OrderedSet()
	for a, b in zip(ind1, ind2):
		child.add(a)
		child.add(b)
	assert len(child) == len(ind1)
	return list(child)


def compute_diversity(population):
	sorted_population = sorted(population, key=lambda ind: ind.fitness.values)
	num_different_fitnesses = 1
	num_different_individuals = 1
	for i in range(1, len(sorted_population)):
		if sorted_population[i].fitness.values != sorted_population[i - 1].fitness.values:
			num_different_fitnesses += 1
		if sorted_population[i] != sorted_population[i - 1]:
			num_different_individuals += 1
	return num_different_individuals, num_different_fitnesses

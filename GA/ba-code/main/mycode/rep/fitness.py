from mycode import utilf


class Fitness(object):
	"""
	weight = (1, -1, 1) means that the first and third component are supposed to be maximized,
	while the second component is supposed to be minimized. comparisons are lexicographic by default,
	but you can use the score (the sum of the weighted components) if you want to.
	load quality is mean of min load and avg load (?)
	"""
	weights = (
		1, 1, 1, 1)  # <#control violations>, <#unsatisfied flows>, <#controllers (crcs + clcs), <load quality>>

	def __init__(self, values=None):
		self._values = (1,) * len(self.weights)
		self._score = None
		if values is not None:
			self.values = values

	def _get_values(self):
		return self._values

	def _set_values(self, values):
		assert len(self._values) == len(values)
		self._values = tuple(values)
		self._score = sum(v * w for v, w in zip(self._values, self.weights))
		assert utilf.is_normal_number(self._score)

	values = property(_get_values, _set_values)

	def invalidate(self):
		self._score = None

	@property
	def valid(self):
		"""Assess if a fitness is valid or not."""
		return self._score is not None

	@property
	def score(self):
		"""returns the quality of this fitness as a single float value"""
		return self._score

	def __hash__(self):
		return hash(self.values)

	def __gt__(self, other):
		return not self.__le__(other)

	def __ge__(self, other):
		return not self.__lt__(other)

	def __le__(self, other):
		assert self.valid and other.valid
		return self._score <= other._score

	def __lt__(self, other):
		assert self.valid and other.valid
		return self._score < other._score

	def __eq__(self, other):
		return self._score == other._score

	def __ne__(self, other):
		return not self.__eq__(other)

	@property
	def control_violations(self):
		assert self.valid
		return self._values[0]

	@property
	def unsatisfied_flows(self):
		assert self.valid
		return self._values[1]

	@property
	def controller_sum(self):
		assert self.valid
		return self._values[2]

	@property
	def load_quality(self):
		assert self.valid
		return self._values[3]

	@classmethod
	def set_weights(cls, C, F):
		Fitness.weights = (3. * len(C) * (len(F) + 1.), 3. * len(C), 1., 1.0)

	def __str__(self):
		return "({},{},{},{:.3f}),{:.3f}".format(self.control_violations, self.unsatisfied_flows,
												 self.controller_sum, self.load_quality, self.score)

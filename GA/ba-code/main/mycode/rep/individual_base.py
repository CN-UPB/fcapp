import random


class IndividualBase(object):
	def __init__(self):
		self._last_random_state = None

	def evaluate(self):
		self._last_random_state = random.getstate()
		self._evaluate()

	def _evaluate(self):
		assert False, "implement"

	def revaluate(self):
		backup_random_state = random.getstate()
		random.setstate(self._last_random_state)
		self._evaluate()
		random.setstate(backup_random_state)
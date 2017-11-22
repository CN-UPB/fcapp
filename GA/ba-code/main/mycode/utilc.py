import heapq
import sys

from constants import *


class Logger(object):
	def __init__(self):
		self.terminal = sys.stdout

	def write(self, message):
		self.terminal.write(message)
		self.terminal.flush()

	def flush(self):
		self.terminal.flush()


sys.stdout = Logger()


class Terminator(object):
	def __init__(self, max_num_violations):
		self.max_num_violations = max_num_violations
		self.best_min_fitness = INF
		self.termination_counter = 0

	def termination(self, population):
		fit_min = min(it.fitness.score for it in population)
		if fit_min >= self.best_min_fitness:
			self.termination_counter += 1
			if self.termination_counter >= self.max_num_violations:
				#print("Evolution Terminated since fitness '{0}' didn't improve for '{1}' generations".format(
				#	self.best_min_fitness, self.max_num_violations))
				return True
		else:
			self.termination_counter = 0
		self.best_min_fitness = min(self.best_min_fitness, fit_min)
		return False


class PriorityQueue(object):
	"""very simple prio queue. changing an existing priority item will add a new item instead"""

	def __init__(self):
		self.queue = []
		self._counter = 0  # unique sequence count

	def __len__(self):
		return len(self.queue)

	def empty(self):
		return len(self) == 0

	def put(self, item, priority=0.0):
		self._counter += 1
		heapq.heappush(self.queue, (priority, self._counter, item))

	def pop(self):
		"""
		:return: lowest priority and the corresponding item
		"""
		priority, counter, item = heapq.heappop(self.queue)
		return priority, item


class DynamicPriorityQueue(object):
	"""
	better prio queue, putting an item in again will just update its priority
	lower priority means more important
	"""

	def __init__(self):

		self._pq = []  # list of entries arranged in a heap
		self._entry_finder = {}  # mapping of tasks to entries
		self._counter = 0  # unique sequence count
		self._removed_set = set()  # set of removed tasks counters

	def __len__(self):
		return len(self._pq) - len(self._removed_set)

	def empty(self):
		return len(self) == 0

	def put(self, task, priority=0.0):
		'Add a new task or update the priority of an existing task'
		if task in self._entry_finder:
			self.remove(task)
		self._counter += 1
		entry = (priority, self._counter, task)
		self._entry_finder[task] = entry
		heapq.heappush(self._pq, entry)

	def put_or_decrease(self, task, other_priority):
		"""will just decrease the priority if other_priority is lower, add task is non-existing, else do nothing, returns True on change"""
		if task in self._entry_finder:
			if self._entry_finder[task][0] <= other_priority:
				return False
		self.put(task, priority=other_priority)
		return True

	def remove(self, task):
		'Mark an existing task as REMOVED.  Raise KeyError if not found.'
		self._removed_set.add(self._entry_finder[task][1])
		del self._entry_finder[task]

	def pop(self):
		'Remove and return the lowest priority and its task. Raise KeyError if empty.'
		while self._pq:
			priority, counter, task = heapq.heappop(self._pq)
			if counter in self._removed_set:
				self._removed_set.remove(counter)
			else:
				del self._entry_finder[task]
				return priority, task
		raise KeyError('pop from an empty priority queue')


class Queue(object):
	class Node(object):
		def __init__(self, content):
			self.content = content
			self.next = None

	def __init__(self):
		self._head = None
		self._tail = None
		self._length = 0

	def __len__(self):
		return self._length

	def empty(self):
		return self._length == 0

	def put(self, content):
		new_node = Queue.Node(content)
		if self._length == 0:
			self._head = new_node
			self._tail = self._head
		else:
			self._tail.next = new_node
			self._tail = new_node
		self._length += 1

	def pop(self):
		if self._length == 0:
			return None
		result = self._head.content
		self._head = self._head.next
		self._length -= 1
		return result


class ExtremumFinder(object):
	def __init__(self):
		self.maximum = -INF
		self.minimum = INF

	def update(self, new_value):
		self.maximum = max(new_value, self.maximum)
		self.minimum = min(new_value, self.minimum)

	def update_all(self, new_values):
		new_best_max = max(new_values)
		new_best_min = min(new_values)
		self.maximum = max(new_best_max, self.maximum)
		self.minimum = min(new_best_min, self.minimum)

	@property
	def distance(self):
		return self.maximum - self.minimum


import collections


class OrderedSet(collections.MutableSet):
	def __init__(self, iterable=None):
		self.end = end = []
		end += [None, end, end]  # sentinel node for doubly linked list
		self.map = {}  # key --> [key, prev, next]
		if iterable is not None:
			self |= iterable

	def __len__(self):
		return len(self.map)

	def __contains__(self, key):
		return key in self.map

	def add(self, key):
		if key not in self.map:
			end = self.end
			curr = end[1]
			curr[2] = end[1] = self.map[key] = [key, curr, end]

	def discard(self, key):
		if key in self.map:
			key, prev, next = self.map.pop(key)
			prev[2] = next
			next[1] = prev

	def __iter__(self):
		end = self.end
		curr = end[2]
		while curr is not end:
			yield curr[0]
			curr = curr[2]

	def __reversed__(self):
		end = self.end
		curr = end[1]
		while curr is not end:
			yield curr[0]
			curr = curr[1]

	def pop(self, last=True):
		if not self:
			raise KeyError('set is empty')
		key = self.end[1][0] if last else self.end[2][0]
		self.discard(key)
		return key

	def __repr__(self):
		if not self:
			return '%s()' % (self.__class__.__name__,)
		return '%s(%r)' % (self.__class__.__name__, list(self))

	def __eq__(self, other):
		if isinstance(other, OrderedSet):
			return len(self) == len(other) and list(self) == list(other)
		return set(self) == set(other)


if __name__ == "__main__":
	print(list(OrderedSet("abcabcfdedefihgghi")))

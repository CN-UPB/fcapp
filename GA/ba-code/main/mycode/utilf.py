from __future__ import (absolute_import, division, print_function)
from collections import Counter
import random
import datetime
import numpy as np

from mycode import settings

from mycode.constants import NAN, INF
from mycode.settings import config


def create_empty_function(ret_value):
	def f(*args):
		return ret_value

	return f


def argmax(iterable):
	return max(enumerate(iterable), key=lambda x: x[1])[0]


def argmin(iterable):
	return min(enumerate(iterable), key=lambda x: x[1])[0]


def println(s):
	print("#{}: {}\n".format(config.PROC_ID, s), end="")


def mean(seq):
	counter = 0
	the_sum = 0.0
	for it in seq:
		the_sum += it
		counter += 1
	assert counter > 0
	return the_sum / counter


class Wrapper(object):
	def __init__(self, it):
		self.it = it

	def __str__(self):
		return self.it.__str__()


def wrap(it):
	return Wrapper(it)


def minmax(iterable):
	_min = float("inf")
	_max = -_min
	for value in iterable:
		_min = min(_min, value)
		_max = max(_max, value)
	return _min, _max


def replace_tabs_soft(text, tabsize=8):
	newText = ""
	for line in text.split("\n"):
		while True:
			index = line.find("\t")
			if index < 0:
				break
			num_spaces = tabsize - (index % tabsize)
			line = line.replace("\t", " " * num_spaces, 1)
		newText += line + "\n"
	return newText[:-1]


def rotated_list(l, offset):
	return l[offset:] + l[:offset]


def count_diversity(l):
	sorted_list = sorted(l)
	num = 1
	for i in range(1, len(sorted_list)):
		if sorted_list[i] != sorted_list[i - 1]:
			num += 1
	return num


def timestamp():
	return datetime.datetime.now().strftime("%y%m%d-%H%M%S")


def getModuleDictList(module):
	names = [item for item in dir(module) if not item.startswith("__")]
	return sorted([(it, getattr(module, it)) for it in names])


def sort_pair((a, b)):
	if a > b:
		return b, a
	return a, b


def forAllCall(the_function):
	def f(the_list):
		for it in the_list:
			the_function(it)

	return f


def for_each(the_list, function):
	for item in the_list:
		function(item)


_random_state_stack = []


def push_random_state():
	_random_state_stack.append(random.getstate())


def pop_random_state():
	random.setstate(_random_state_stack.pop())


def kwargsToDict(**kwargs):
	return kwargs


def wrap_method(methodName, **kwargs):
	def wrappedMethod(instance, *args):
		return getattr(instance, methodName)(*args, **kwargs)

	return wrappedMethod


def clamp(x, low, up):
	if x < low:
		return low
	if x > up:
		return up
	return x


def create_color_string(r, g, b):
	def to_hex(x):
		i = clamp(int(x * 256.0), 0, 255)
		s = hex(i)[2:]
		if len(s) == 1:
			return "0" + s
		return s

	sr, sg, sb = to_hex(r), to_hex(g), to_hex(b)
	return "#{0}{1}{2}".format(sr, sg, sb)


def create_random_color_string():
	[r, g, b] = [random.random() for _ in range(3)]
	return create_color_string(r, g, b)


def index_of_element_in_list(element, list):
	for index, it in enumerate(list):
		if it == element:
			return index
	return None


_counter = wrap(0)


def get_counter():
	_counter.it += 1
	return _counter.it - 1


def edges_of_path(path):
	'returns edges already by (min, max)'
	for i in xrange(len(path) - 1):
		if path[i] > path[i + 1]:
			yield path[i + 1], path[i]
		else:
			yield path[i], path[i + 1]


def is_edge_of_path(a, b, path):
	for i in xrange(len(path) - 1):
		if (a, b) == (path[i], path[i + 1]) or (b, a) == (path[i], path[i + 1]):
			return True
	return False


def bool_partition_list(pair_list):
	true_list, false_list = [], []
	for item, go_left in pair_list:
		if go_left:
			true_list.append(item)
		else:
			false_list.append(item)
	return true_list, false_list


def indent_value(value, longest_value):
	l = len(str(longest_value))
	s = str(value)
	return " " * (l - len(s)) + s


def count_if(seq, condition):
	"""Returns the amount of items in seq that return true from condition"""
	return sum(1 for item in seq if condition(item))


def safe_min(seq, **kwargs):
	try:
		return min(seq, **kwargs)
	except ValueError:
		return None


def fst(the_tuple):
	return the_tuple[0]


def snd(the_tuple):
	return the_tuple[1]


def trd(the_tuple):
	return the_tuple[2]


def latency_of_path(G, path):
	return sum(G.edge[a][b]["l_cap"] for a, b in edges_of_path(path))


def length_of_path(G, path):
	if config.USE_HOP_PATH_LENGTH:
		return len(path) - 1
	return sum(G.edge[a][b]["l_cap"] for a, b in edges_of_path(path))


def print_header(text):
	print("=" * 60)
	print(text)
	print("=" * 60)


def interpolate_color(a, b, factor):
	return tuple(np.add(a, np.multiply(np.subtract(b, a), factor)))


def move_coord(coord, translation, factor):
	return tuple(np.add(coord, np.multiply(factor, translation)))


def create_index_mapping(the_list):
	dic = {}
	for i, v in enumerate(the_list):
		dic[v] = i
	return dic


def flatten_list(nested_list):
	result = []
	for l in nested_list:
		result.extend(l)
	return result


def sort_and_remove_duplicates(the_list):
	if the_list == None or len(the_list) <= 1:
		return list(the_list)
	sorted_list = sorted(the_list)
	result = [sorted_list[0]]
	for i in range(1, len(sorted_list)):
		if sorted_list[i] != sorted_list[i - 1]:
			result.append(sorted_list[i])
	return result


def cross_product(seq_a, seq_b=None):
	"""generator for crossproduct"""
	if seq_b is None:
		seq_b = seq_a
	for a in seq_a:
		for b in seq_b:
			yield a, b


def cross_product3(seq_a, seq_b, seq_c):
	for a in seq_a:
		for b in seq_b:
			for c in seq_c:
				yield a, b, c


def h1(text):
	return "{1}\n{0}\n{2}".format(text, "=" * 60, "-" * 60)


def h2(text):
	return "{1} {0} {1}".format(text, "=" * 10)


def empty(seq):
	return len(seq) == 0


def safe_div(a, b):
	if b == 0.0:
		return NAN
	return a / b


def exponential_selection(seq, nonskip_prob):
	assert nonskip_prob > 0. and not empty(seq)
	while True:
		for elem in seq:
			if random.random() < nonskip_prob:
				return elem


def exponential_multi_selection(seq, use_prob, stop_prob):
	assert stop_prob > 0. and not empty(seq)
	selected_elements = []
	for elem in seq:
		if random.random() < use_prob:
			selected_elements.append(elem)
		if random.random() < stop_prob:
			break
	return selected_elements


def round_weighed(x):
	if random.random() < x - int(x):
		return int(x) + 1
	return int(x)


def group(seq):
	'returns {(elem, count)} dict'
	counter = Counter()
	for it in seq:
		counter[it] += 1
	return dict(counter)


def sel_weighed(dic):
	'input: dict((val, prob))'
	assert abs(sum(it for it in dic.itervalues()) - 1.0) < .01
	rand_selection = random.random()
	prob_sum = 0.0
	for val, prob in dic.iteritems():
		prob_sum += prob
		if rand_selection <= prob_sum:
			return val
	assert False, "didnt work"


if __name__ == "__main__":
	the_list = group([sel_weighed({0: .2, 1: .4, 2: .1, 3: .3}) for _ in range(100)])
	print(the_list)


def is_normal_number(number):
	return -INF < number < INF

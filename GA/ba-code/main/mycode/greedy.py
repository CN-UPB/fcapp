from __future__ import (absolute_import, division, print_function)
import random

import networkx as nx

from mycode import settings

from mycode.settings import *
from . import algorithms
from mycode.utilc import PriorityQueue
from mycode.utilf import latency_of_path
from mycode.utilf import length_of_path


class GreedyRunner(object):
	def __init__(self, cn):
		self.cn = cn

	def run_greedy(self, ind):
		'clc_perm = [clc5, clc1, ...] with true indices'
		clc_perm = ind.clc_perm
		self.cn.restore_backup()
		self._uncontrolled_nodes = set(self.cn.get_uncontrolled_nodes())
		self._unsatisfied_flows = set(self.cn.get_unsatisfied_flows())
		for counter, clc_id in enumerate(clc_perm):
			path = self._find_crc(clc_id)
			if path is not None:
				self.cn.extra_info.add_crc_control(path)
				self._add_new_clc(counter, clc_id, ind)
			if len(self._uncontrolled_nodes) + len(self._unsatisfied_flows) == 0:
				break
			# cn.extra_info.cleanup_redundant_controls()

	def _find_crc(self, clc_id):
		# check already active CRCs first
		path = algorithms.dijkstra_multi_source(self.cn.G, self.cn.extra_info, source_set=set(self.cn.crcs),
												target=clc_id, use_source_as_clc=False)
		if path is not None:
			return path
		# need to add a new CRC, at first try to avoid active CLCs and CLC candidate
		return self._find_new_crc(clc_id)

	def _find_new_crc(self, clc_id):
		paths = []
		for crc_id in list(set(self.cn.C) - (set(self.cn.crcs) | set(self.cn.clcs) | {clc_id})):
			paths.append(algorithms.llp(self.cn.G, source=crc_id, target=clc_id))
		if len(set(self.cn.crcs)) == 0:  # first CRC should be placed centrally of all the controllers
			paths.sort(key=lambda p: sum(
				length_of_path(self.cn.G, algorithms.llp(self.cn.G, source=p[0], target=c)) for c in self.cn.C))
		else:
			paths.sort(key=lambda p: length_of_path(self.cn.G, p))
		for path in paths:
			if self.cn.extra_info.check_crc(path):
				return path
		# last option: try CLC candidate, then already active CLCs
		if self.cn.extra_info.check_crc([clc_id]):
			return [clc_id]
		paths = sorted([algorithms.llp(self.cn.G, source=old_clc, target=clc_id) for old_clc in self.cn.clcs],
					   key=lambda it: length_of_path(self.cn.G, it))
		for path in paths:
			if self.cn.extra_info.check_crc(path):
				return path
		return None

	def _update_potential_flows(self, pf, clc_id, new_bs):
		'updates set of flows ids'
		clc = self.cn.extra_info.nodes[clc_id]
		for flow_id in set(self.cn.Wf[new_bs]):
			if not self.cn.extra_info.flows[flow_id].is_satisfied and self.cn.flows[flow_id].nodes <= clc.controlled_bs:
				pf.put(flow_id, priority=self._get_flow_priority(flow_id))

	def _get_flow_priority(self, f):
		if config.FLOW_ORDER == "leastDemanding":
			return self.cn.flows[f].p_flow
		if config.FLOW_ORDER == "mostDemanding":
			return -self.cn.flows[f].p_flow
		if config.FLOW_ORDER == "random":
			return random.random()
		assert False, "error"

	def _add_new_clc(self, counter, clc_id, ind):
		paths = []
		pf = PriorityQueue()  # potential flows
		num_new_nodes_controlled = 0
		num_new_flows_satisfied = 0
		if self.cn.extra_info.check_crc([clc_id]):  # add self-control
			if not self.cn.extra_info.nodes[clc_id].is_controlled:
				num_new_nodes_controlled += 1
				self._uncontrolled_nodes.remove(clc_id)
			self.cn.extra_info.add_clc_control([clc_id])
			self._update_potential_flows(pf, clc_id, clc_id)
		else:  # no self-control possible
			self.cn.C.remove(clc_id)
			return
		# search for paths to nodes that are uncontrolled or unsatisfied flows pass through
		for node in self.cn.extra_info.nodes.itervalues():
			if node.node_id != clc_id and (
						not node.is_controlled or len(set(self.cn.Wf[node.node_id]) & self._unsatisfied_flows) > 0):
				paths.append((algorithms.llp(self.cn.G, source=clc_id, target=node.node_id), node.is_controlled,
							  len(set(self.cn.Wf[node.node_id]) & self._unsatisfied_flows)))
		solved = False
		if not self.all_nodes_controlled:
			paths.sort(key=lambda x: x[1])
			paths.sort(key=lambda x: length_of_path(self.cn.G, x[0]))
		else:
			paths.sort(key=lambda x: length_of_path(self.cn.G, x[0]))
			paths.sort(key=lambda x: x[2], reverse=True)
			solved = True
		if config.REPRESENTATION == "ga3":
			nn_minimum = config.VC_FACTOR * self.cn.vc_ratio
		elif config.REPRESENTATION == "ga3b":
			nn_minimum = ind.nn_minimum
		else:
			assert config.REPRESENTATION == "ga3c"
			nn_minimum = ind.nn_minimums[counter]
		while (len(paths) > 0 or len(pf) > 0) and not (self.all_nodes_controlled and self.all_flows_satisfied):
			if not solved and self.all_nodes_controlled:  # resort once all nodes are controlled
				paths.sort(key=lambda x: length_of_path(self.cn.G, x[0]))
				paths.sort(key=lambda x: x[2], reverse=True)
				solved = True
			if len(pf) > 0 and (num_new_nodes_controlled >= nn_minimum or self.all_nodes_controlled):
				_, f = pf.pop()
				if self.cn.extra_info.check_flow_satisfaction(clc_id, f):
					num_new_flows_satisfied += 1
					self.cn.extra_info.add_flow_satisfaction(clc_id, f)
					self._unsatisfied_flows.remove(f)
			elif len(paths) > 0:
				path = list(paths[0][0])
				del paths[0]
				if self.cn.extra_info.check_clc(path):
					bs_id = path[-1]
					if not self.cn.extra_info.nodes[bs_id].is_controlled:
						num_new_nodes_controlled += 1
						self._uncontrolled_nodes.remove(bs_id)
					self.cn.extra_info.add_clc_control(path)
					self._update_potential_flows(pf, clc_id, bs_id)
				elif latency_of_path(self.cn.G, path) > self.cn.extra_info.get_path_latency_limit_of_node_for_new_proc(
						clc_id, use_as_clc=True):
					break
			else:
				break


	@property
	def all_nodes_controlled(self):
		return len(self._uncontrolled_nodes) == 0

	@property
	def all_flows_satisfied(self):
		return len(self._unsatisfied_flows) == 0

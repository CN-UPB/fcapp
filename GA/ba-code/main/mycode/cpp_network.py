from __future__ import (absolute_import, division, print_function)
import random
import traceback
import numpy as np

import networkx as nx

from mycode import utilf
from mycode.constants import *
from mycode.greedy import GreedyRunner
from mycode.settings import *
from mycode.cpp_network_extra import CppNetworkExtraInfo
from . import algorithms

from mycode import settings


# region extra classes
from mycode.utilc import PriorityQueue
from mycode.utilf import empty


class Flow(object):
	def __init__(self, flow_id, nodes, b_flow, l_flow, p_flow, x, y, profit=1.0):
		self.flow_id = flow_id
		self.nodes = nodes
		self.b_flow = b_flow
		self.l_flow = l_flow
		self.p_flow = p_flow
		self.x, self.y = x, y
		self.profit = profit

	@property
	def num_nodes(self):
		return len(self.nodes)


# endregion

class CppNetwork(object):
	def __init__(self):
		self.G = nx.Graph()
		self.extra_info = None
		self.V, self._C, self.C_list, self.F = [None] * 4
		self.flows = {}
		self._extra_info_backup = None
		self.greedy_runner = GreedyRunner(self)
		for key in ["b_CLC", "b_CRC", "l_CLC", "l_CRC", "p_CLC", "p_CRC", "flows", "name", "V", "C", "F"]:
			self.G.graph[key] = None

	# region properties

	def _get_c(self):
		return self._C

	def _set_c(self, new_c):
		self._C = new_c
		self.C_list = list(sorted(self._C))
		self.C_indices = dict((v, k) for k, v in enumerate(self.C_list))

	C = property(_get_c, _set_c)

	@property
	def clcs(self):
		return (node.node_id for node in self.extra_info.nodes.itervalues() if node.is_clc)

	@property
	def crcs(self):
		return (node.node_id for node in self.extra_info.nodes.itervalues() if node.is_crc)

	@property
	def controllers(self):
		return (node.node_id for node in self.extra_info.nodes.itervalues() if node.is_controller)

	@property
	def num_C(self):
		return len(self.C)

	@property
	def num_V(self):
		return len(self.V)

	@property
	def num_flows(self):
		return len(self.F)

	@property
	def num_edges(self):
		return self.G.number_of_edges()

	@property
	def vc_ratio(self):
		return len(self.V) / max(1, (len(self.C) - 1))

	@property
	def all_nodes_controlled(self):
		return all(ninfo.is_controlled for ninfo in self.extra_info.nodes.itervalues())

	def get_used_controllers(self):
		return [c for c in self.C if self.extra_info.nodes[c].is_controller]

	def get_controlled_nodes(self):
		return [ninfo.node_id for _, ninfo in self.extra_info.nodes.iteritems() if ninfo.is_controlled]

	def get_uncontrolled_nodes(self):
		return [ninfo.node_id for _, ninfo in self.extra_info.nodes.iteritems() if not ninfo.is_controlled]

	def get_unsatisfied_flows(self):
		return [finfo.flow_id for _, finfo in self.extra_info.flows.iteritems() if not finfo.is_satisfied]

	@property
	def b_CLC(self):
		return self.G.graph["b_CLC"]

	@property
	def b_CRC(self):
		return self.G.graph["b_CRC"]

	@property
	def l_CLC(self):
		return self.G.graph["l_CLC"]

	@property
	def l_CRC(self):
		return self.G.graph["l_CRC"]

	@property
	def p_CLC(self):
		return self.G.graph["p_CLC"]

	@property
	def p_CRC(self):
		return self.G.graph["p_CRC"]

	# endregion

	# region repr A

	def _route_crc_request(self, crc, clc_index):
		path_latency_limit = self.extra_info.get_path_latency_limit_of_node_for_new_proc(crc, use_as_clc=False)
		clc = self.C_list[clc_index]
		path = algorithms.dijkstra(self.G, self.extra_info, crc, {clc}, self.G.graph["b_CRC"], path_latency_limit)
		if path is None:
			return False
		self.extra_info.add_crc_control(path)

	def _route_clc_request(self, clc, bs_id):
		path_latency_limit = self.extra_info.get_path_latency_limit_of_node_for_new_proc(clc, use_as_clc=True)
		path = algorithms.dijkstra(self.G, self.extra_info, clc, {bs_id}, self.G.graph["b_CLC"], path_latency_limit)
		if path is None:
			return False
		self.extra_info.add_clc_control(path)

	def _route_sat_request(self, clc, flow_id):
		self._fulfill_satisfaction_request(clc, self.flows[flow_id])

	def _route_assignment_requests(self, items, routing_function):
		shuffled = list(enumerate(items))
		random.shuffle(shuffled)
		for item_index, controller in enumerate(items):
			if controller != -1:
				routing_function(controller, item_index)

	# endregion

	# region repr B and C
	def route_crc_controls(self, crcs, clcs):
		'connects crcs to closest clcs until all clcs are coordinated'
		q = PriorityQueue()
		uncontrolled_clcs = set(clcs)

		def find_and_put_crc_path(crc):
			max_path_latency = self.extra_info.get_path_latency_limit_of_node_for_new_proc(crc, use_as_clc=False)
			path = algorithms.dijkstra(self.G, self.extra_info, crc, uncontrolled_clcs,
									   max_path_latency=max_path_latency,
									   required_datarate=self.G.graph["b_CRC"])
			if path is not None:
				q.put(path, priority=utilf.length_of_path(self.G, path))

		for crc in crcs:
			find_and_put_crc_path(crc)
		while not q.empty():
			path_length, path = q.pop()
			crc, clc, latency = path[0], path[-1], utilf.latency_of_path(self.G, path)
			if (clc in uncontrolled_clcs and
						latency <= self.extra_info.get_path_latency_limit_of_node_for_new_proc(crc,
																							   use_as_clc=False) and
					self.extra_info.is_additional_datarate_okay_for_path(path, self.G.graph["b_CRC"])):
				self.extra_info.add_crc_control(path_from_crc_to_clc=path)
				uncontrolled_clcs.remove(clc)
			find_and_put_crc_path(crc)

	def route_clc_controls(self, clcs):
		'connects clcs to closest nodes until all nodes are controlled'
		q = PriorityQueue()
		uncontrolled_bs = set(self.V)

		def find_and_put_clc_path(clc):
			max_path_latency = self.extra_info.get_path_latency_limit_of_node_for_new_proc(clc, use_as_clc=True)
			path = algorithms.dijkstra(self.G, self.extra_info, clc, uncontrolled_bs,
									   max_path_latency=max_path_latency,
									   required_datarate=self.G.graph["b_CRC"])
			if path is not None:
				q.put(path, priority=utilf.length_of_path(self.G, path))

		for clc in clcs:
			find_and_put_clc_path(clc)
		while not q.empty():
			path_length, path = q.pop()
			clc, bs, latency = path[0], path[-1], utilf.latency_of_path(self.G, path)
			# are the constraints now still okay?
			if (bs in uncontrolled_bs and
						latency <= self.extra_info.get_path_latency_limit_of_node_for_new_proc(clc, use_as_clc=True) and
					self.extra_info.is_additional_datarate_okay_for_path(path, self.G.graph["b_CLC"])):
				self.extra_info.add_clc_control(path_from_clc_to_node=path)
				uncontrolled_bs.remove(bs)
			find_and_put_clc_path(clc)

	def route_flow_satisfactions(self, clcs, fperm):
		for flow in (self.flows[it] for it in fperm):
			used_clc, satisfaction_paths, _ = algorithms.flow_dijkstra(self.G, self.extra_info, flow=flow,
																		 source_clcs=clcs)
			if used_clc is not None:
				self.extra_info.add_flow_satisfaction(clc=used_clc, flow_id=flow.flow_id,
													  used_paths_from_clc_to_flow_nodes=satisfaction_paths)
		pass

	def route_flow_satisfactions_by_shortest_path(self, clcs): # todo too slow
		q = PriorityQueue()
		unsatisfied_flows = set(self.F)

		def find_and_put_flow_satisfaction(flow):
			used_clc, satisfaction_paths, max_path_length = algorithms.flow_dijkstra(self.G, self.extra_info, flow=flow,
																					 source_clcs=clcs)
			if used_clc is not None:
				q.put((flow, used_clc, satisfaction_paths), priority=max_path_length)

		for flow in self.flows.itervalues():
			find_and_put_flow_satisfaction(flow)
		while not q.empty():
			path_length, (flow, used_clc, satisfaction_paths) = q.pop()
			max_latency = max(utilf.latency_of_path(self.G, it) for it in satisfaction_paths)
			if (flow.flow_id in unsatisfied_flows and
						max_latency <= self.extra_info.get_path_latency_limit_of_node_for_new_proc(used_clc,
																								   use_as_clc=True,
																								   flow_to_satisfy=flow) and
					self.extra_info.flow_satisfaction_paths_datarate_okay(clc_id=used_clc, flow=flow,
																		  satisfaction_paths=satisfaction_paths)):
				self.extra_info.add_flow_satisfaction(clc=used_clc, flow_id=flow.flow_id,
													  used_paths_from_clc_to_flow_nodes=satisfaction_paths)
				unsatisfied_flows.remove(flow.flow_id)
			else:
				find_and_put_flow_satisfaction(flow)

	# endregion



	# region flow routing

	def _fulfill_satisfaction_request(self, controller, flow):
		controller_info = self.extra_info.nodes[controller]
		edge_b_rem_backup = {}
		path_latency_limit = self.extra_info.get_path_latency_limit_of_node_for_new_proc(controller, use_as_clc=True,
																						 flow_to_satisfy=flow)
		if path_latency_limit < 0:
			return False

		def find_path_to_node_of_flow(node_of_flow):
			'returns path or None'
			already_controlled = node_of_flow in controller_info.controlled_bs
			additional_datarate = flow.b_flow
			if already_controlled:
				path = controller_info.controlled_bs_paths[node_of_flow]
				if not self.extra_info.is_additional_datarate_okay_for_path(path, additional_datarate):
					return None
			else:
				additional_datarate += self.G.graph["b_CLC"]
				path = algorithms.dijkstra(self.G, self.extra_info, source=controller, target_set={node_of_flow},
										   required_datarate=additional_datarate, max_path_latency=path_latency_limit)
				if path is None:
					return None
			for a, b in utilf.edges_of_path(path):
				edge_info = self.extra_info.edges[a, b]
				if not edge_b_rem_backup.has_key(edge_info):
					edge_b_rem_backup[edge_info] = edge_info.b_rem
				edge_info.b_rem -= additional_datarate
			return path

		def undo_tmp_changes():
			for edge_info, original_b_rem in edge_b_rem_backup.iteritems():
				edge_info.b_rem = original_b_rem

		used_paths = []
		for t in flow.nodes:
			path = find_path_to_node_of_flow(t)
			if path is None:  # restore backup when satisfaction failed for one node
				undo_tmp_changes()
				return False
			used_paths.append(path)
		undo_tmp_changes()
		self.extra_info.add_flow_satisfaction(clc=controller, flow_id=flow.flow_id,
											  used_paths_from_clc_to_flow_nodes=used_paths)
		return True

	# endregion

	# region misc
	def restore_backup(self):
		assert self._extra_info_backup is not None
		self.extra_info.restore_backup(self._extra_info_backup)

	def _create_backup(self):
		self._extra_info_backup = self.extra_info.copy()

	def __str__(self):
		return self.to_string()

	def to_string(self, verbose=False):
		output = utilf.wrap("")

		def p(s):
			output.it += s + "\n"

		crcs = [it for it in self.C if self.extra_info.nodes[it].is_crc]
		clcs = [it for it in self.C if self.extra_info.nodes[it].is_clc]
		used_controllers = self.get_used_controllers()
		unused_controllers = self.C - set(used_controllers)
		controlled_nodes, uncontrolled_nodes = utilf.bool_partition_list((ninfo.node_id, ninfo.is_controlled) for
																		 _, ninfo in self.extra_info.nodes.iteritems())
		supervised_clcs, unsupervised_clcs = utilf.bool_partition_list((ninfo.node_id, ninfo.is_supervised) for
																	   _, ninfo in self.extra_info.nodes.iteritems() if
																	   ninfo.is_clc)
		satisfied_flows, unsatisfied_flows = utilf.bool_partition_list(
			(finfo.flow_id, finfo.is_satisfied) for _, finfo in self.extra_info.flows.iteritems())
		avg_flow_size = np.mean([float(flow.num_nodes) for _, flow in self.flows.iteritems()]) if \
			len(self.flows) > 0 else NAN
		avg_satisfied_flow_size = np.mean([float(self.flows[flow_id].num_nodes) for flow_id in satisfied_flows]) if \
			len(satisfied_flows) > 0 else NAN

		def print_general_info():
			p("Graph with {} nodes, {} edges and {} flows".format(self.num_V, self.num_edges, self.num_flows))
			p("Fitness: {}".format(str(self.compute_fitness_values())))
			p("Used {} CRCs: {}".format(len(crcs), crcs))
			p("Used {} CLCs: {}".format(len(clcs), clcs))
			p("Used controllers: {} / {} -> {}".format(len(used_controllers), self.num_C,
													   str(sorted(used_controllers))))
			p("Unused controllers: {} / {} -> {}".format(len(unused_controllers), self.num_C,
														 str(sorted(unused_controllers))))
			p("Uncontrolled nodes: {} -> {}".format(len(uncontrolled_nodes), uncontrolled_nodes))
			p("Control structure violations: {}".format(
				self.extra_info.num_uncontrolled_nodes + self.extra_info.num_unsupervised_clcs))
			p("Controlled nodes: {} / {} = {}%".format(len(controlled_nodes), self.num_V,
													   len(controlled_nodes) * 100.0 / self.num_V))
			p("Supervised CLCs: {} / {} = {}%".format(len(supervised_clcs), len(list(self.clcs)),
													  utilf.safe_div(len(supervised_clcs) * 100.0,
																	 len(list(self.clcs)))))
			p("Satisfied {} / {} flows with mean number-of-nodes of {}, {}".format(len(satisfied_flows), self.num_flows,
																				   avg_satisfied_flow_size,
																				   avg_flow_size))

			edge_b_rems = [einfo.b_rem for _, einfo in self.extra_info.edges.iteritems()]
			edge_b_caps = [edata["b_cap"] for _, _, edata in self.G.edges_iter(data=True)]
			edge_l_caps = [edata["l_cap"] for _, _, edata in self.G.edges_iter(data=True)]
			node_parent_clc_size = [len(it.clcs) for it in self.extra_info.nodes.itervalues()]
			num_controlled_bs = [len(it.controlled_bs) for it in self.extra_info.nodes.itervalues() if it.is_clc]
			p_satisfied_flows = [self.flows[it].p_flow for it in satisfied_flows]
			p_unsatisfied_flows = [self.flows[it].p_flow for it in unsatisfied_flows]
			path_lens_crc = utilf.flatten_list(
				[map(len, it.controlled_clc_paths.values()) for it in self.extra_info.nodes.itervalues()])
			path_lens_clc = utilf.flatten_list(
				[map(len, it.controlled_bs_paths.values()) for it in self.extra_info.nodes.itervalues()])
			path_max_lens_crc = [max(map(len, it.controlled_clc_paths.values())) for it in
								 self.extra_info.nodes.itervalues() if not empty(it.controlled_clc_paths)]
			path_max_lens_clc = [max(map(len, it.controlled_bs_paths.values())) for it in
								 self.extra_info.nodes.itervalues() if not empty(it.controlled_bs_paths)]
			clc_loads = [it.get_clc_load(self) for it in self.extra_info.nodes.itervalues() if it.is_clc]
			for name, l in zip(["b_rem", "b_cap", "l_cap", "#pCLCs", "#coBSs",
								"p-sflows", "p-uflows", "path-len-CRC", "path-len-CLC",
								"path-max-len-CRC", "path-max-len-CLC", "clc_loads"],
							   [edge_b_rems, edge_b_caps, edge_l_caps, node_parent_clc_size, num_controlled_bs,
								p_satisfied_flows, p_unsatisfied_flows,
								path_lens_crc, path_lens_clc, path_max_lens_crc, path_max_lens_clc, clc_loads]):
				line = "{}: <invalid>".format(name)
				if l is not None and len(l) > 0:
					line = "{}: min: {}, max: {}, avg: {}, std: {}".format(name, np.min(l), np.max(l), np.mean(l),
																		   np.std(l))
				p(line)

		if verbose:
			if len(used_controllers) > 0:
				p("CLC, pCLCs, CRC, controlled BS, satisfied flows:")
				max_id = max(used_controllers)
				for clc in sorted(clcs):
					cinfo = self.extra_info.nodes[clc]
					p("{}, {}, {}, {}, {}".format(utilf.indent_value(clc, max_id), list(cinfo.clcs), cinfo.crc,
												  sorted(cinfo.controlled_bs),
												  sorted(cinfo.satisfies)))
				p("CRC, controlled CLC:")
				max_id = max(used_controllers)
				for crc in sorted(crcs):
					cinfo = self.extra_info.nodes[crc]
					p("{}, {}".format(utilf.indent_value(crc, max_id),
									  sorted(cinfo.controlled_clcs)))
			else:
				p("No controllers used")

		print_general_info()
		return output.it

	@property
	def load_quality(self):
		'return avg(avg(clc_loads), min(clc_loads)'
		clc_loads = [it.get_clc_load(self) for it in self.extra_info.nodes.itervalues() if it.is_clc]
		if len(clc_loads) == 0:
			return 1.0
		if config.FITNESS_4TH == "min":
			return min(clc_loads)
		elif config.FITNESS_4TH == "mean":
			return utilf.mean(clc_loads)
		return 0.0

	def compute_fitness_values(self):
		return (self.extra_info.num_uncontrolled_nodes + self.extra_info.num_unsupervised_clcs,
				self.extra_info.num_unsatisfied_flows, self.extra_info.num_clcs + self.extra_info.num_crcs,
				self.load_quality)

	def compute_true_b_rems(self):
		nodes_dic, nodes = self.extra_info.nodes, self.extra_info.nodes.values()
		edges_dic = self.extra_info.edges
		true_rems = {}
		for (a, b), einfo in edges_dic.iteritems():
			true_rems[utilf.sort_pair((a, b))] = self.G.edge[a][b]["b_cap"]
		for crc in self.crcs:
			for clc_path in nodes_dic[crc].controlled_clc_paths.itervalues():
				for edge in utilf.edges_of_path(clc_path):
					true_rems[edge] -= self.G.graph["b_CRC"]
		for clc in self.clcs:
			for target, bs_path in nodes_dic[clc].controlled_bs_paths.iteritems():
				flow_data_rate = sum(flow.b_flow for flow in self.flows.itervalues() if
									 flow.flow_id in nodes_dic[clc].satisfies and target in flow.nodes)
				for edge in utilf.edges_of_path(bs_path):
					true_rems[edge] -= self.G.graph["b_CRC"] + flow_data_rate
		return true_rems

	# endregion

	# region transform

	def copy_ilp_solution(self, ilp_instance):
		"""takes solved ilp instance and transforms cpp_network to be the same solution"""
		assert self.name is not None, "should have been generated by file beforehand"
		assert self.F == set(ilp_instance.F.value) and self.V == set(
			ilp_instance.V.value), "graphs are not based on the same input file"
		self.C.clear()
		self.C.update(ilp_instance.C.value)
		for c in self.C:
			self.G.node[c]["p_node"] = ilp_instance.p_node[c]
		self.restore_backup()
		self.extra_info.copy_ilp_solution(ilp_instance)
		self.extra_info.recompute_true_b_rems()
		self._create_backup()

	def copy_fcpg_solution(self, greedy_cn):
		"""takes the existing crowd_network and transforms cpp_network to be the same solution"""
		assert self.extra_info is not None, "should have been generated by file beforehand"
		assert self.F == set(greedy_cn.F) and self.V == set(greedy_cn.V), "graphs are not based on the same input file"
		self.C.clear()
		self.C.update(greedy_cn.C)
		for c in self.C:
			self.G.node[c]["p_node"] = greedy_cn.G.node[c]["p_node"]
		self.restore_backup()
		self.extra_info.copy_fcpg_solution(greedy_cn)
		self._create_backup()

	# endregion

	def generate_from_file(self, fin):

		try:
			def skip_lines(num_lines):
				for _ in range(num_lines):
					fin.readline()

			tmp = fin.readline()
			self.V = set([int(n) for n in tmp[tmp.find("=") + 2:tmp.find(";") - 1].split(" ")])
			assert self.num_V > 0, "Error: Empty network!"
			assert sorted(list(self.V)) == range(len(self.V)), "V must be zero indexed"
			tmp = fin.readline()
			self.C = set([int(n) for n in tmp[tmp.find("=") + 2:tmp.find(";") - 1].split(" ")])
			self.C_list = list(sorted(self.C))

			assert self.num_C > 0, "Error: No potential controller nodes!"

			self.G.add_nodes_from(self.V)

			tmp = fin.readline()
			self.F = set([int(n) for n in tmp[tmp.find("=") + 2:tmp.find(";") - 1].split()])
			assert sorted(list(self.F)) == range(len(self.F)), "F must be zero indexed"
			tmp = fin.readline()
			for n in tmp[tmp.find("=") + 2:tmp.find(";") - 1].split(" "):
				self.G.add_edge(int(n[n.find("(") + 1:n.find(",")]), int(n[n.find(",") + 1:n.find(")")]))

			skip_lines(2)
			for i in range(0, self.num_V):
				tmp = fin.readline().split(" ")
				node_id = int(tmp[0])
				self.G.node[node_id]['p_node'] = float(tmp[1])
				self.G.node[node_id]['x'] = float(tmp[2])
				self.G.node[node_id]['y'] = float(tmp[3])

			skip_lines(2)
			for _ in range(0, self.num_edges):
				skip_lines(1)  # skip the other, identical edge of the reversed direction
				tmp = fin.readline().split(" ")
				node1_id, node2_id = map(int, tmp[:2])
				self.G.edge[node1_id][node2_id]['b_cap'] = float(tmp[2])
				self.G.edge[node1_id][node2_id]['l_cap'] = float(tmp[3])

			skip_lines(2)
			self.flows = {}
			for _ in self.F:
				tmp = fin.readline().split(" ")
				flow_id = int(tmp[0])
				flow = Flow(flow_id=flow_id, nodes=None, b_flow=float(tmp[1]), l_flow=float(tmp[2]),
							x=float(tmp[3]), y=float(tmp[4]), p_flow=None)
				self.flows[flow_id] = flow

			skip_lines(1)

			def read_float_value():
				tmp = fin.readline()
				return float(tmp[tmp.find("=") + 2:tmp.find(";") - 1])

			for attr, value in zip(["b_CLC", "b_CRC", "l_CLC", "l_CRC", "p_CLC", "p_CRC"],
								   [read_float_value() for _ in range(6)]):
				self.G.graph[attr] = value

			skip_lines(8)
			self.W = {}
			self.Wb = {}
			for f in self.F:
				self.Wb[f] = []
				for j in self.V:
					tmp = fin.readline().split(" ")
					flow_id, node_id, used = map(int, tmp)
					self.W[flow_id, node_id] = used
					if used == 1:
						self.Wb[f].append(node_id)

			self.Wf = {}
			for j in self.V:
				self.Wf[j] = [f for f in self.F if self.W[f, j] == 1]

			for f in self.F:
				self.flows[f].nodes = set(self.Wb[f])
				self.flows[f].p_flow = 4 * self.flows[f].b_flow * len(self.flows[f].nodes)
			self.extra_info = CppNetworkExtraInfo(self)
			self._create_backup()

		except Exception:
			traceback.print_exc()
			exit(1)

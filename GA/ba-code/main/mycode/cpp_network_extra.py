from __future__ import (absolute_import, division, print_function)
from collections import Counter
import copy
import random

from mycode import utilf
from mycode.constants import INF





# all these classes use ids of flows/clcs etc.
from mycode.utilf import empty, latency_of_path, flatten_list, edges_of_path


class NodeInfo(object):
	def __init__(self, node_id):
		"""
		node is controlled, when controlled by a CLC (a CLC controls itself). CRC -> CLC control is irrelevant for this attribute
		a node can be both clc and crc
		"""
		self.node_id = node_id
		self.proc = 0
		self.satisfies = set()  # satisfied flow ids
		self.controlled_bs, self.controlled_bs_paths = set(), {}  # base stations (bs, normal nodes) controlled by this controller
		self.controlled_clcs, self.controlled_clc_paths = set(), {}  # clcs controlled by this controller
		self.clcs = set()  # this node controlled by these CLCs
		self.crc = None  # this node is controlled by thisCRC
		self.max_allowed_proc = INF

	def __str__(self):
		return "id: {}, cbs: {}, clcs: {}".format(self.node_id, self.controlled_bs, self.clcs)

	def restore_backup(self, backup):
		self.proc = backup.proc
		self.satisfies = backup.satisfies.copy()
		self.controlled_bs = backup.controlled_bs.copy()
		self.controlled_bs_paths = backup.controlled_bs_paths.copy()
		self.controlled_clcs = backup.controlled_clcs.copy()
		self.controlled_clc_paths = backup.controlled_clc_paths.copy()
		self.clcs = backup.clcs.copy()
		self.crc = backup.crc
		self.max_allowed_proc = backup.max_allowed_proc

	@property
	def is_clc(self):
		return not empty(self.controlled_bs)

	@property
	def is_crc(self):
		return not empty(self.controlled_clcs)

	@property
	def is_controller(self):
		return self.is_clc or self.is_crc

	@property
	def is_controlled(self):
		return len(self.clcs) > 0

	@property
	def is_supervised(self):
		'is CRC-controlled'
		return self.crc is not None

	def get_clc_load(self, cn):
		max_load = -INF
		for bs in self.controlled_bs:
			rtt = 2. * latency_of_path(cn.G, self.controlled_bs_paths[bs]) + (
				self.proc * cn.G.graph["p_CLC"] / cn.G.node[self.node_id]["p_node"])
			max_load = max(max_load, rtt / cn.G.graph["l_CLC"])
		for flow_id in self.satisfies:
			flow = cn.flows[flow_id]
			for flow_node in flow.nodes:
				rtt = 2. * latency_of_path(cn.G, self.controlled_bs_paths[flow_node]) + (
					self.proc * flow.p_flow / cn.G.node[self.node_id]["p_node"])
				max_load = max(max_load, rtt / flow.l_flow)
		assert max_load > -INF
		return max_load

	def add_parent_clc_without_redundancy(self, new_clc, cn_extra):
		'assumes max. one redundant control per BS'
		if len(self.clcs) >= 1:
			for clc_id in self.clcs:
				clc = cn_extra.nodes[clc_id]
				assert self.node_id in clc.controlled_bs
				if not any(self.node_id in cn_extra.cn.flows[it].nodes for it in clc.satisfies):
					clc.undo_bs_control(self, cn_extra)
					break
		self.clcs.add(new_clc)

	def update_max_allowed_proc(self, new_allowed_proc):
		self.max_allowed_proc = min(self.max_allowed_proc, new_allowed_proc)

	def add_bs_path(self, path_to_bs):
		bs = path_to_bs[-1]
		self.proc += 1
		self.controlled_bs.add(bs)
		self.controlled_bs_paths[bs] = path_to_bs
		assert self.is_clc

	def add_clc_path(self, path_to_clc):
		clc = path_to_clc[-1]
		self.proc += 1
		self.controlled_clcs.add(clc)
		self.controlled_clc_paths[clc] = path_to_clc
		assert self.is_crc

	# def __setattr__(self, k, v):
	# 	if k in ['max_allowed_Proc'] and k < INF:
	# 		pass
	# 	super(NodeInfo, self).__setattr__(k, v)

	def undo_bs_control(self, controlled_bs, cn_extra):
		assert controlled_bs.node_id in self.controlled_bs
		controlled_bs.clcs.remove(self.node_id)
		self.controlled_bs.remove(controlled_bs.node_id)
		for a, b in edges_of_path(self.controlled_bs_paths[controlled_bs.node_id]):
			edge = cn_extra.edges[a, b]
			edge.b_rem += cn_extra.cn.G.graph["b_CLC"]
		del self.controlled_bs_paths[controlled_bs.node_id]
		self.proc -= 1

	def undo_clc_control(self, controlled_clc, cn_extra):
		assert controlled_clc.node_id in self.controlled_clcs
		controlled_clc.crc = None
		self.controlled_clcs.remove(controlled_clc.node_id)
		for a, b in edges_of_path(self.controlled_clc_paths[controlled_clc.node_id]):
			edge = cn_extra.edges[a, b]
			edge.b_rem += cn_extra.cn.G.graph["b_CRC"]
		del self.controlled_clc_paths[controlled_clc.node_id]
		self.proc -= 1


class EdgeInfo(object):
	def __init__(self, node1_id, node2_id, b_rem):
		self.edge_id = utilf.sort_pair((node1_id, node2_id))
		self.b_rem = b_rem

	def restore_backup(self, backup):
		self.b_rem = backup.b_rem

	def __setattr__(self, k, v):
		super(EdgeInfo, self).__setattr__(k, v)


class FlowInfo(object):
	def __init__(self, flow_id):
		self.flow_id = flow_id
		self.controller = None

	@property
	def is_satisfied(self):
		return self.controller is not None

	def restore_backup(self, backup):
		self.controller = backup.controller


class CppNetworkExtraInfo(object):
	"""
	additional, dynamic info for graph attributes like Proc for nodes
	edges keys have to be ordered (smaller, larger)
	"""

	def __init__(self, cn=None):
		self.cn = cn
		self.nodes = {}
		self.edges = {}
		self.flows = {}
		if cn is not None:
			for node_id in self.cn.G.nodes_iter():
				self.nodes[node_id] = NodeInfo(node_id)
			for node1_id, node2_id, edata in self.cn.G.edges_iter(data=True):
				node1_id, node2_id = utilf.sort_pair((node1_id, node2_id))
				self.edges[node1_id, node2_id] = EdgeInfo(node1_id, node2_id, edata["b_cap"])
			for flow_id in self.cn.flows:
				self.flows[flow_id] = FlowInfo(flow_id)

	def copy(self):
		the_copy = CppNetworkExtraInfo()
		the_copy.G = self.cn.G
		the_copy.nodes = copy.deepcopy(self.nodes)
		the_copy.edges = copy.deepcopy(self.edges)
		the_copy.flows = copy.deepcopy(self.flows)
		return the_copy

	def restore_backup(self, backup):
		for k, v in backup.nodes.iteritems():
			self.nodes[k].restore_backup(v)
		for k, v in backup.edges.iteritems():
			self.edges[k].restore_backup(v)
		for k, v in backup.flows.iteritems():
			self.flows[k].restore_backup(v)

	@property
	def num_unsatisfied_flows(self):
		return sum(1 for flow in self.flows.itervalues() if not flow.is_satisfied)

	@property
	def num_controllers(self):
		return sum(1 for node in self.nodes.itervalues() if node.is_controller)

	@property
	def num_uncontrolled_nodes(self):
		return sum(1 for node in self.nodes.itervalues() if not node.is_controlled)

	@property
	def num_unsupervised_clcs(self):
		return sum(1 for node in self.nodes.itervalues() if node.is_clc and not node.is_supervised)

	@property
	def num_clcs(self):
		return sum(1 for node in self.nodes.itervalues() if node.is_clc)

	@property
	def num_crcs(self):
		return sum(1 for node in self.nodes.itervalues() if node.is_crc)

	def copy_ilp_solution(self, ilp_instance):
		def get_value(attr_name, key, to_bool=True):
			attr = getattr(ilp_instance, attr_name)
			value = attr._data[key].value
			if value is None:
				value = 0.0
			if to_bool:
				return value > .5
			return value

		def prinf_f_links():
			for u, v, a, b in sorted((u, v, a, b) for (u, v, (a, b)) in
									 utilf.cross_product3(self.cn.C, self.cn.V, list(self.cn.G.edges_iter()))):
				if get_value("f", (u, v, a, b)):
					print((u, v, a, b))
				elif get_value("f", (u, v, b, a)):
					print((u, v, b, a))

		# prinf_f_links()

		def build_path(attr_name, source, target):
			edges = utilf.sort_and_remove_duplicates([sorted([a, b]) for (a, b) in self.cn.G.edges_iter() if
													  get_value(attr_name, (source, target, a, b)) or
													  get_value(attr_name, (source, target, b, a))])
			edge_dic = dict()

			def extend(k, v):
				if edge_dic.has_key(k):
					edge_dic[k].append(v)
				else:
					edge_dic[k] = [v]

			for a, b in edges:
				extend(a, b)
				extend(b, a)
			path = [source]
			while path[-1] != target:
				result = edge_dic[path[-1]]
				if len(result) > 1:
					if len(path) < 2:
						print([source, target])
						print(edges)
						print(edge_dic)
						assert False, "path is not correct"
					result = list(set(result) - {path[-2]})
				path.append(result[0])
			return path

		for node_id in self.cn.G.nodes_iter():
			node = self.nodes[node_id]
			node.clcs = set(c for c in self.cn.C if get_value("CLC", (c, node_id)))
			node.paths_to_clcs = {}
			for clc in node.clcs:
				node.paths_to_clcs[clc] = list(reversed(build_path("f", clc, node_id)))
			if node_id in self.cn.C:
				node.proc = int(get_value("Proc", node_id, to_bool=False) + .005)
				node.satisfies = set(flow_id for flow_id in self.flows if get_value("Sat", (node_id, flow_id)))
				crcs = list(c for c in self.cn.C if get_value("CRC", (c, node_id)))
				assert len(crcs) <= 1
				node.crc, node.path_to_crc = None, None
				if len(crcs) == 1:
					node.crc = crcs[0]
					node.path_to_crc = list(reversed(build_path("g", node.crc, node_id)))

				node.controlled_bs = set(bs_id for bs_id in self.cn.V if get_value("CLC", (node_id, bs_id)))
				for bs in node.controlled_bs:
					node.controlled_bs_paths[bs] = build_path("f", node_id, bs)
				node.controlled_clcs = set(clc_id for clc_id in self.cn.C if get_value("CRC", (node_id, clc_id)))
				for clc in node.controlled_clcs:
					node.controlled_clc_paths[clc] = build_path("g", node_id, clc)

		for flow_id, flow in self.flows.iteritems():
			flow.controller = None
			for c in self.cn.C:
				if get_value("Sat", (c, flow_id)):
					flow.controller = c

	def recompute_true_b_rems(self):
		true_rems = self.cn.compute_true_b_rems()
		for (a, b), true_rem in true_rems.iteritems():
			self.get_edge(a, b).b_rem = true_rem

	def copy_fcpg_solution(self, greedy_cn):
		for node_id, ndata in greedy_cn.G.nodes_iter(data=True):
			node = self.nodes[node_id]
			node.clcs, node.paths_to_clcs = set(ndata["CLCs"]), dict(ndata["pathtoCLC"])
			if node_id in greedy_cn.C:
				node.proc = ndata["Proc"]
				node.satisfies = set(ndata["Satisfies"])
				node.crc = ndata["CRC"]
				node.path_to_crc = None if ndata["pathtoCRC"] is None else list(ndata["pathtoCRC"])
				node.controlled_bs, node.controlled_bs_paths = set(ndata["CLCcontrol"]), dict(ndata["CLCpaths"])
				node.controlled_clcs, node.controlled_clc_paths = set(ndata["CRCcontrol"]), dict(ndata["CRCpaths"])
		for a, b, edata in greedy_cn.G.edges_iter(data=True):
			self.get_edge(a, b).b_rem = edata["b_rem"]
		for flow_id, fdic in greedy_cn.fdata.iteritems():
			self.flows[flow_id].controller = fdic["CLC"]

	def get_edge(self, node1_id, node2_id):
		if node1_id < node2_id:
			return self.edges[node1_id, node2_id]
		return self.edges[node2_id, node1_id]

	def cleanup_redundant_controls(self):
		vlist = list(self.cn.V)
		random.shuffle(vlist)
		for v in vlist:
			parent_clcs = list(self.nodes[v].clcs)
			random.shuffle(parent_clcs)
			for clc in parent_clcs:
				if len(self.nodes[v].clcs) > 1 and len(self.nodes[clc].satisfies & set(self.cn.Wf[v])) == 0:
					self.nodes[clc].undo_bs_control(self.nodes[v], self)

	def _get_flow_satisfaction_datarate(self, clc, flow_node, b_flow):
		if flow_node in clc.controlled_bs:
			return b_flow
		return b_flow + self.cn.G.graph["b_CLC"]

	def flow_satisfaction_paths_datarate_okay(self, clc_id, flow, satisfaction_paths):
		"returns true if data rate constraints are okay"
		if len(satisfaction_paths) == 1:
			return self.is_additional_datarate_okay_for_path(path=satisfaction_paths[0],
															 required_datarate=self._get_flow_satisfaction_datarate(
																 self.nodes[clc_id], tuple(flow.nodes)[0], flow.b_flow))
		additional_datarates_for_edge = Counter()
		for path in satisfaction_paths:
			for a, b in utilf.edges_of_path(path):
				additional_datarates_for_edge[a, b] += self._get_flow_satisfaction_datarate(self.nodes[clc_id],
																							path[-1], flow.b_flow)
		for (a, b), datarate in additional_datarates_for_edge.iteritems():
			if datarate > self.edges[a, b].b_rem:
				return False
		return True

	def is_additional_datarate_okay_for_path(self, path, required_datarate):
		for a, b in utilf.edges_of_path(path):
			if self.edges[a, b].b_rem < required_datarate:
				return False
		return True

	def compute_max_allowed_proc(self, controller, path, required_processing_capacity, latency_limit):
		result = self.cn.G.node[controller]["p_node"] / required_processing_capacity * (
			latency_limit - 2. * utilf.latency_of_path(self.cn.G, path))
		assert result >= .0
		return result

	def get_path_latency_limit_of_node_for_new_proc(self, node_id, use_as_clc, flow_to_satisfy=None):
		"""automatically uses the correct Proc number depending on weather or not clc/crc is already activated
		returns -1, if node cannot handle further procs
		"""
		ninfo = self.nodes[node_id]
		gnode = self.cn.G.node[node_id]
		if not use_as_clc:  # use as crc
			num_proc = ninfo.proc + (2 if not ninfo.is_crc else 1)
			if num_proc > ninfo.max_allowed_proc:
				return -1.
			return .5 * (self.cn.G.graph["l_CRC"] - num_proc * self.cn.G.graph["p_CRC"] / gnode["p_node"])
		num_proc = ninfo.proc + (2 if not ninfo.is_clc else 1)
		if flow_to_satisfy is not None:  # use as clc satisfying flow
			for flow_node in flow_to_satisfy.nodes:
				if flow_node not in ninfo.controlled_bs:
					num_proc += 1
			if num_proc > ninfo.max_allowed_proc:
				return -1.
			return min(.5 * (self.cn.G.graph["l_CLC"] - num_proc * self.cn.G.graph["p_CLC"] / gnode["p_node"]),
					   .5 * (flow_to_satisfy.l_flow - num_proc * flow_to_satisfy.p_flow / gnode["p_node"]))
		if use_as_clc:  # use as clc controlling node
			if num_proc > ninfo.max_allowed_proc:
				return -1.
			return .5 * (self.cn.G.graph["l_CLC"] - num_proc * self.cn.G.graph["p_CLC"] / gnode["p_node"])

	def _reduce_datarate_on_path(self, path, additional_datarate):
		for a, b in utilf.edges_of_path(path):
			self.edges[a, b].b_rem -= additional_datarate
			assert self.edges[a, b].b_rem >= 0.0

	def add_clc_control(self, path_from_clc_to_node):
		clc, node = path_from_clc_to_node[0], path_from_clc_to_node[-1]
		clc_info = self.nodes[clc]
		assert node not in clc_info.controlled_bs, "node {} was already controlled by the CLC {}".format(node, clc)
		self._reduce_datarate_on_path(path_from_clc_to_node, self.cn.G.graph["b_CLC"])
		clc_info.add_bs_path(path_from_clc_to_node)
		self.nodes[node].add_parent_clc_without_redundancy(clc, self)
		clc_info.update_max_allowed_proc(self.compute_max_allowed_proc(
			clc, path_from_clc_to_node, self.cn.G.graph["p_CLC"], self.cn.G.graph["l_CLC"]))

	def add_crc_control(self, path_from_crc_to_clc):
		crc, clc = path_from_crc_to_clc[0], path_from_crc_to_clc[-1]
		crc_info, clc_info = self.nodes[crc], self.nodes[clc]
		self._reduce_datarate_on_path(path_from_crc_to_clc, self.cn.G.graph["b_CRC"])
		crc_info.add_clc_path(path_from_crc_to_clc)
		crc_info.update_max_allowed_proc(self.compute_max_allowed_proc(
			crc, path_from_crc_to_clc, self.cn.G.graph["p_CRC"], self.cn.G.graph["l_CRC"]))
		clc_info.crc = crc

	def add_flow_satisfaction(self, clc, flow_id, used_paths_from_clc_to_flow_nodes=None):
		"""will add clc_control when necessary. assumes all constraints can be fulfilled
		if paths is None, then we assume control paths already exist"""
		flow, clc_info = self.cn.flows[flow_id], self.nodes[clc]
		if used_paths_from_clc_to_flow_nodes is None:
			used_paths_from_clc_to_flow_nodes = [
				clc_info.controlled_bs_paths[it] for it in flow.nodes
				]
		assert len(used_paths_from_clc_to_flow_nodes) == len(flow.nodes)

		for path in used_paths_from_clc_to_flow_nodes:
			path_end_node = path[-1]
			assert path[0] == clc and path_end_node in flow.nodes
			if path_end_node not in clc_info.controlled_bs:
				self.add_clc_control(path)
			for a, b in utilf.edges_of_path(path):
				self.edges[a, b].b_rem -= flow.b_flow
				assert self.edges[a, b].b_rem >= 0.0
		self.flows[flow.flow_id].controller = clc
		clc_info.proc += 1
		clc_info.satisfies.add(flow.flow_id)
		clc_info.update_max_allowed_proc(self.compute_max_allowed_proc(
			clc,
			max((it for it in used_paths_from_clc_to_flow_nodes), key=lambda it: utilf.latency_of_path(self.cn.G, it)),
			flow.p_flow, flow.l_flow))

	def check_crc(self, path):
		"""checks if a certain CRC control can be established"""
		crc = path[0]
		return all([
			self.is_additional_datarate_okay_for_path(path, self.cn.G.graph["b_CRC"]),
			utilf.latency_of_path(self.cn.G, path) <= self.get_path_latency_limit_of_node_for_new_proc(crc,
																									   use_as_clc=False)
		])

	def check_clc(self, path):
		"""checks if a certain CLC control can be established"""
		clc = path[0]
		return all([
			self.is_additional_datarate_okay_for_path(path, self.cn.G.graph["b_CLC"]),
			latency_of_path(self.cn.G, path) <= self.get_path_latency_limit_of_node_for_new_proc(clc, use_as_clc=True)
		])

	def check_flow_satisfaction(self, clc_id, flow_id):
		"""checks if clc can satisfy flow on existing control paths"""
		clc, flow = self.nodes[clc_id], self.cn.flows[flow_id]
		if self.flows[flow_id].is_satisfied:
			return False
		if not flow.nodes <= clc.controlled_bs:
			return False
		satisfaction_paths = []
		latency_limit = self.get_path_latency_limit_of_node_for_new_proc(clc_id, use_as_clc=True, flow_to_satisfy=flow)
		for flow_node in flow.nodes:
			path = clc.controlled_bs_paths[flow_node]
			satisfaction_paths.append(path)
			if latency_of_path(self.cn.G, path) > latency_limit:
				return False
		return self.flow_satisfaction_paths_datarate_okay(clc_id, flow, satisfaction_paths)

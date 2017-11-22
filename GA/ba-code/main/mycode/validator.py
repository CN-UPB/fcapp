from __future__ import (absolute_import, division, print_function)
import traceback
import sys

from . import utilf
from .constants import *


def _check_control_redundancy(cn):
	"checks that there are no useless controls"
	nodes_dic, nodes = cn.extra_info.nodes, cn.extra_info.nodes.values()
	for bs in nodes:
		if len(bs.clcs) >= 2:
			# all controls should be via satisfaction
			for clc_id in bs.clcs:
				clc = nodes_dic[clc_id]
				T.assertIn(bs.node_id, clc.controlled_bs)
				T.assertTrue(any(bs.node_id in cn.flows[it].nodes for it in clc.satisfies),
							 "CLC {} redundantly controls BS {} (not needed for control "
							 "structure or flow satisfaction)".format(clc_id, bs.node_id))


def validate_cpp_network(cn, check_redundancy=True):
	try:
		if "validator" in VERBOSE:
			print(utilf.h1("VALIDATION"))
		_check_controller_status(cn)
		_check_path_integrity(cn)
		_check_flow_satisfaction(cn)
		_check_datarate(cn)
		_check_latency(cn)
		if check_redundancy:
			_check_control_redundancy(cn)

	except AssertionError, err:
		traceback.print_exc(err)
		print(utilf.h2("NOT A VALID SOLUTION"), file=sys.stderr)
		raise err
	# raise err


def check_latency(cn):
	try:
		_check_latency(cn)
	except AssertionError, err:
		traceback.print_exc(err)
		raise err


def _check_latency(cn):
	nodes_dic, nodes = cn.extra_info.nodes, cn.extra_info.nodes.values()
	for node in nodes:
		T.assertEqual(node.proc, sum(len(it) for it in [node.controlled_bs, node.controlled_clcs, node.satisfies]))

	def p_latency(controller_id, p_demand):
		return p_demand * nodes_dic[controller_id].proc / cn.G.node[controller_id]["p_node"]

	for controller in cn.C:
		max_allowed_proc = INF
		for clc, clc_path in nodes_dic[controller].controlled_clc_paths.iteritems():
			max_allowed_proc = min(max_allowed_proc, cn.extra_info.compute_max_allowed_proc(
				controller, clc_path, cn.G.graph["p_CRC"], cn.G.graph["l_CRC"]))
		for bs, bs_path in nodes_dic[controller].controlled_bs_paths.iteritems():
			max_allowed_proc = min(max_allowed_proc, cn.extra_info.compute_max_allowed_proc(
				controller, bs_path, cn.G.graph["p_CLC"], cn.G.graph["l_CLC"]))
			for flow in cn.flows.itervalues():
				if flow.flow_id in nodes_dic[controller].satisfies and bs in flow.nodes:
					max_allowed_proc = min(max_allowed_proc, cn.extra_info.compute_max_allowed_proc(
						controller, bs_path, flow.p_flow, flow.l_flow))

		T.assertLessEqual(nodes_dic[controller].proc, max_allowed_proc)

	for crc in cn.crcs:
		for clc_path in nodes_dic[crc].controlled_clc_paths.itervalues():
			T.assertLessEqual(2.0 * utilf.latency_of_path(cn.G, clc_path) + p_latency(crc, cn.G.graph["p_CRC"]),
							  cn.G.graph["l_CRC"])
	for clc in cn.clcs:
		for bs, bs_path in nodes_dic[clc].controlled_bs_paths.iteritems():
			double_path_latency = 2.0 * utilf.latency_of_path(cn.G, bs_path)
			T.assertLessEqual(double_path_latency + p_latency(clc, cn.G.graph["p_CLC"]), cn.G.graph["l_CLC"])
			for flow in cn.flows.itervalues():
				if flow.flow_id in nodes_dic[clc].satisfies and bs in flow.nodes:
					T.assertLessEqual(double_path_latency + p_latency(clc, flow.p_flow), flow.l_flow)


def _check_datarate(cn):
	true_rems = cn.compute_true_b_rems()
	for edge, true_rem in true_rems.iteritems():
		T.assertGreaterEqual(true_rem, 0.0)
		T.assertAlmostEqual(true_rem, cn.extra_info.edges[edge].b_rem, places=ALMOST_EQUAL_PLACES)


def _check_flow_satisfaction(cn):
	nodes_dic, nodes = cn.extra_info.nodes, cn.extra_info.nodes.values()
	satisfied_flows = set()
	for clc in cn.clcs:
		for flow_id in nodes_dic[clc].satisfies:
			T.assertFalse(flow_id in satisfied_flows)
			satisfied_flows.add(flow_id)
			flow_nodes = set(cn.flows[flow_id].nodes)
			T.assertTrue(flow_nodes <= nodes_dic[clc].controlled_bs)
	unsatisfied_flows = cn.F - satisfied_flows
	if "validator" in VERBOSE:
		print("#unsatisfied flows: {}".format(len(unsatisfied_flows)))


def _check_path_integrity(cn):
	nodes_dic, nodes = cn.extra_info.nodes, cn.extra_info.nodes.values()
	for node in nodes:
		for the_set, the_paths in [(node.controlled_bs, node.controlled_bs_paths),
								   (node.controlled_clcs, node.controlled_clc_paths)]:
			T.assertEqual(the_set, set(the_paths.keys()))
			for key, the_path in the_paths.iteritems():
				T.assertEqual(the_path[0], node.node_id)
				T.assertEqual(the_path[-1], key)
				for a, b in utilf.edges_of_path(the_path):
					T.assertTrue(cn.G.has_edge(a, b))


def _check_controller_status(cn):
	nodes_dic, nodes = cn.extra_info.nodes, cn.extra_info.nodes.values()
	T.assertSetEqual(set(cn.clcs), set(node.node_id for node in nodes if node.is_clc))
	T.assertSetEqual(set(cn.crcs), set(node.node_id for node in nodes if node.is_crc))
	controlled_nodes = set(utilf.flatten_list([node.controlled_bs for node in nodes]))
	uncontrolled_nodes = cn.V - controlled_nodes
	if "validator" in VERBOSE:
		print("uncontrolled nodes: {}".format(uncontrolled_nodes))
	T.assertEqual(len(uncontrolled_nodes), 0)
	for clc in cn.clcs:
		T.assertEqual([node.node_id for node in nodes if clc in node.controlled_clcs], [nodes_dic[clc].crc])
	# for nonclc in cn.V - set(cn.clcs):
	# 	T.assertIsNone(nodes_dic[nonclc].crc)
	# todo fix repra for that

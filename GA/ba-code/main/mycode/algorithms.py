import networkx as nx

from mycode import settings
from mycode.settings import config

from mycode.utilc import DynamicPriorityQueue


def _compute_path(parent_dict, current_node):
	path = []
	while True:
		assert len(path) < 100
		if current_node == None:
			break
		path.append(current_node)
		current_node = parent_dict[current_node]
	return list(reversed(path))


def dijkstra(G, Gextra, source, target_set, required_datarate, max_path_latency):
	"""
	:returns a successful path from source to a target from target_set with lowest path length
	"""
	q = DynamicPriorityQueue()
	q.put((source, 0.0), priority=0.0)
	marked = set()
	parents = {source: None}
	while not q.empty():
		path_length, (current_node, current_path_latency) = q.pop()
		marked.add(current_node)

		if current_node in target_set:
			return _compute_path(parents, current_node)
		for neighbor in G.neighbors_iter(current_node):
			if neighbor not in marked:
				edata = G.edge[current_node][neighbor]
				new_path_latency = current_path_latency + edata["l_cap"]
				if (required_datarate <= Gextra.get_edge(current_node, neighbor).b_rem and
							new_path_latency <= max_path_latency):
					new_path_length = path_length + 1
					if not config.USE_HOP_PATH_LENGTH:
						new_path_length = new_path_latency
					if q.put_or_decrease((neighbor, new_path_latency), other_priority=new_path_length):
						parents[neighbor] = current_node
	return None


def dijkstra_multi_source(G, Gextra, source_set, target, use_source_as_clc):
	"""
	:returns a valid path from source of the source_set to the target with lowest path length
	"""
	if len(source_set) == 0:
		return None
	required_datarate = G.graph["b_CRC"]
	if use_source_as_clc:
		required_datarate = G.graph["b_CLC"]
	path_latency_upper_bound = max(Gextra.get_path_latency_limit_of_node_for_new_proc(it, use_as_clc=use_source_as_clc)
								   for it in source_set)
	q = DynamicPriorityQueue()
	q.put((target, 0.0), priority=0.0)
	marked = set()
	parents = {target: None}
	while not q.empty():
		path_length, (current_node, current_path_latency) = q.pop()
		marked.add(current_node)

		if (current_node in source_set and current_path_latency <=
			Gextra.get_path_latency_limit_of_node_for_new_proc(current_node, use_as_clc=use_source_as_clc)):
			return list(reversed(_compute_path(parents, current_node)))
		for neighbor in G.neighbors_iter(current_node):
			if neighbor not in marked:
				edata = G.edge[current_node][neighbor]
				new_path_latency = current_path_latency + edata["l_cap"]
				if (required_datarate <= Gextra.get_edge(current_node, neighbor).b_rem and
							new_path_latency <= path_latency_upper_bound):
					new_path_length = path_length + 1
					if not config.USE_HOP_PATH_LENGTH:
						new_path_length = new_path_latency
					if q.put_or_decrease((neighbor, new_path_latency), other_priority=new_path_length):
						parents[neighbor] = current_node
	return None


def flow_dijkstra(G, Gextra, flow, source_clcs):
	"""
	returns clc, [shortest satisfaction paths], max_path_length of flow nodes
	only uses shortest paths to clcs. if these do not work data rate wise, they are discarded,
	instead of searching for longer ones.
	ASSUMES THAT EXISTING CLC/BS CONTROL PATHS ARE MINIMAL PATH LENGTH WISE
	"""
	source_clcs_set = set(source_clcs)
	q = DynamicPriorityQueue()  # (source flow_node, current path node, max path latency)
	marked = {}
	parents = {}
	for flow_node in flow.nodes:
		q.put((flow_node, flow_node, 0.0), priority=0.0)
		marked[flow_node] = {flow_node}
		parents[flow_node] = {flow_node: None}
	while not q.empty():
		path_length, (root, current_node, latency) = q.pop()

		if current_node in source_clcs_set:
			if all(current_node in marked_set for marked_set in marked.itervalues()):
				satisfaction_paths = [list(reversed(_compute_path(parents[flow_node], current_node))) for flow_node
									  in flow.nodes
									  if flow_node not in Gextra.nodes[current_node].controlled_bs]
				for flow_node in flow.nodes & Gextra.nodes[current_node].controlled_bs:
					satisfaction_paths.append(Gextra.nodes[current_node].controlled_bs_paths[flow_node])
				if (latency <= Gextra.get_path_latency_limit_of_node_for_new_proc(current_node, use_as_clc=True,
																				  flow_to_satisfy=flow) and
						Gextra.flow_satisfaction_paths_datarate_okay(current_node, flow, satisfaction_paths)):
					return current_node, satisfaction_paths, path_length  # path_length by algo design maximal of all flow nodes
				else:
					source_clcs_set.remove(current_node)

		for neighbor in G.neighbors_iter(current_node):
			if neighbor not in marked[root]:
				if (flow.b_flow <= Gextra.get_edge(current_node, neighbor).b_rem):
					marked[root].add(neighbor)
					new_latency = latency + G.edge[current_node][neighbor]["l_cap"]
					new_path_length = path_length + 1
					if not config.USE_HOP_PATH_LENGTH:
						new_path_length = new_latency
					if q.put_or_decrease((root, neighbor, new_latency),
										 other_priority=new_path_length):
						parents[root][neighbor] = current_node
	return None, None, None


def llp(G, source, target):
	'lowest latency path'
	if config.USE_HOP_PATH_LENGTH:
		return nx.shortest_path(G, source=source, target=target)
	return nx.shortest_path(G, source=source, target=target, weight="l_cap")

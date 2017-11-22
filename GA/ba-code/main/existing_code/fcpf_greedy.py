from __future__ import division
from crowd_network import *
#pdb.set_trace()

class CPGreedy:

	def __init__(self, filename=None, flowOption="MostDemanding", modify_controllers=False, contrProb=None, cn=None):
		if filename is not None:

			self.cn = CrowdNetwork()
			valid_network = self.cn.generate_from_file(filename, modify_controllers, contrProb)
			if valid_network:
				self.state = "NOT SOLVED"
			else:
				self.state = "INVALID NETWORK"
				print("Error: Invalid network!")
				exit(1)
		else:
			if cn is None:
				print("Error: Nothing to create CPGreedy network from!")
				exit(1)
			else:
				self.cn = cn
				self.state = "NOT SOLVED"
			
		self.getFlowOption = flowOption
		self.Controlled = []
		self.CRCs = []
		self.CLCs = []
		self.Satisfied = []
		if len(self.cn.C) > 1:
			self.VCRatio = len(self.cn.V)/(len(self.cn.C)-1)
		else: 
			self.VCRatio = len(self.cn.V)
		self.banlist = []

	def cpgreedy(self):
		if self.state == "INVALID NETWORK":
			print("Error: Invalid network!")
			exit(1)
			
		if len(self.Controlled) < len(self.cn.V):
			self.state = "NOT SOLVED"
			
		self.globalOption = "neighbors"
		while len(self.Controlled) < len(self.cn.V):
			self.findCLC(self.globalOption)
			if len(self.CLCs) == len(self.cn.C):
				break
				
		if len(self.Controlled) == len(self.cn.V):
			self.state = "Solved"
		
		if len(self.CLCs) < len(self.cn.C):
			self.globalOption = "flows"		
			while len(self.Satisfied) < len(self.cn.F):
				tmpsat = len(self.Satisfied)
				self.findCLC(self.globalOption)
				if tmpsat == len(self.Satisfied):
					self.newCLCcontrols -= len(self.cn.G.node[self.CLCs[-1]]['CLCcontrol'])
					self.banlist.append(self.CLCs[-1])
					self.remCLC(self.CLCs[-1])
				if len(self.CLCs) + len(self.banlist) == len(self.cn.C): 
					break		
		self.cleanupCLCcontrols(self.cn.V)
		
	def findCLC(self,option):
		candidates = self.getCLCcandidates(option)
		for v in candidates:
			Gtmp = self.cn.G.copy()
			Gtmp = self.findCRC(Gtmp,v)
			if Gtmp is not None:
				self.cn.G = self.addNewCLC(Gtmp,v)
				break
			
	def getCLCcandidates(self,option=None):
		candidates = list(set(self.cn.C) - (set(self.CLCs) | set(self.banlist)))
		# avoid CRCs to be used as CLCs as long as possible
		if len(set(candidates) - set(self.CRCs)) > 0:
			candidates = [c for c in candidates if not c in self.CRCs]
		remaining_nodes = set(self.cn.V) - set(self.Controlled)
		remaining_flows = set(self.cn.F) - set(self.Satisfied)
		
		if option == "neighbors": # emphasis on controlling nodes
			ctmp = [(k,len((set([k]) | set(self.cn.G.neighbors(k))) - set(self.Controlled))) for k in candidates]
			ctmp.sort(key=lambda x: x[1], reverse=True)
			bestvalue = ctmp[0][1] 
			if bestvalue > 0:
				candidates = [x[0] for x in ctmp]
			else:
				self.globalOption = "isolated_nodes"
				candidates = self.getCLCcandidates("isolated_nodes")
		elif option == "isolated_nodes":
			paths = []
			for i in remaining_nodes:
				for j in candidates:
					paths.append(nx.shortest_path(self.cn.G, source=j, target=i))
			paths.sort(key=len)
			candidates = []
			for p in paths:
				if not p[0] in candidates:
					candidates.append(p[0])
		elif option == "flows": # emphasis on data flow satisfaction
			ctmp = [(k,len(set(self.cn.Wf[k]) - set(self.Satisfied))) for k in candidates]
			ctmp.sort(key=lambda x: x[1], reverse=True)
			bestvalue = ctmp[0][1]
			if bestvalue > 0:
				candidates = [x[0] for x in ctmp]
			else:
				self.globalOption = "isolated_flows"
				candidates = self.getCLCcandidates("isolated_flows")
		elif option == "isolated_flows":
			paths = []
			for f in remaining_flows:
				for i in self.cn.Wb[f]:
					for j in candidates:
						paths.append(nx.shortest_path(self.cn.G, source=j, target=i))
			paths.sort(key=len)
			candidates = []
			for p in paths:
				if not p[0] in candidates:
					candidates.append(p[0])
			
		return candidates
			
	def addNewCLC(self,G,v):
		paths = []
		pf = set([]) #potential flows
		nc = 0
		nnc = 0 #new nodes controlled
		fs = 0 #flows satisfied
		
		tmp = self.checkCLC(G,[v])
		if tmp == True: #add self-conrtrol
			nc += 1
			if v not in self.Controlled:
				nnc +=1
			G = self.addCLCcontrol(G,[v])
			pf = self.updatePotentialFlows(pf,G,v,[v])
		else: #no self-control possible
			self.cn.C.remove(v)
			return G
			
		for i in self.cn.V:
			if i != v and (i not in self.Controlled or len(set(self.cn.Wf[i]) - set(self.Satisfied)) > 0):
				paths.append((nx.shortest_path(G, source=v, target=i), i in self.Controlled, len(set(self.cn.Wf[i]) - set(self.Satisfied))))
		if len(self.Controlled) < len(self.cn.V):
			paths.sort(key=lambda x: x[1])
			paths.sort(key=lambda x: len(x[0]))
			notyetsolved = True
		else:
			paths.sort(key=lambda x: len(x[0]))
			paths.sort(key=lambda x: x[2], reverse=True)
			notyetsolved = False
			
		while (len(paths) > 0 or len(pf) > 0) and (len(self.Controlled) < len(self.cn.V) or len(self.Satisfied) < len(self.cn.F)):			
			if notyetsolved and len(self.Controlled) == len(self.cn.V):  #resort once all nodes are controlled
				paths.sort(key=lambda x: len(x[0]))
				paths.sort(key=lambda x: x[2], reverse=True)
				notyetsolved = False
			if len(pf) > 0 and (nnc >= self.VCRatio or len(self.Controlled) == len(self.cn.V)):
				f = self.getFlow(pf, self.getFlowOption)
				tmp = self.checkFlowSat(G,v,f)
				if tmp == True:
					G = self.addFlowSat(G,v,f)
					fs += 1
				pf.remove(f)
			elif len(paths) > 0:
				p = list(paths[0][0])
				del paths[0]
				tmp = self.checkCLC(G,p)
				if tmp == True:
					nc += 1
					if p[-1] not in self.Controlled:
						nnc +=1
					G = self.addCLCcontrol(G,p)
					pf = self.updatePotentialFlows(pf,G,v,[p[-1]])
				elif tmp > 2:  # invalid because of latency -> no later paths will be valid -> stop;
					break
			else:
				break
				
		return G
		
	def updatePotentialFlows(self,pf,G,v,nn):
		cpf = set([])
		for w in nn:
			cpf = cpf | set(self.cn.Wf[w])
		for f in cpf:
			if self.cn.fdata[f]['isSat'] == False and set(self.cn.Wb[f]) <= set(G.node[v]['CLCcontrol']):
				pf.add(f)
			
		return pf
		
	def getFlow(self, pf, option):
		tmp = list(pf)
		if len(tmp) == 0:
			return None
		else:
			if option == "MostDemanding":
				tmp.sort(key=lambda f: self.cn.fdata[f]['p_flow'], reverse=True)
			elif option == "LeastDemanding":
				tmp.sort(key=lambda f: self.cn.fdata[f]['p_flow'])
			return tmp[0]	
	
	def findCRC(self, G, v):
		# check already active CRCs first
		paths = []
		for i in self.CRCs: 
			paths.append(nx.shortest_path(G, source=i, target=v))
		paths.sort(key=len)
		for p in paths:
			if self.checkCRC(G,p):
				return self.addCRCcontrol(G,p)
		
		# need to add a new CRC, at first try to avoid active CLCs and CLC candidate
		return self.findNewCRC(G,v)
		
	def findNewCRC(self, G, v):	
		paths = []
		for i in list(set(self.cn.C) - (set(self.CRCs) | set(self.CLCs) | set([v]))):
			paths.append(nx.shortest_path(G, source=i, target=v))
		if len(self.CRCs) == 0:	# first CRC should be placed centrally
			paths.sort(key=lambda p: sum(len(nx.shortest_path(G, source=p[0], target=c)) for c in self.cn.C))
		else:	
			paths.sort(key=lambda p: len(p))
		for p in paths:
			if self.checkCRC(G,p):
				return self.addCRCcontrol(G,p)
		# last option: try CLC candidate, then already active CLCs
		if self.checkCRC(G,[v]):
			return self.addCRCcontrol(G,[v])
		paths = []
		for i in self.CLCs:
			paths.append(nx.shortest_path(G, source=i, target=v))
		paths.sort(key=len)
		for p in paths:
			if self.checkCRC(G,p):
				return self.addCRCcontrol(G,p)
						
		return None
		
	def addCRCcontrol(self,G,path):
		v = path[0]
		w = path[-1]
		for i in range(0,len(path)-1):
			G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.b_CRC
		G.node[v]['Proc'] += 1
		G.node[v]['CRCcontrol'].append(w)
		G.node[v]['CRCpaths'][w] = path
		G.node[v]['isCRC'] = True
		G.node[w]['CRC'] = v
		G.node[w]['pathtoCRC'] = path
		if v not in self.CRCs:
			self.CRCs.append(v)
		
		return G
			
	def addCLCcontrol(self,G,path):
		v = path[0]
		w = path[-1]
		for i in range(0,len(path)-1):
			G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.b_CLC
		G.node[v]['Proc'] += 1
		G.node[v]['CLCcontrol'].append(w)
		G.node[v]['CLCpaths'][w] = path
		G.node[v]['isCLC'] = True
		G.node[w]['CLCs'].append(v)
		G.node[w]['pathtoCLC'][v] = path
		if v not in self.CLCs:
			self.CLCs.append(v)
		if w not in self.Controlled:
			self.Controlled.append(w)
		
		return G
		
	def addFlowSat(self,G,v,f):
		self.cn.fdata[f]['isSat'] = True
		self.cn.fdata[f]['CLC'] = v
		for k in self.cn.Wb[f]:
			path = G.node[v]['CLCpaths'][k]
			for i in range(0,len(path)-1):
				G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.fdata[f]['b_flow']
		G.node[v]['Proc'] += 1
		G.node[v]['Satisfies'].append(f)
		self.Satisfied.append(f)
		
		return G
	
	# checks if a certain CRC control can be established	
	def checkCRC(self,G,path):
		v = path[0]
		for i in range(0,len(path)-1):
			if G.edge[path[i]][path[i+1]]['b_rem'] < self.cn.b_CRC:
				return False
		if sum(2*G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (G.node[v]['Proc']+1)*self.cn.p_CRC/G.node[v]['p_node'] > self.cn.l_CRC:
			return False
		if not self.verifyLatency(G,v):
			return False
		
		return True
	
	# checks if a certain CLC control can be established
	def checkCLC(self,G,path):
		v = path[0]
		for i in range(0,len(path)-1):
			if G.edge[path[i]][path[i+1]]['b_rem'] < self.cn.b_CLC:
				return 2
		if sum(2*G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (G.node[v]['Proc']+1)*self.cn.p_CLC/G.node[v]['p_node'] > self.cn.l_CLC:
			return 4
		if not self.verifyLatency(G,v):
			return 5
		
		return True
		
	# checks if a flow f can be satisfied by a controller v
	def checkFlowSat(self,G,v,f):
		if self.cn.fdata[f]['isSat'] == True:
			return False
		if not set(self.cn.Wb[f]) <= set(G.node[v]['CLCcontrol']):
			return False
		for k in self.cn.Wb[f]:
			path = G.node[v]['CLCpaths'][k]
			for i in range(0,len(path)-1):
				if G.edge[path[i]][path[i+1]]['b_rem'] < self.cn.fdata[f]['b_flow']:
					return False
			if sum(2*G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (G.node[v]['Proc']+1)*self.cn.fdata[f]['p_flow']/G.node[v]['p_node'] > self.cn.fdata[f]['l_flow']:
				return False
		if not self.verifyLatency(G,v):
			return False
		
		return True
	
	# checks if all latency constraints are (still) met
	def verifyLatency(self,G,v):
		for i in G.node[v]['CRCcontrol']:
			path = G.node[v]['CRCpaths'][i]
			if sum(2*G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (G.node[v]['Proc']+1)*self.cn.p_CRC/G.node[v]['p_node'] > self.cn.l_CRC:
				return False
		for i in G.node[v]['CLCcontrol']:
			path = G.node[v]['CLCpaths'][i]
			if sum(2*G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (G.node[v]['Proc']+1)*self.cn.p_CLC/G.node[v]['p_node'] > self.cn.l_CLC:
				return False
		for f in G.node[v]['Satisfies']:
			for i in self.cn.Wb[f]:
				path = G.node[v]['CLCpaths'][i]
				if sum(2*G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (G.node[v]['Proc']+1)*self.cn.fdata[f]['p_flow']/G.node[v]['p_node'] > self.cn.fdata[f]['l_flow']:
					return False
					
		return True	
		
	def cleanupCLCcontrols(self,nodelist):
		vtmp = list(nodelist)
		random.shuffle(vtmp)
		for v in vtmp:
			ctmp = list(self.cn.G.node[v]['CLCs'])
			random.shuffle(ctmp)
			for c in ctmp:
				if c != v and len(self.cn.G.node[v]['CLCs']) > 1 and len(set(self.cn.G.node[c]['Satisfies']) & set(self.cn.Wf[v])) == 0:
					self.remCLCcontrol(c,v)
					
	def remCLC(self,v):
		tmp = list(self.cn.G.node[v]['Satisfies'])
		for f in tmp:
			self.remFlowSat(f)
		tmp = list(self.cn.G.node[v]['CLCcontrol'])
		for w in tmp:
			self.remCLCcontrol(v,w)	
		self.cn.G.node[v]['isCLC'] = False
		if self.cn.G.node[v]['CRC'] is not None:
			self.remCRCcontrol(self.cn.G.node[v]['CRC'],v)
		self.CLCs.remove(v)
					
	def remCLCcontrol(self,v,w):
		path = self.cn.G.node[v]['CLCpaths'][w]
		for i in range(0,len(path)-1):
			self.cn.G.edge[path[i]][path[i+1]]['b_rem'] += self.cn.b_CLC
		self.cn.G.node[v]['Proc'] -= 1
		self.cn.G.node[v]['CLCcontrol'].remove(w)
		del self.cn.G.node[v]['CLCpaths'][w]
		self.cn.G.node[w]['CLCs'].remove(v)
		del self.cn.G.node[w]['pathtoCLC'][v]
		if len(self.cn.G.node[w]['CLCs']) == 0:
			self.Controlled.remove(w)
			self.state = "NOT SOLVED"
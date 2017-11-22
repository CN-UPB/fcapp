from __future__ import division
import networkx as nx
import sys, math, random, time, copy
from crowd_network import *
import pdb
#pdb.set_trace()

class CPFlex:

	def __init__(self, filename=None, flowOption="LeastDemanding", scenario=None, modify_controllers=False, contrProb=None, cn=None, inputversion="flex", evalscen="generic"):
		if filename is not None:
			self.cn = CrowdNetwork()
			valid_network = self.cn.generate_from_file(filename, modify_controllers, contrProb, evalscen)
			if valid_network:
				self.state = "NOT SOLVED"
			else:
				self.state = "INVALID NETWORK"
				print "Error: Invalid network!"
				exit(1)
		else:
			if cn is None:
				print "Error: Nothing to create CPFlex network from!"
				exit(1)
			else:
				self.cn = cn
				self.state = "NOT SOLVED"
			
		self.getFlowOption = flowOption
		self.iterations = 0
		self.Controlled = []
		self.CRCs = []
		self.CLCs = []
		self.Satisfied = []
		self.uncontrolledCLCs = []
		self.CLCloadlimit = 0.5
		self.remCLCswithlowload = False
		self.flexOperation = False
		if len(self.cn.C) > 1:
			self.VCRatio = len(self.cn.V)/(len(self.cn.C)-1)
		else: 
			self.VCRatio = len(self.cn.V)
		self.banlist = []
			
	def scratchCopy(self):
		cntmp = self.cn.copy()
		cntmp.cleanup()
		
		return CPFlex(filename=None,cn=cntmp)

	def cpgreedy(self):
		if self.state == "INVALID NETWORK":
			print "Error: Invalid network!"
			exit(1)
			
		self.iterations += 1
		self.newCLCcontrols = 0 # for simulation stats
		self.newFlowSats = 0
			
		if self.iterations > 1:	
			if self.remCLCswithlowload == True:
				tmp = list(self.CLCs)
				for c in tmp:
					if self.CLCload(c) < self.CLCloadlimit:
						self.remCLC(c)
			while len(self.uncontrolledCLCs) > 0:
				v = self.uncontrolledCLCs[0]
				tmp = self.findCRC(v)
				if tmp == False:
					self.remCLC(v)
				self.uncontrolledCLCs.remove(v)
			self.updateVCRatio()
			self.browseCurrentCLCs()
			
		if len(self.Controlled) < len(self.cn.V):
			self.state = "NOT SOLVED"
			
		self.globalOption = "neighbors"
		while len(self.Controlled) < len(self.cn.V):
			if len(self.CLCs) == len(self.cn.C):
				if self.iterations > 1 and self.flexOperation == True: 
					self.browseCurrentCLCs()
				self.forceControl()
				break
			self.findCLC(self.globalOption)
				
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
		#tstart = time.time()
		candidates = self.getCLCcandidates(option)
		#tend = time.time()
		#print "Candidate-Runtime: " + str(tend-tstart)
		for v in candidates:
			tmp = self.findCRC(v)
			if tmp == True:
				self.addNewCLC(v)
				break
				
	def forceControl(self): # force control of uncontrolled nodes to nearest CLC
		uncontrolled = list(set(self.cn.V) - set(self.Controlled))
		removed_flows = []
		for v in uncontrolled:
			CLCtmp = list(self.CLCs)
			CLCtmp.sort(key=lambda c: len(nx.shortest_path(self.cn.G, source=c, target=v)))
			c = CLCtmp[0]		
			path = nx.shortest_path(self.cn.G, source=c, target=v)
			ftmp = list(self.cn.G.node[c]['Satisfies'])
			ftmp.sort(key=lambda f: self.cn.fdata[f]['p_flow'], reverse=True) 
			for f in ftmp:
				removed_flows.append((c,f))
				self.remFlowSat(f)
				tmp = self.checkCLC(path)
				if tmp == True:
					self.addCLCcontrol(path)
					break
				elif tmp == 2: # processing capacity is fine, now clear path
					for i in range(0,len(path)-1):
						ftmp2 = [f for f in self.cn.F if self.flowUsesLink(f,path[i],path[i+1]) == True]
						ftmp2.sort(key=lambda f: self.cn.fdata[f]['b_flow'], reverse=True) 
						for x in ftmp2:
							removed_flows.append((self.cn.fdata[f]['CLC'],f))
							self.remFlowSat(f)
							if self.cn.G.edge[path[i]][path[i+1]]['b_rem'] >= self.cn.b_CLC:
								break
					self.addCLCcontrol(path)
					break
							
		for c,f in removed_flows: # add back flows if possible
			tmp = self.checkFlowSat(c,f)
			if tmp == True:
				self.addFlowSat(c,f)
			
	def getCLCcandidates(self,option=None):
	
		candidates = list(set(self.cn.C) - (set(self.CLCs) | set(self.banlist)))
		# avoid CRCs to be used as CLCs as long as possible
		if len(set(candidates) - set(self.CRCs)) > 0:
			candidates = [c for c in candidates if not c in self.CRCs]
		remaining_nodes = set(self.cn.V) - set(self.Controlled)
		remaining_flows = set(self.cn.F) - set(self.Satisfied)
		
		if option == "neighbors":
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
		elif option == "flows":
			ctmp = [(k,len(set(self.cn.Wf[k]) - set(self.Satisfied))) for k in candidates]
			ctmp.sort(key=lambda x: x[1], reverse=True)
			bestvalue = ctmp[0][1]
			if bestvalue > 0:
				candidates = [x[0] for x in ctmp]
			else:
				self.globalOption = "isolated_flows"
				candidates = self.getCLCcandidates("isolated_flows")
		elif option == "flows_nn": # CAUTION: very slow for many flows in the network! Currently not used.
			ctmp = [(k,len(set(self.cn.Wf[k]) - set(self.Satisfied)) + sum(len(set(self.cn.Wf[j]) - set(self.Satisfied)) for j in self.cn.G.neighbors(k))) for k in candidates]
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
		elif option == "isolated_flows2": # just a test, currently not used.
			nodes_with_flows = [(k,len(set(self.cn.Wf[k]) - set(self.Satisfied))) for k in self.cn.V]
			nodes_with_flows.sort(key=lambda x: x[1], reverse=True)
			node_with_most_flows = nodes_with_flows[0][0]
			paths = []
			for j in candidates:
				paths.append(nx.shortest_path(self.cn.G, source=j, target=node_with_most_flows))
			paths.sort(key=len)
			candidates = [p[0] for p in paths]
		elif option == "neighbors_and_flows": # currently not used.
			ctmp = [(k,len(set([k]) | set(self.cn.G.neighbors(k)) - set(self.Controlled)) + len(set(self.cn.Wf[k]) - set(self.Satisfied))) for k in candidates]
			ctmp.sort(key=lambda x: x[1], reverse=True)
			candidates = [x[0] for x in ctmp]
			
		return candidates
			
	def addNewCLC(self,v):
		paths = []
		pf = set([])
		nc = 0
		nnc = 0
		fs = 0
		
		tmp = self.checkCLC([v])
		if tmp == True:
			nc += 1
			if v not in self.Controlled:
				nnc +=1
			self.addCLCcontrol([v])
			pf = self.updatePotentialFlows(pf,v,[v])
		else:
			self.cn.C.remove(v)
			
		for i in self.cn.V:
			if i <> v and (i not in self.Controlled or len(set(self.cn.Wf[i]) - set(self.Satisfied)) > 0):
				paths.append((nx.shortest_path(self.cn.G, source=v, target=i), i in self.Controlled, len(set(self.cn.Wf[i]) - set(self.Satisfied))))
		if len(self.Controlled) < len(self.cn.V):
			paths.sort(key=lambda x: x[1])
			paths.sort(key=lambda x: len(x[0]))
			notyetsolved = True
		else:
			paths.sort(key=lambda x: len(x[0]))
			paths.sort(key=lambda x: x[2], reverse=True)
			notyetsolved = False
			
		while (len(paths) > 0 or len(pf) > 0) and (len(self.Controlled) < len(self.cn.V) or len(self.Satisfied) < len(self.cn.F)):			
			#print "Controlled: "  + str(len(self.Controlled)) + " / " + str(len(self.cn.V)) + "   Satisfied: " + str(len(self.Satisfied)) + " / " + str(len(self.cn.F))
			#print "Current CLC: " + str(v) + "   NNC: " + str(nnc) + "   VCRatio: " + str(self.VCRatio)
			#time.sleep(0.1)
			if notyetsolved and len(self.Controlled) == len(self.cn.V):
				paths.sort(key=lambda x: len(x[0]))
				paths.sort(key=lambda x: x[2], reverse=True)
				notyetsolved = False
			if len(pf) > 0 and (nnc >= self.VCRatio or len(self.Controlled) == len(self.cn.V)):
				f = self.getFlow(pf, self.getFlowOption)
				tmp = self.checkFlowSat(v,f)
				#print "CLC: " + str(v) + " Flow: " + str(f) + " Result: " + str(tmp)
				if tmp == True:
					self.addFlowSat(v,f)
					fs += 1
				pf.remove(f)
			else:
				if len(paths) == 0:
					break
				p = list(paths[0][0])
				del paths[0]
				tmp = self.checkCLC(p)
				#print "CLC: " + str(v) + " Node: " + str(p[-1]) + " Result: " + str(tmp)
				if tmp == True:
					nc += 1
					if p[-1] not in self.Controlled:
						nnc +=1
					self.addCLCcontrol(p)
					pf = self.updatePotentialFlows(pf,v,[p[-1]])
				elif tmp > 2: # issue is exhausted processing capacity
					break
		
	def updateVCRatio(self):
		self.VCRatio = (len(self.cn.V)-len(self.Controlled)) / len(self.cn.C)
		
	def updatePotentialFlows(self,pf,v,nn):
		cpf = set([])
		for w in nn:
			cpf = cpf | set(self.cn.Wf[w])
		for f in cpf:
			if self.cn.fdata[f]['isSat'] == False and set(self.cn.Wb[f]) <= set(self.cn.G.node[v]['CLCcontrol']):
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
	
	def findCRC(self, v):
		# check already active CRCs first
		paths = []
		for i in self.CRCs: 
			paths.append(nx.shortest_path(self.cn.G, source=i, target=v))
		paths.sort(key=len)
		for p in paths:
			if self.checkCRC(p) == True:
				self.addCRCcontrol(p)
				return True
		
		# need to add a new CRC, at first try to avoid active CLCs and CLC candidate
		return self.findNewCRC(v)
		
	def findNewCRC(self, v):	
		paths = []
		for i in list(set(self.cn.C) - (set(self.CRCs) | set(self.CLCs) | set([v]))):
			paths.append(nx.shortest_path(self.cn.G, source=i, target=v))
		if len(self.CRCs) == 0:	# first CRC should be placed centrally
			paths.sort(key=lambda p: sum(len(nx.shortest_path(self.cn.G, source=p[0], target=c)) for c in self.cn.C))
		else:	
			paths.sort(key=lambda p: len(p))
		for p in paths:
			if self.checkCRC(p) == True:
				self.addCRCcontrol(p)
				return True
		# last option: try CLC candidate, then already active CLCs
		if self.checkCRC([v]) == True:
			self.addCRCcontrol([v])
			return True
		paths = []
		for i in self.CLCs:
			paths.append(nx.shortest_path(self.cn.G, source=i, target=v))
		paths.sort(key=len)
		for p in paths:
			if self.checkCRC(p) == True:
				self.addCRCcontrol(p)
				return True
						
		return False
		
	def addCRCcontrol(self,path):
		v = path[0]
		w = path[-1]
		for i in range(0,len(path)-1):
			self.cn.G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.b_CRC
		self.cn.G.node[v]['Proc'] += 1
		self.cn.G.node[v]['CRCcontrol'].append(w)
		self.cn.G.node[v]['CRCpaths'][w] = path
		self.cn.G.node[v]['isCRC'] = True
		self.cn.G.node[w]['CRC'] = v
		self.cn.G.node[w]['pathtoCRC'] = path
		if v not in self.CRCs:
			self.CRCs.append(v)
			
	def addCLCcontrol(self,path):
		self.newCLCcontrols += 1
		v = path[0]
		w = path[-1]
		for i in range(0,len(path)-1):
			self.cn.G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.b_CLC
		self.cn.G.node[v]['Proc'] += 1
		self.cn.G.node[v]['CLCcontrol'].append(w)
		self.cn.G.node[v]['CLCpaths'][w] = path
		self.cn.G.node[v]['isCLC'] = True
		self.cn.G.node[w]['CLCs'].append(v)
		self.cn.G.node[w]['pathtoCLC'][v] = path
		if v not in self.CLCs:
			self.CLCs.append(v)
		if w not in self.Controlled:
			self.Controlled.append(w)
		
	def addFlowSat(self,v,f):
		self.newFlowSats += 1
		self.cn.fdata[f]['isSat'] = True
		self.cn.fdata[f]['CLC'] = v
		for k in self.cn.Wb[f]:
			path = self.cn.G.node[v]['CLCpaths'][k]
			for i in range(0,len(path)-1):
				self.cn.G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.fdata[f]['b_flow']
		self.cn.G.node[v]['Proc'] += 1
		self.cn.G.node[v]['Satisfies'].append(f)
		self.Satisfied.append(f)
	
	# checks if a certain CRC control can be established	
	def checkCRC(self,path):
		v = path[0]
		for i in range(0,len(path)-1):
			if self.cn.G.edge[path[i]][path[i+1]]['b_rem'] < self.cn.b_CRC:
				return False
		if sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (self.cn.G.node[v]['Proc']+1)*self.cn.p_CRC/self.cn.G.node[v]['p_node'] > self.cn.l_CRC:
			return False
		if self.verifyLatency(v) == False:
			return False
		
		return True
	
	# checks if a certain CLC control can be established
	def checkCLC(self,path):
		v = path[0]
		if sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (self.cn.G.node[v]['Proc']+1)*self.cn.p_CLC/self.cn.G.node[v]['p_node'] > self.cn.l_CLC:
			return 4
		if self.verifyLatency(v) == False:
			return 5
		for i in range(0,len(path)-1):
			# reserve capacity for 2 CRC assignments (might be beneficial later)
			if self.cn.G.edge[path[i]][path[i+1]]['b_rem'] - 2*self.cn.b_CRC < self.cn.b_CLC: 
				return 2
		
		return True
		
	# checks if a flow f can be satisfied by a controller v
	def checkFlowSat(self,v,f):
		if self.cn.fdata[f]['isSat'] == True:
			return False
		if not set(self.cn.Wb[f]) <= set(self.cn.G.node[v]['CLCcontrol']):
			return False
		flowedgecount = {}
		for k in self.cn.Wb[f]:
			path = self.cn.G.node[v]['CLCpaths'][k]
			for i in range(0,len(path)-1):
				if path[i] < path[i+1]:
					edgekey = (path[i],path[i+1])
				else: 
					edgekey = (path[i+1],path[i])
				if not edgekey in flowedgecount:
					flowedgecount[edgekey] = 1
				else:
					flowedgecount[edgekey] += 1
			if sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (self.cn.G.node[v]['Proc']+1)*self.cn.fdata[f]['p_flow']/self.cn.G.node[v]['p_node'] > self.cn.fdata[f]['l_flow']:
				return False
		for e in flowedgecount:
			# reserve capacity for 2 CRC and 2 CLC assignments (complete control structure more important than flow satisfaction)
			if self.cn.G.edge[e[0]][e[1]]['b_rem'] - 2*self.cn.b_CRC - 2*self.cn.b_CLC < flowedgecount[(e[0],e[1])] * self.cn.fdata[f]['b_flow']:
				return False
		if self.verifyLatency(v) == False:
			return False
		
		return True
	
	# checks if all latency constraints are (still) met
	def verifyLatency(self,v):
		for i in self.cn.G.node[v]['CRCcontrol']:
			path = self.cn.G.node[v]['CRCpaths'][i]
			if sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (self.cn.G.node[v]['Proc']+1)*self.cn.p_CRC/self.cn.G.node[v]['p_node'] > self.cn.l_CRC:
				return False
		for i in self.cn.G.node[v]['CLCcontrol']:
			path = self.cn.G.node[v]['CLCpaths'][i]
			if sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (self.cn.G.node[v]['Proc']+1)*self.cn.p_CLC/self.cn.G.node[v]['p_node'] > self.cn.l_CLC:
				return False
		for f in self.cn.G.node[v]['Satisfies']:
			for i in self.cn.Wb[f]:
				path = self.cn.G.node[v]['CLCpaths'][i]
				if sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + (self.cn.G.node[v]['Proc']+1)*self.cn.fdata[f]['p_flow']/self.cn.G.node[v]['p_node'] > self.cn.fdata[f]['l_flow']:
					return False
					
		return True	
		
	def remCRC(self,v):
		self.cn.G.node[v]['isCRC'] = False
		tmp = list(self.cn.G.node[v]['CRCcontrol'])
		for w in tmp:
			self.remCRCcontrol(v,w)
		self.CRCs.remove(v)	
		
	def remCRCcontrol(self,v,w):
		path = self.cn.G.node[v]['CRCpaths'][w]
		for i in range(0,len(path)-1):
			self.cn.G.edge[path[i]][path[i+1]]['b_rem'] += self.cn.b_CRC
		self.cn.G.node[v]['Proc'] -= 1
		self.cn.G.node[v]['CRCcontrol'].remove(w)
		del self.cn.G.node[v]['CRCpaths'][w]
		self.cn.G.node[w]['CRC'] = None
		self.cn.G.node[w]['pathtoCRC'] = None
		if self.cn.G.node[w]['isCLC'] == True:
			self.uncontrolledCLCs.append(w)		
			self.state = "NOT SOLVED"
		if len(self.cn.G.node[v]['CRCcontrol']) == 0:
			self.remCRC(v)
		
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
		
	def remFlowSat(self,f):
		v = self.cn.fdata[f]['CLC']
		for k in self.cn.Wb[f]:
			path = self.cn.G.node[v]['CLCpaths'][k]
			for i in range(0,len(path)-1):
				self.cn.G.edge[path[i]][path[i+1]]['b_rem'] += self.cn.fdata[f]['b_flow']
		self.cn.G.node[v]['Proc'] -= 1
		self.cn.G.node[v]['Satisfies'].remove(f)
		self.cn.fdata[f]['isSat'] = False
		self.cn.fdata[f]['CLC'] = None
		self.Satisfied.remove(f)
		
	def addFlow(self,stime=0,dur=None,amount=1):
		for i in range(1,amount+1):
			self.cn.addFlow(stime=stime,dur=dur)
		if self.flexOperation and len(self.CLCs) > 0:
			if amount == 1:
				self.browseCurrentCLCsforSingleFlow(self.cn.F[-1])
			else:
				self.browseCurrentCLCs()
		
	def remFlow(self,f):
		#self.cn.fdata[-f] = copy.deepcopy(self.cn.fdata[f]) # uncomment ONLY for debbuging!
		if self.cn.fdata[f]['isSat'] == True:
			self.remFlowSat(f)
		tmplist = list(self.cn.Wb[f])
		self.cn.remFlow(f)
		if self.flexOperation:
			self.cleanupCLCcontrols(tmplist)
		
	def clearFlows(self):
		tmp = list(self.cn.F)
		for f in tmp:
			self.remFlow(f)
						
	def browseCurrentCLCs(self):
		paths = []
		pf = {}
		nnc = {}
		for v in self.CLCs:
			if self.CLCload(v) < 0.99:
				pf[v] = self.updatePotentialFlows(set([]),v,self.cn.G.node[v]['CLCcontrol'])
				nnc[v] = 0
				for i in list(set(self.cn.V) - set(self.cn.G.node[v]['CLCcontrol'])):
					if i not in self.Controlled or len(set(self.cn.Wf[i]) - set(self.Satisfied)) > 0:
						paths.append((nx.shortest_path(self.cn.G, source=v, target=i), i in self.Controlled, len(set(self.cn.Wf[i]) - set(self.Satisfied))))
					
		if len(self.Controlled) < len(self.cn.V):
			paths.sort(key=lambda x: x[1])
			paths.sort(key=lambda x: len(x[0]))
			notyetsolved = True
		else:
			paths.sort(key=lambda x: len(x[0]))
			paths.sort(key=lambda x: x[2], reverse=True)
			notyetsolved = False
				
		while (len(paths) > 0 or sum(len(pf[v]) for v in pf) > 0) and (len(self.Controlled) < len(self.cn.V) or len(self.Satisfied) < len(self.cn.F)):			
			if notyetsolved and len(self.Controlled) == len(self.cn.V):
				paths.sort(key=lambda x: len(x[0]))
				paths.sort(key=lambda x: x[2], reverse=True)
				notyetsolved = False

			if sum(len(pf[v]) for v in pf) > 0 and (len(paths) == 0 or len(self.Controlled) == len(self.cn.V)):
				currv = [v for v in pf if len(pf[v]) > 0][0]
			else: 
				currv = paths[0][0][0]
				
			if self.CLCload(currv) > 0.99:
				pf[currv] = set([])	
				paths = [p for p in paths if p[0][0] <> currv]
			elif len(pf[currv]) > 0 and (len(paths) == 0 or nnc[currv] >= self.VCRatio or len(self.Controlled) == len(self.cn.V)):
				f = self.getFlow(pf[currv], self.getFlowOption)
				tmp = self.checkFlowSat(currv,f)
				if tmp == True:
					self.addFlowSat(currv,f)
					for w in pf:
						if f in pf[w]:
							pf[w].remove(f)
				else:
					pf[currv].remove(f)
			else:
				p = list(paths[0][0])
				del paths[0]
				tmp = self.checkCLC(p)
				if tmp == True:
					if p[-1] not in self.Controlled:
						nnc[currv] +=1
					self.addCLCcontrol(p)
					pf[currv] = self.updatePotentialFlows(pf[currv],currv,[p[-1]])
				elif tmp > 2:	
					paths = [p for p in paths if p[0][0] <> currv]
					pf[currv] = set([])
						
	def CLCload(self,c):
		if not c in self.CLCs:
			return 0
			
		loadlist = []
		# for i in self.cn.G.node[c]['CRCcontrol']:
			# path = self.cn.G.node[c]['CRCpaths'][i]
			# loadlist.append(sum(2*G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + self.cn.G.node[c]['Proc']*self.cn.p_CRC/self.cn.G.node[c]['p_node'] / self.cn.l_CRC)
		for i in self.cn.G.node[c]['CLCcontrol']:
			path = self.cn.G.node[c]['CLCpaths'][i]
			loadlist.append(sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + self.cn.G.node[c]['Proc']*self.cn.p_CLC/self.cn.G.node[c]['p_node'] / self.cn.l_CLC)
		for f in self.cn.G.node[c]['Satisfies']:
			for i in self.cn.Wb[f]:
				path = self.cn.G.node[c]['CLCpaths'][i]
				loadlist.append(sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)) + self.cn.G.node[c]['Proc']*self.cn.fdata[f]['p_flow']/self.cn.G.node[c]['p_node'] / self.cn.fdata[f]['l_flow'])

		return max(loadlist)
		
	def CLCoutput(self,c):
		out = "Data for CLC " + str(c) + ":\n"
		out += "Load: " + str(self.CLCload(c))  + "\n"
		out += "Proc: " + str(self.cn.G.node[c]['Proc']) + ", Nodes controlled: " + str(len(self.cn.G.node[c]['CLCcontrol'])) + ", Flows satisfied: " + str(len(self.cn.G.node[c]['Satisfies'])) + "\n"
		if len(self.cn.G.node[c]['Satisfies']) > 0:
			out += "Biggest flow satisfied: " + str(max(self.cn.fdata[f]['p_flow'] for f in self.cn.G.node[c]['Satisfies'])) + "\n"
		
		return out
		
	def getAverageCLCload(self):
		return sum(self.CLCload(c) for c in self.CLCs)/len(self.CLCs)
		
	def getCLCwithLeastLoad(self):
		tmp = list(self.CLCs)
		tmp.sort(key=lambda c: self.CLCload(c))
		return tmp[0]
		
	def getAverageCLCpathlength(self):
		return sum(len(self.cn.G.node[c]['CLCpaths'][v]) for c in self.CLCs for v in self.cn.G.node[c]['CLCcontrol']) / sum(len(self.cn.G.node[c]['CLCcontrol']) for c in self.CLCs)
		
	def getAverageCRCpathlength(self):
		return sum(len(self.cn.G.node[c]['CRCpaths'][v]) for c in self.CRCs for v in self.cn.G.node[c]['CRCcontrol']) / sum(len(self.cn.G.node[c]['CRCcontrol']) for c in self.CRCs)
		
	def getAverageLinkUsage(self):
		return sum(self.cn.G[u][v]['b_rem']/self.cn.G[u][v]['b_cap'] for u,v in self.cn.G.edges()) / self.cn.G.number_of_edges()
		
	def CLCcontrolRatio(self):
		return sum(len(self.cn.G.node[c]['CLCcontrol']) for c in self.CLCs)/len(self.cn.V)
		
	def cleanupCLCcontrols(self,nodelist):
		counter = 0
		vtmp = list(nodelist)
		random.shuffle(vtmp)
		for v in vtmp:
			ctmp = list(self.cn.G.node[v]['CLCs'])
			random.shuffle(ctmp)
			for c in ctmp:
				if c <> v and len(self.cn.G.node[v]['CLCs']) > 1 and len(set(self.cn.G.node[c]['Satisfies']) & set(self.cn.Wf[v])) == 0:
					self.remCLCcontrol(c,v)
					counter += 1
		#print "CLC controls removed: " + str(counter)
		
	def browseCurrentCLCsforSingleFlow(self,f):
		CLCstmp = list([c for c in self.CLCs if set(self.cn.Wb[f]) <= set(self.cn.G.node[c]['CLCcontrol'])])
		for c in CLCstmp:	
			tmp = self.checkFlowSat(c,f)
			if tmp == True:
				self.addFlowSat(c,f)
				return 1
		
		CLCstmp = list([c for c in self.CLCs if not set(self.cn.Wb[f]) <= set(self.cn.G.node[c]['CLCcontrol'])])
		CLCstmp.sort(key=lambda c: sum(len(nx.shortest_path(self.cn.G, source=c, target=i)) for i in self.cn.Wb[f]))
		CLCstmp.sort(key=lambda c: len(set(self.cn.Wb[f]) - set(self.cn.G.node[c]['CLCcontrol'])))
		for c in CLCstmp:
			paths = (nx.shortest_path(self.cn.G, source=c, target=i) for i in self.cn.Wb[f] if not i in self.cn.G.node[c]['CLCcontrol'])
			for p in paths:
				tmp = self.checkCLC(p)
				if tmp == True:
					self.addCLCcontrol(p)
				else: 
					break
			if tmp == True:
				tmp = self.checkFlowSat(c,f)
				if tmp == True:
					self.addFlowSat(c,f)
				else: 
					for p in paths:
						self.remCLCcontrol(c,p[-1])
						
	def flowUsesLink(self,f,v,w):
		if self.cn.fdata[f]['isSat'] == True:
			c = self.cn.fdata[f]['CLC']
			for k in self.cn.Wb[f]:
				path = self.cn.G.node[k]['pathtoCLC'][c]
				if any(([v,w] == path[i:i+1]) for i in xrange(len(path)-1)) or any(([w,v] == path[i:i+1]) for i in xrange(len(path)-1)):
					return True
		return False
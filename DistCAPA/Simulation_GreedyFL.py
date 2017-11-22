from lib import crowd_network as CN
from ComplexNetworkSim import NetworkSimulation
#import FlexFCPF_PartialGraph
import GreedyFL_Flows
import Manager
import math, sys
from lib import cp_flex_fcfs

import time
import networkx as nx

directory = 'test'
TRIALS = 1
Node = 1
CLC = 2
CRC = 3


class Simulation_GreedyFL:

	def __init__(self, cn):
		self.MAX_SIMULATION_TIME = 50
		self.state = 'Not Solved'
		self.CRCs = []
		self.CLCs = []
		self.Controlled = []
		self.Satisfied = []
		self.newCLCcontrols = 0
		self.newFlowSats = 0
		self.successfulCleanup = {}
		self.nrCleanupAttempts = {}
		self.iteration = 0
		self.cn = cn
		self.LLlimit = 0.25
		self.current_time = None
		self.max_dist = self.getMaxDist()
		self.host_dist = self.getHostDist()
		self.shortestPaths = self.getShortestPaths()
		self.use_resume_data = True
		self.resumeData = {}

	def run(self):
		self.globalSharedParameters = {}
		self.globalSharedParameters['cn'] = self.cn
		self.globalSharedParameters['simTime'] = self.MAX_SIMULATION_TIME
		self.globalSharedParameters['solved'] = self.state == 'Solved'
		self.globalSharedParameters['flowsSat'] = len(self.Satisfied)
		self.globalSharedParameters['nrOfCleanupAttempts'] = {}
		self.globalSharedParameters['successfulCleanup'] = {}
		self.globalSharedParameters['runtime'] = {}
		self.globalSharedParameters['LLlimit'] = self.LLlimit
		self.globalSharedParameters['maxDist'] = self.max_dist
		self.globalSharedParameters['hostDist'] = self.host_dist
		self.globalSharedParameters['shortestPaths'] = self.shortestPaths
		if self.use_resume_data:
			self.globalSharedParameters['resumeData'] = self.resumeData
		else:
			self.globalSharedParameters['resumeData'] = {}

		states = []
		for n in self.cn.G.nodes():
			self.globalSharedParameters['runtime'][n] = 0.0
			states.append(Node)
			if n in self.cn.C:
				if self.cn.G.node[n]['isCLC']:
					states[-1] = CLC
				elif self.cn.G.node[n]['isCRC']:
					states[-1] = CRC

		simulation = NetworkSimulation(self.cn.G,states,GreedyFL_Flows.GreedyFL_Flows,directory,self.MAX_SIMULATION_TIME,TRIALS,Manager.Manager,**self.globalSharedParameters)
		
		simulation.runSimulation()

		self.successfulCleanup = self.globalSharedParameters['successfulCleanup']
		self.nrCleanupAttempts = self.globalSharedParameters['nrOfCleanupAttempts']
		
		self.resumeData = dict(self.globalSharedParameters['resumeData'])

		self.analyse()
		self.validityCheck(log=True,fix=False)

		self.iteration += 1
		
		'''print self.state
		print str(len(self.CLCs)) + ' CLCs out of ' + str(len(self.cn.C))
		print str(len(self.Satisfied)) + ' flows out of ' + str(len(self.cn.F))'''

	def analyse(self):
		self.Controlled = []
		for n in self.cn.V:
			if n in self.cn.C:
				if self.cn.G.node[n]['isCLC'] == True or len(self.cn.G.node[n]['CLCs']) > 0:
					self.Controlled.append(n)
			else:
				if len(self.cn.G.node[n]['CLCs']) > 0:
					self.Controlled.append(n)
		if len(self.Controlled) < len(self.cn.V):
			self.state = 'Not Solved'
		else:
			self.state = 'Solved'
		
		self.CLCs = []
		for n in self.cn.C:
			if self.cn.G.node[n]['isCLC']:
				self.CLCs.append(n)
		
		self.Satisfied = []
		for f in self.cn.F:
			if self.cn.fdata[f]['isSat']:
				self.Satisfied.append(f)
	
	# check validity and fix inconsistencies that can happen if the simulation terminates at the wrong time.
	def validityCheck(self,log=False,fix=False):
		ok = True
		log_output = ''
		fix_inconsistencies = fix
		
		for clc in self.CLCs:
			for n in self.cn.G.node[clc]['CLCcontrol']:
				if clc not in self.cn.G.node[n]['CLCs']:
					if fix_inconsistencies == True:
						self.cn.G.node[n]['CLCs'].append(clc)
					if log == True:
						log_output += str(clc) + ' controls ' + str(n) + ', but ' + str(n) + ' isn\'t controlled by ' + str(clc) + '\n'
					else:
						print str(clc) + ' controls ' + str(n) + ', but ' + str(n) + ' isn\'t controlled by ' + str(clc)
					ok = False
			for f in self.cn.G.node[clc]['Satisfies']:
				if clc <> self.cn.fdata[f]['CLC']:
					if log == True:
						log_output += str(clc) + ' satisfies ' + str(f) + ', but ' + str(f) + ' thinks it is satisfied by ' + str(self.cn.fdata[f]['CLC']) + '\n'
					else:
						print str(clc) + ' satisfies ' + str(f) + ', but ' + str(f) + ' thinks it is satisfied by ' + str(self.cn.fdata[f]['CLC'])
					ok = False
			for attr in ['CLCcontrol','Satisfies']:
				if len(self.cn.G.node[clc][attr]) <> len(list(set(self.cn.G.node[clc][attr]))):
					if log == True:
						log_output += str(clc) + ' has duplicate entries in ' + attr + ' : ' + str([n for n in self.cn.G.node[clc][attr] if self.cn.G.node[clc][attr].count(n) > 1]) + '\n'
					else:
						print str(clc) + ' has duplicate entries in ' + attr + ' : ' + str([n for n in self.cn.G.node[clc][attr] if self.cn.G.node[clc][attr].count(n) > 1])
					ok = False
		
		for n in self.cn.V:
			#print self.Controlled
			#print "Node: " + str(n) + ", CLCs: " + str(self.cn.G.node[n]['CLCs'])
			toBeRemoved = []
			for clc in self.cn.G.node[n]['CLCs']:
				if n not in self.cn.G.node[clc]['CLCcontrol']:
					toBeRemoved.append(clc)
					if log == True:
						log_output += str(n) + ' is controlled by ' + str(clc) + ', but ' + str(clc) + ' doesn\'t control ' + str(n) + ' (but ' + str(len(self.cn.G.node[clc]['CLCcontrol'])) + ' other nodes) \n'
					else:
						print str(n) + ' is controlled by ' + str(clc) + ', but ' + str(clc) + ' doesn\'t control ' + str(n) + ' (but ' + str(len(self.cn.G.node[clc]['CLCcontrol'])) + ' other nodes)'
					ok = False
			if fix_inconsistencies == True:
				for i in toBeRemoved:
					self.cn.G.node[n]['CLCs'].remove(i)
				if len(self.cn.G.node[n]['CLCs']) == 0 and n in self.Controlled:
					self.Controlled.remove(n)
			if len(self.cn.G.node[n]['CLCs']) <> len(list(set(self.cn.G.node[n]['CLCs']))):
				if log == True:
					log_output += str(clc) + ' has duplicate entries in its CLCs : ' + str([n for n in self.cn.G.node[n]['CLCs'] if self.cn.G.node[n]['CLCs'].count(n) > 1]) + '\n'
				else:
					print str(clc) + ' has duplicate entries in its CLCs : ' + str([n for n in self.cn.G.node[n]['CLCs'] if self.cn.G.node[n]['CLCs'].count(n) > 1])
				ok = False

		for f in self.cn.F:
			if self.cn.fdata[f]['isSat']:
				clc = self.cn.fdata[f]['CLC']
				for n in self.cn.Wb[f]:
					if clc not in self.cn.G.node[n]['CLCs']:
						if fix_inconsistencies == True:
							self.cn.G.node[n]['CLCs'].append(clc)
						if log == True:
							log_output += 'Flow ' + str(f) + ' belongs to ' + str(self.cn.Wb[f]) + ', but ' + str(n) + ' doesn\'t have ' + str(self.cn.fdata[f]['CLC']) + ' as its CLC' + '\n'
						else:
							print 'Flow ' + str(f) + ' belongs to ' + str(self.cn.Wb[f]) + ', but ' + str(n) + ' doesn\'t have ' + str(self.cn.fdata[f]['CLC']) + ' as its CLC'
						ok = False
				if not f in self.cn.G.node[clc]['Satisfies']:
					if log == True:
						log_output += str(f) + ' thinks it is satisfied by ' + str(clc) + ', but ' + str(clc) + ' does not satisfy ' + str(f) + '\n'
					else:
						print str(f) + ' thinks it is satisfied by ' + str(clc) + ', but ' + str(clc) + ' does not satisfy ' + str(f)
					ok = False
						
		for c in self.CLCs:
			if self.cn.G.node[c]['p_rem'] < 0:
				if log == True:
					log_output += 'CLC ' + str(c) + ' uses more than its available processing capacity. Difference: ' + str(self.cn.G.node[c]['p_rem']) + '\n'
				else:
					print 'CLC ' + str(c) + ' uses more than its available processing capacity. Difference: ' + str(self.cn.G.node[c]['p_rem'])
				ok = False
		
		if log == True and len(log_output) > 0:
			logfile = open("GreedyFL_log.txt", "a")
			if self.current_time is not None:
				logfile.write("Current time: " + str(self.current_time) + "\n")
			logfile.write(log_output)
			logfile.close()
		
		return ok

	def printInfo(self):
		for n in self.cn.V:
			if n in self.cn.C:
				if self.cn.G.node[n]['isCLC']:
					print str(n) + ' is CLC, controls ' + str(self.cn.G.node[n]['CLCcontrol'])
			print str(n) + ' is controlled by ' + str(self.cn.G.node[n]['CLCs'])
		print str(len(self.CLCs)) + ' CLCs used'
		print str(len(self.Satisfied)) + ' flows out of ' + str(len(self.cn.F)) + ' satisfied'

	def updateTime(self,t,addNewFlow=False):
		self.current_time = t
		self.removeExpiredFlows()
		if addNewFlow == True:
			self.addFlow(stime=t)
			
	def removeExpiredFlows(self):
		for i in [j for j in self.cn.fremhelp if j < self.current_time]:
			tmp = list(self.cn.fremhelp[i])
			for f in tmp:
				self.remFlow(f)
		if math.ceil(self.current_time) in self.cn.fremhelp:
			tmp = list(self.cn.fremhelp[math.ceil(self.current_time)])
			for f in tmp:
				if self.cn.fdata[f]['stime'] + self.cn.fdata[f]['duration'] < self.current_time:
					self.remFlow(f)		

		# for debugging
		tsum = sum(1 for i in self.cn.fremhelp for j in self.cn.fremhelp[i])
		if tsum <> len(self.cn.F):
			print "Error: fremhelp not working properly!"
			print tsum
			print len(self.cn.F)
			exit(1)
			
	def getMaxDist(self):
		mdist = {}
		for v in self.cn.V:
			mdist[v] = max([len(nx.shortest_path(self.cn.G, source = v, target = w)) for w in self.cn.V]) - 1
			
		return mdist
		
	def getHostDist(self):
		cdist = {}
		for v in self.cn.V:
			cdist[v] = min([len(nx.shortest_path(self.cn.G, source = v, target = c)) for c in self.cn.C if c <> v]) - 1
			
		return cdist
		
	def getShortestPaths(self):
		sp = {}
		for v in self.cn.V:
			sp[v] = {}
			for w in self.cn.V:
				sp[v][w] = nx.shortest_path(self.cn.G, source = v, target = w)
			
		return sp

	# Code from CPFlex
	#---------------------------------------------------------------------------------
	def CLCload(self, c):
		return self.cn.G.node[c]['p_node'] - self.cn.G.node[c]['p_rem']

	def getAverageCLCload(self):
		if len(self.CLCs) == 0:
			return 0
		else:
			return sum(self.CLCload(c) for c in self.CLCs)/len(self.CLCs)

	def getCLCwithLeastLoad(self):
		tmp = list(self.CLCs)
		tmp.sort(key=lambda c: self.CLCload(c))
		return tmp[0]

	def addFlow(self, stime = 0, dur = None, amount = 1):
		for i in range(1, amount + 1):
			self.cn.addFlow(stime = stime, dur = dur)

	def remFlow(self, f):
		if self.cn.fdata[f]['isSat'] == True:
			v = self.cn.fdata[f]['CLC']
			for k in self.cn.Wb[f]:
				path = self.cn.G.node[v]['CLCpaths'][k]
				for i in range(0,len(path)-1):
					self.cn.G.edge[path[i]][path[i+1]]['b_rem'] += self.cn.fdata[f]['b_flow']
			self.cn.G.node[v]['p_rem'] += self.cn.G.node[v]['ProcFlow'][f]
			del self.cn.G.node[v]['ProcFlow'][f]
			self.cn.G.node[v]['Satisfies'].remove(f)
			self.cn.fdata[f]['isSat'] = False
			self.cn.fdata[f]['CLC'] = None
			self.Satisfied.remove(f)
		self.cn.remFlow(f)

	def scratchCopy(self):
		cntmp = self.cn.copy()
		cntmp.cleanup()
		return Simulation_GreedyFL(cntmp)

	def getAverageCRCpathlength(self):
		return 0

	def getAverageCLCpathlength(self):
		if len(self.CLCs) == 0:
			return 0
		else:
			return float(sum(len(self.cn.G.node[c]['CLCpaths'][v]) for c in self.CLCs for v in self.cn.G.node[c]['CLCcontrol'])) / sum(len(self.cn.G.node[c]['CLCcontrol']) for c in self.CLCs)

	def CLCcontrolRatio(self):
		return float(sum(len(self.cn.G.node[c]['CLCcontrol']) for c in self.CLCs))/len(self.cn.V)
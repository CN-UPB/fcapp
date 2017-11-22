from __future__ import division
import networkx as nx
import sys, copy
from math import exp,sqrt,pow,ceil
import random
from ChModel import *
import pdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties

ft_file = {"CoMP": "flowtypes_CoMP.csv", "generic": "flowtypes_new.csv"}
dur_params = {"expo": 0.02, "pareto": 1.02, "uniform": 120}
					
class CrowdNetwork:

	def __init__(self):
		self.G = nx.Graph()
		self.flowDurationMode = "expo" # type of random variate to determine DFG durations
		self.discardedFlows = 0 # for monitoring only
		self.fdata = {}
		self.fremhelp = {}
	
	def generate_from_file(self, filename, modify_controllers=False, contrProb=None, evalscen="generic"):
		
		if modify_controllers == True and contrProb == None:
			print("Error: Modifying potential hosts requires setting a probability!")
			exit(1)
				
		# read flowtypes
		
		try:
			self.loadflowtypes(ft_file[evalscen])
		except:
			print("Error: Could not read flowtypes from " + ft_file[evalscen] + "!")
			exit(1)
		self.evalscen = evalscen
		
		# read input file

		try:
			fin = open(filename, "r")
			tmp = fin.readline()
			self.V = [int(n) for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split(" ")]
			self.no_bs = len(self.V)
			if self.no_bs == 0:
				print("Error: Empty network!")
				exit(1)
			tmp = fin.readline()			
			self.C = [int(n) for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split(" ")]
			self.no_C_ori = len(self.C)
			
			if modify_controllers == True and contrProb <> None:
				self.C = []
				for n in self.V:
					c = random.random()
					if c < contrProb:
						self.C.append(n)
				if len(self.C) == 0:
					self.C.append(random.choice(self.V))
			
			self.no_C = len(self.C)
			if self.no_C == 0:
				print("Error: No potential controller nodes!")
				exit(1)
			
			for n in self.V:
				if n in self.C:
					self.G.add_node(n, CRC=None, CLCs=[], isCLC=False, isCRC=False, CLCcontrol=[], CRCcontrol=[], Satisfies=[], Proc=0, ProcCRC={}, ProcCLC={}, ProcFlow={}, CRCpaths={}, CLCpaths={}, pathtoCRC=None, pathtoCLC={}, pathtoTAP={}, pin='true', style='filled',fillcolor='blue',shape='circle', width=0.2, height=0.2, marker=0)
				else:
					self.G.add_node(n, CLCs=[], pathtoCLC={}, pin='true', style='filled',fillcolor='grey',shape='circle', width=0.2, height=0.2, marker='o')
			
			tmp = fin.readline()
			if tmp[:len("set T")] == "set T":
				self.T = [int(n) for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split(" ")]
				self.no_T = len(self.T)
				if self.no_T == 0:
					print("Error: No TAPs in the network!")
					exit(1)
				tmp = fin.readline()
				for t in self.T:
					self.G.node[t]['TAPcontrol'] = []
			else:
				self.T = []
				self.no_T = 0
				
			self.F = [int(n) for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split(" ")]
			self.no_flows = len(self.F)
			self.lastflow = self.no_flows-1
			tmp = fin.readline()
			if tmp[:len("set F_BB")] == "set F_BB":
				self.F_BB = [int(n) for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split(" ")]
				tmp = fin.readline()
			else:
				self.F_BB = []
			self.no_flowsBB = len(self.F_BB)
				
			for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split(" "):
				self.G.add_edge(int(n[n.find("(")+1:n.find(",")]),int(n[n.find(",")+1:n.find(")")]))
			self.no_links = self.G.number_of_edges()
			
			tmp = fin.readline()
			tmp = fin.readline().split(" ")
			if tmp[2] == "b_max": # determine whether or not file contains deprecated b_max parameter
				b_max_fix = 0
			else:
				b_max_fix = 1
			
			for i in range(0, self.no_bs):
				tmp = fin.readline().split(" ")
				if int(tmp[0]) in self.C:
					self.G.node[int(tmp[0])]['p_node'] = float(tmp[2-b_max_fix])
					self.G.node[int(tmp[0])]['p_rem'] = self.G.node[int(tmp[0])]['p_node']
				self.G.node[int(tmp[0])]['x'] = float(tmp[3-b_max_fix])
				self.G.node[int(tmp[0])]['y'] = float(tmp[4-b_max_fix])
				
			tmp = fin.readline()
			tmp = fin.readline()
			for i in range(0, self.no_links):
				tmp = fin.readline().split(" ")
				tmp = fin.readline().split(" ")
				self.G.edge[int(tmp[0])][int(tmp[1])]['b_cap'] = float(tmp[2])
				self.G.edge[int(tmp[0])][int(tmp[1])]['l_cap'] = float(tmp[3])
				self.G.edge[int(tmp[0])][int(tmp[1])]['b_rem'] = float(tmp[2])
			
			tmp = fin.readline()
			tmp = fin.readline()
			for i in range(0, self.no_flows):
				tmp = fin.readline().split(" ")
				f = int(tmp[0])
				self.fdata[f] = {}
				self.fdata[f]['isSat'] = False
				self.fdata[f]['CLC'] = None
				self.fdata[f]['hasTAP'] = False
				self.fdata[f]['TAPpath'] = []
				if f in self.F_BB:
					self.fdata[f]['toBB'] = 1
				else: 
					self.fdata[f]['toBB'] = 0
				self.fdata[f]['isGen'] = False
				self.fdata[f]['genstime'] = 0
				self.fdata[f]['b_flow'] = float(tmp[1])
				self.fdata[f]['l_flow'] = float(tmp[2])
				self.fdata[f]['p_flow'] = float(tmp[3])
				self.fdata[f]['x'] = float(tmp[4])
				self.fdata[f]['y'] = float(tmp[5])
				self.fdata[f]['stime'] = 0
				self.fdata[f]['duration'] = self.getDuration()
				fremindex = ceil(self.fdata[f]['stime'] + self.fdata[f]['duration'])
				if not fremindex in self.fremhelp:
					self.fremhelp[fremindex] = []
				self.fremhelp[fremindex].append(f)
				
			tmp = fin.readline()
			tmp = fin.readline()
			self.b_CLC = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			self.b_CRC = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			self.l_CLC = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			self.l_CRC = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			self.p_CLC = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			self.p_CRC = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			tmp = fin.readline()
			tmp = fin.readline()
			tmp = fin.readline()
			if tmp[:len("param : m_")] == "param : m_": # skipping lines containing no longer used weights from older input files
				tmp = fin.readline()
				tmp = fin.readline()
				tmp = fin.readline()
				tmp = fin.readline()
				
			self.dist = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			self.dim1 = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
			tmp = fin.readline()
			self.dim2 = float(tmp[tmp.find("=")+2:tmp.find(";")-1])

			tmp = fin.readline()
			if tmp[:len("param : L_BB")] == "param : L_BB": # handling whether or not input file contains L_BB value
				self.L_BB = float(tmp[tmp.find("=")+2:tmp.find(";")-1])
				tmp = fin.readline()
			else:
				self.L_BB = 0
				
			tmp = fin.readline()	
			self.W = {}
			self.Wb = {}
			for f in self.F:
				self.Wb[f] = []
				for j in self.V:
					tmp = fin.readline().split(" ")
					self.W[int(tmp[0]),int(tmp[1])] = int(tmp[2])
					if int(tmp[2]) == 1:
						self.Wb[f].append(int(tmp[1]))
				
			self.Wf = {}
			for j in self.V:
				self.Wf[j] = [f for f in self.F if self.W[f,j] == 1]
				
			for f in self.F:
				self.fdata[f]['connections'] = len(self.Wb[f])
					
			return True
			
		except:
			
			return False
		
	def copy(self):
		cn = CrowdNetwork()
		cn.__dict__ = copy.deepcopy(self.__dict__)
		
		return cn
		
	def loadflowtypes(self,filename):
		self.ftypes = []
		self.ftypedata = {}
		fin = open(filename, "r")
		attributes = [att.translate(None, ' \n\t\r') for att in fin.readline().split(";")]
		while True:
			try:
				tmp = fin.readline().split(";")
				if len(tmp[0]) == 0:
					break
				self.ftypes.append(tmp[0])
				self.ftypedata[tmp[0]] = {}
				for i,att in enumerate(attributes[1:],start=1):
					self.ftypedata[tmp[0]][att] = float(tmp[i])
			except:
				break
		
		if sum(self.ftypedata[type]['prob'] for type in self.ftypes) < 0.999 or sum(self.ftypedata[type]['prob'] for type in self.ftypes) > 1.001:
			print("ERROR: flow probabilities don't sum up to 1.0!")
			exit(1)
			
	def getDuration(self):
		if not self.flowDurationMode in dur_params:
			print "Error: unsupported flowDurationMode!"
			exit(1)
	
		if self.flowDurationMode == "pareto":
			return random.paretovariate(dur_params[self.flowDurationMode])
		elif self.flowDurationMode == "expo":
			return random.expovariate(dur_params[self.flowDurationMode])
		elif self.flowDurationMode == "uniform":
			dtmp = random.random()
			return dur_params[self.flowDurationMode] * dtmp
		
	def addFlow(self,stime=0,dur=None):
		self.lastflow += 1
		f = self.lastflow
		self.F.append(f)
		self.fdata[f] = {}
		self.fdata[f]['isSat'] = False
		self.fdata[f]['CLC'] = None
		self.fdata[f]['hasTAP'] = False   
		self.fdata[f]['TAPpath'] = []
		self.fdata[f]['toBB'] = 0
		self.fdata[f]['isGen'] = False
		self.fdata[f]['genstime'] = 0
		self.fdata[f]['stime'] = stime
		if dur is not None:
			self.fdata[f]['duration'] = dur
		else:
			self.fdata[f]['duration'] = self.getDuration()
		fremindex = ceil(self.fdata[f]['stime'] + self.fdata[f]['duration'])
		if not fremindex in self.fremhelp:
			self.fremhelp[fremindex] = []
		self.fremhelp[fremindex].append(f)
		
		if self.evalscen == "generic":
			sinr_insufficient = True
			while (sinr_insufficient):
				self.fdata[f]['x'] = random.uniform(-self.dist, self.dim1 * self.dist)
				self.fdata[f]['y'] = random.uniform(-self.dist, self.dim2 * self.dist)
				self.fdata[f]['connections'] = 0
				
				rspw = []
				for bs in self.V:
					s = sqrt(pow(self.G.node[bs]['x'] - self.fdata[f]['x'], 2) + pow(self.G.node[bs]['y'] - self.fdata[f]['y'], 2))
					rspw.append([bs,received_signal_power_watts(s),s])
					
				rspw.sort(key=lambda rspw: rspw[1], reverse=True)
				
				wattsum = rspw[0][1]
				self.fdata[f]['connections'] += 1
				# SINR threshold = 0.0 dB (formerly -7.5 dB)
				while (sinr(rspw, self.fdata[f]['connections'], self.no_bs) < 0.0 and self.fdata[f]['connections'] < min(3, self.no_bs)):
					self.fdata[f]['connections'] += 1
				
				if (sinr(rspw, self.fdata[f]['connections'], self.no_bs) >= 0.0):
					sinr_insufficient = False
				else:
					self.discardedFlows += 1
			
			self.Wb[self.lastflow] = []		
			for j in range(0, self.fdata[f]['connections']):
				self.W[f,rspw[j][0]] = 1
				self.Wb[f].append(rspw[j][0])
			for j in self.Wb[f]:
				self.Wf[j].append(f)
		elif self.evalscen == "CoMP":
			self.fdata[f]['x'] = random.uniform(-self.dist, self.dim1 * self.dist)
			self.fdata[f]['y'] = random.uniform(-self.dist, self.dim2 * self.dist)
			self.fdata[f]['connections'] = 0
				
			snrs = []
			for bs in self.V:
				s = sqrt(pow(self.G.node[bs]['x'] - self.fdata[f]['x'], 2) + pow(self.G.node[bs]['y'] - self.fdata[f]['y'], 2))
				snrs.append([bs,snr(s),s])
				
			snrs.sort(key=lambda snrs: snrs[1], reverse=True)
			
			# SINR threshold = 0.0 dB (formerly -7.5 dB)
			if (snrs[2][1] >= 0.0):
				self.fdata[f]['connections'] = 3
			else: 
				self.fdata[f]['connections'] = 2
			
			self.Wb[self.lastflow] = []		
			for j in range(0, self.fdata[f]['connections']):
				self.W[f,snrs[j][0]] = 1
				self.Wb[f].append(snrs[j][0])
			for j in self.Wb[f]:
				self.Wf[j].append(f)
		
		c = random.random()
		pcheck = 0.0
		
		for type in self.ftypes:
			self.fdata[f]['type'] = type
			pcheck += self.ftypedata[type]['prob']
			if pcheck > c:
				break
				
		if 'BBprob' in self.ftypedata[self.fdata[f]['type']]:
			BB_check = self.ftypedata[self.fdata[f]['type']]['BBprob']
			m = random.random()
			if m < BB_check:
				self.fdata[f]['toBB'] = 1
				self.F_BB.append(f)
		
		# generate DFG parameters
		db = random.random()
		self.fdata[f]['b_flow'] = db * (self.ftypedata[self.fdata[f]['type']]['bflowubound'] \
			- self.ftypedata[self.fdata[f]['type']]['bflowlbound']) + self.ftypedata[self.fdata[f]['type']]['bflowlbound']
		dl = random.random()
		self.fdata[f]['l_flow'] = dl * (self.ftypedata[self.fdata[f]['type']]['lflowubound'] \
			- self.ftypedata[self.fdata[f]['type']]['lflowlbound']) + self.ftypedata[self.fdata[f]['type']]['lflowlbound']
		dp = random.random()
		self.fdata[f]['p_flow'] = self.fdata[f]['connections'] * (dp * (self.ftypedata[self.fdata[f]['type']]['opubound'] \
			- self.ftypedata[self.fdata[f]['type']]['oplbound']) + self.ftypedata[self.fdata[f]['type']]['oplbound'])
					
	def remFlow(self, f):
		fremindex = ceil(self.fdata[f]['stime'] + self.fdata[f]['duration'])
		self.fremhelp[fremindex].remove(f)
		if len(self.fremhelp[fremindex]) == 0:
			del self.fremhelp[fremindex]
		for i in self.Wb[f]:
			self.W[f,i] = 0
			self.Wf[i].remove(f)
		del self.Wb[f]
		del self.fdata[f]
		self.F.remove(f)
		
	def cleanup(self):
		for n in self.V:
			self.G.node[n]['CLCs'] = []
			self.G.node[n]['pathtoCLC'] = {}
			
		for n in self.C:
			self.G.node[n]['p_rem'] = self.G.node[n]['p_node']
			self.G.node[n]['Proc'] = 0
			self.G.node[n]['ProcCRC'] = {}
			self.G.node[n]['ProcCLC'] = {}
			self.G.node[n]['ProcFlow'] = {}
			self.G.node[n]['CRC'] = None
			self.G.node[n]['isCLC'] = False
			self.G.node[n]['isCRC'] = False
			self.G.node[n]['CLCcontrol'] = []
			self.G.node[n]['CRCcontrol'] = []
			self.G.node[n]['Satisfies'] = []
			self.G.node[n]['CRCpaths'] = {}
			self.G.node[n]['CLCpaths'] = {}
			self.G.node[n]['pathtoCRC'] = None
			self.G.node[n]['pathtoTAP'] = {}
			
		for t in self.T:
			self.G.node[n]['TAPcontrol'] = []

		for e in self.G.edges():
			self.G.edge[e[0]][e[1]]['b_rem'] = self.G.edge[e[0]][e[1]]['b_cap']
			
		for f in self.F:
			self.fdata[f]['isSat'] = False
			self.fdata[f]['CLC'] = None
			self.fdata[f]['hasTAP'] = False   
			self.fdata[f]['TAPpath'] = []
			self.fdata[f]['isGen'] = False
			self.fdata[f]['genstime'] = 0
			
	def load(self):
		return sum(self.fdata[f]['b_flow'] for f in self.F)
		
	def output(self,filename="graph.pdf",legend=False,labelmode="nodes",edgemode="weighted",uniform_color=False,crad=None):
		if labelmode == "flows":
			fcolor= 'w'
		else: 
			fcolor= 'black'
			
		loc = {}
		labellist = {}
		for n in self.V:
			loc[n] = (self.G.node[n]['x'],self.G.node[n]['y'])
			if labelmode == "nodes":
				labellist[n] = str(n)
			else:
				labellist[n] = " "
				
		col = ['w' for n in self.V]
		if uniform_color == False:
			for c in self.C:
				if self.G.node[c]['isCLC']:
					col[c] = '#4bdd54'
					if labelmode == "flows":
						labellist[c] = str(len(self.G.node[c]['Satisfies']))
				elif self.G.node[c]['isCRC']:
					col[c] = 'red'
				else:
					col[c] = '#87CEFA'
		
		bmin = min([self.G[u][v]['b_cap'] for u,v in self.G.edges()])
		if edgemode == "weighted":
			weights = [(self.G[u][v]['b_cap'] / bmin) for u,v in self.G.edges()]
		else:
			weights = [1.0 for u,v in self.G.edges()]
		
		plt.axis('off')
		nodes = nx.draw_networkx_nodes(self.G,pos=loc,node_color=col,labels=labellist,font_size=8,font_color=fcolor,width=weights)
		nodes.set_edgecolor('black')
		nx.draw_networkx_labels(self.G,pos=loc,node_color=col,labels=labellist,font_size=8,font_color=fcolor,width=weights)
		
		if crad is None:
			nx.draw_networkx_edges(self.G,pos=loc,node_color=col,labels=labellist,font_size=8,font_color=fcolor,width=weights)
		else:
			center = (self.dim1 - 1) * self.dist / 2
			circle1 = plt.Circle((center,center), crad, color='0.75', fill=False)
			fig = plt.gcf()
			ax = fig.gca()
			ax.add_artist(circle1)
		
		plt.tight_layout()
		plt.savefig(filename)
		
		if legend:
			plotlines = [plt.scatter(1, 1, s=400, marker='o', facecolor='red', linewidth=1.0),plt.scatter(1, 1, s=400, marker='o', facecolor='#4bdd54', linewidth=1.0),plt.scatter(1, 1, s=400, marker='o', facecolor='#87CEFA', linewidth=1.0)]
			plotlabels = ["RCA","LCA","potential host"]
			F = plt.figure(2)
			F.legend(plotlines, plotlabels, scatterpoints=1, loc='upper left', shadow=False, fancybox=True, prop=FontProperties(size=18), ncol=3)
			bb = Bbox.from_bounds(0, 0, 7.25, 0.65)
			plt.savefig('graph_legend.pdf', bbox_inches=bb)
			
from __future__ import division
import copy

import networkx as nx
from ChModel import *

class CrowdNetwork:

	def __init__(self):
		self.G = nx.Graph()
	
	def generate_from_file(self, filename, modify_controllers=False, contrProb=None):
		
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
			
			if modify_controllers == True and contrProb != None:
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
					self.G.add_node(n, CRC=None, CLCs=[], isCLC=False, isCRC=False, CLCcontrol=[], CRCcontrol=[], Satisfies=[], Proc=0, ProcCRC={}, ProcCLC={}, ProcFlow={}, CRCpaths={}, CLCpaths={}, pathtoCRC=None, pathtoCLC={}, pin='true', style='filled',fillcolor='blue',shape='circle', width=0.2, height=0.2, marker=0)
				else:
					self.G.add_node(n, CLCs=[], pathtoCLC={}, pin='true', style='filled',fillcolor='grey',shape='circle', width=0.2, height=0.2, marker=0)
					
			tmp = fin.readline()
			self.F = [int(n) for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split()]
			self.no_flows = len(self.F)
			self.lastflow = self.no_flows-1
			tmp = fin.readline()
			for n in tmp[tmp.find("=")+2:tmp.find(";")-1].split(" "):
				self.G.add_edge(int(n[n.find("(")+1:n.find(",")]),int(n[n.find(",")+1:n.find(")")]))
			self.no_links = self.G.number_of_edges()

			tmp = fin.readline()
			tmp = fin.readline()
			for i in range(0, self.no_bs):
				tmp = fin.readline().split(" ")
				if int(tmp[0]) in self.C:
					if modify_controllers:
						self.G.node[int(tmp[0])]['p_node'] = 2.e11
					else:
						self.G.node[int(tmp[0])]['p_node'] = float(tmp[1])
					self.G.node[int(tmp[0])]['p_rem'] = self.G.node[int(tmp[0])]['p_node']
				self.G.node[int(tmp[0])]['x'] = float(tmp[2])
				self.G.node[int(tmp[0])]['y'] = float(tmp[3])
				
			tmp = fin.readline()
			tmp = fin.readline()
			for i in range(0, self.no_links):
				tmp = fin.readline().split(" ")
				tmp = fin.readline().split(" ")
				self.G.edge[int(tmp[0])][int(tmp[1])]['b_cap'] = float(tmp[2])
				self.G.edge[int(tmp[0])][int(tmp[1])]['l_cap'] = float(tmp[3])
				self.G.edge[int(tmp[0])][int(tmp[1])]['b_rem'] = self.G.edge[int(tmp[0])][int(tmp[1])]['b_cap']
				
			tmp = fin.readline()
			tmp = fin.readline()
			self.fdata = {}
			for f in self.F:
				tmp = fin.readline().split(" ")
				self.fdata[int(tmp[0])] = {}
				self.fdata[int(tmp[0])]['isSat'] = False
				self.fdata[int(tmp[0])]['CLC'] = None
				self.fdata[int(tmp[0])]['b_flow'] = float(tmp[1])
				self.fdata[int(tmp[0])]['l_flow'] = float(tmp[2])

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
			tmp = fin.readline()
			tmp = fin.readline()

			tmp = fin.readline()
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
				self.fdata[f]['p_flow'] = 4 * self.fdata[f]['b_flow'] * self.fdata[f]['connections']
					
			return True
			
		except:
		
			return False
		
	def copy(self):
		cn = CrowdNetwork()
		cn.__dict__ = copy.deepcopy(self.__dict__)
		
		return cn
		

			
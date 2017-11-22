import networkx as nx
from ComplexNetworkSim import NetworkAgent, Sim
import matplotlib.pyplot as plt
import time,random
import pdb
#pdb.set_trace()

class FlowHelper:

	# Are we trying to find a clc from mine or if it didnt work from any
	MY_CLCS = 0
	ANY_CLCS = 1
	
	# Steps of flow processing
	NEW = 0
	ACCEPTED = 1
	SECOND_REQUEST = 2
	
	def __init__(self, f, Wb):
		self.f = f
		self.step = self.NEW
		self.accepted = {} # nodes which accepted this flow -> time
		self.denied = {} # similar to accepted
		self.requested = {} # nodes a control request has been sent to
		self.search_dist = 0
		self.neighbors = []
		self.searchingIn = self.MY_CLCS
		self.mainNode = min(Wb) # node with lowest ID is mainly responsible for finding a clc
	
	def addAccepted(self, clc, time):
		self.accepted[clc] = time
		if self.step == self.NEW:
			self.step = self.ACCEPTED
	
	def addDenied(self, clc, time):
		self.denied[clc] = time
		
	def addRequested(self, clc, time):
		self.requested[clc] = time
		
	def __repr__(self):
		out = "FlowHelper object for DFG " + str(self.f) + ": Step: " + str(self.step) + ", main node: " + str(self.mainNode) 
		out += ", searchingIn: " + str(self.searchingIn) + ", dist: " + str(self.search_dist) + "\n"
		out += "Requested: " + str(self.requested) + "\n"
		out += "Accepted: " + str(self.accepted) + "\n"
		out += "Denied: " + str(self.denied) + "\n"
		return out

class GreedyFL_Flows(NetworkAgent):

	# Whether the node tries to be a controller or node atm
	COLLECT = 0
	SEARCH = 1
	
	# possible states of a Node
	NodeState = 1
	CLCState = 2
	CRCState = 3
	
	def __init__(self, state, initialiser):
		NetworkAgent.__init__(self, state, initialiser)
		self.time = 0
		self.state = state
		if self.state == self.CRCState:
			# CRC isn't our task
			self.state = self.NodeState
		self.cn = self.globalSharedParameters['cn']
		self.me = self.cn.G.node[self.id]
		self.myFlows = {} # flow -> FlowHelper object. Only contains not yet satisfied flows, which i own
		self.messages = []
		if self.canControl():
			self.step = random.choice([self.SEARCH,self.COLLECT])
		else:
			self.step = self.SEARCH
		self.shortestPaths = self.globalSharedParameters['shortestPaths'][self.id]
		self.endtime = self.globalSharedParameters['simTime']
		self.ConnectForFreePossible = {}
		self.LockPossible = {}
		self.NodeControlRejected = {}
		self.NodeControlRequested = {}
		self.NodeControlUrgentRequested = {}
		self.ControlConfirmationSent = False
		self.CLClog = []
		
		# search distance parameters
		self.max_dist = self.globalSharedParameters['maxDist'][self.id]
		self.host_dist = self.globalSharedParameters['hostDist'][self.id]
		self.search_dist = self.host_dist
		self.neighbors = self.getNeighbourhood(self.search_dist)
		
		# cleanUp parameters
		self.flowInfoTimeout = 50
		self.controlInfoTimeout = 100
		
		# flag for using final message processing
		# prevents validation errors that are only caused by stopping at the wrong time 
		# (e.g. a CLC accepted a node in the last simulation step, then the node will not be able to register that CLC in the next step)
		self.use_final_message_processing = True
		
		# Controller and potential controller specific variables
		if self.canControl():
			self.timeForNextStep = random.randint(0,10) 
			self.timeControlRequest = -1
			self.timeSatRequest = -1
			self.NodeControlUrgent = {}
			self.NodeControlAccepted = []
			self.FlowSatConfirm = []
			# low load parameters/variables
			self.LLlimit = self.globalSharedParameters['LLlimit']
			self.attempt_LL = False
			self.p_attempt_LL = 0.1
			self.timeAttemptLL = -1
			self.TakeOverPossible = {}
			self.cannotTakeWork = {} 
			self.TakeOverRequestsSent = False
			self.TakeOverConfirmationSent = False
			
		# possible resume data
		try:
			self.loadResumeData()
		except:
			pass
			
	def Run(self):

		while True:
			if self.time < self.endtime:
			
				start = time.time()
				
				# possibly start a low load handover attempt
				if self.canControl():
					if self.attempt_LL == False and self.state == self.CLCState and self.me['p_node'] - self.me['p_rem'] <= self.me['p_node']*self.LLlimit \
					and self.timeSatRequest < self.time - 10 and self.timeControlRequest < self.time - 10:
						p = random.random()
						if p < self.p_attempt_LL:
							self.attempt_LL = True
							self.timeAttemptLL = self.time
							self.TakeOverRequestsSent = False
							self.TakeOverConfirmationSent = False
				
				# regular tasks
				self.processMessages()
				if self.canControl():
					# control nodes and flows that accepted my control
					self.acceptNodes()
					if self.timeControlRequest < self.time - 10:
						self.acceptFlows()
				self.updateFlows()
				self.clearOldInformation()
				
				# clear LL attempt if no candidate for take over is found and if the attempt runs for at least 5 rounds
				if self.canControl():
					if self.attempt_LL == True and len(self.TakeOverPossible) == 0 and self.timeAttemptLL < self.time - 5:
						self.attempt_LL = False
				
				# DFG handling after being controlled
				if (self.me['CLCs'] or self.state == self.CLCState):
					self.flowControl()
					self.cleanUpControl()
				
				# low load attempt procedure
				if self.state == self.CLCState:
					self.step = self.COLLECT # of course a node should collect while being CLC
					# -------------------------------------------
					if self.attempt_LL == True and len(self.TakeOverPossible) > 0 and self.TakeOverConfirmationSent == False:
						candidates = list(self.TakeOverPossible.keys())
						candidates.sort(key=lambda c: len(self.getShortestPath(c)))
						n = candidates[0]
						self.send(n, 'Take Over Confirmation')
						self.TakeOverConfirmationSent = True
						del self.TakeOverPossible[n]
					elif self.attempt_LL == True and self.TakeOverRequestsSent == False:
						for n in self.cn.V:
							if n == self.id:
								continue
							if n in self.cn.C and n not in self.cannotTakeWork:
								self.send(n, 'Take Over')
						self.TakeOverRequestsSent = True
				
				# looking for a CLC to control me
				elif not self.me['CLCs']:
					self.handleNodeControl()
			
				self.time += 1
				
				end = time.time()
				self.globalSharedParameters['runtime'][self.id] += end-start
				
				yield Sim.hold, self, NetworkAgent.TIMESTEP_DEFAULT
			
			else: # end of simulation
			
				if self.id == max(self.cn.V): 
					## save state for possible future continuation
					for n in self.cn.V:
						if n <> self.id:
							client = self.getAgent(n)
							client.saveResumeData()
					self.saveResumeData()
					## avoid validation errors because of unprocessed messages of nodes with smaller IDs
					if self.use_final_message_processing == True:
						for n in self.cn.V:
							if n <> self.id:
								client = self.getAgent(n)
								client.processFinalMessages()
						self.processFinalMessages()
			
				yield Sim.passivate, self
				
	def handleNodeControl(self):
		if self.canControl():
			if self.time >= self.timeForNextStep:
				if self.step == self.SEARCH:
					self.step = self.COLLECT
					self.timeForNextStep = random.randint(10, 20) + self.time
				else:
					self.step = self.SEARCH
					self.timeForNextStep = random.randint(10, 20) + self.time

		if self.step == self.SEARCH:
			# if all surrounding potential hosts have rejected, increase searching distance!
			if len(self.NodeControlRejected) == len(self.NodeControlRequested) \
			and len(self.NodeControlRequested) > 0:
				self.search_dist += 1
				self.neighbors = self.getNeighbourhood(self.search_dist)
			
			# send confirmation requests
			if self.ControlConfirmationSent == False:
				if len(self.ConnectForFreePossible) > 0:
					candidates = list(self.ConnectForFreePossible.keys())
					candidates.sort(key=lambda c: len(self.getShortestPath(c)))
					n = candidates[0]
					self.send(n, 'Connect For Free Accept')
					del self.ConnectForFreePossible[n]
					self.ControlConfirmationSent = True
				elif len(self.LockPossible) > 0:
					candidates = list(self.LockPossible.keys())
					candidates.sort(key=lambda c: len(self.getShortestPath(c)))
					n = candidates[0]
					self.send(n, 'Lock Accept')
					del self.LockPossible[n]
					self.ControlConfirmationSent = True 
			
			# send control requests
			remaining_neighbors = [n for n in self.neighbors if n in self.cn.C and n not in self.NodeControlRejected]
			if len(self.ConnectForFreePossible) == 0 and len(self.LockPossible) == 0 and len(remaining_neighbors) == 0:
				if self.canControl():
				# ensure that a potential host without requests does not end up uncontrolled eventually
					self.addNode([self.id])
					self.step = self.COLLECT
				else:
				# else send urgent messages
					for n in self.neighbors:
						if n in self.cn.C and n not in self.NodeControlUrgentRequested:
							self.send(n, 'Node Control Urgent') 
							self.NodeControlUrgentRequested[n] = self.time
			else:	
				# send normal messages (default case)
				for n in self.neighbors:
					if n in self.cn.C and n not in self.NodeControlRequested:
						self.send(n, 'Node Control')
						self.NodeControlRequested[n] = self.time
	
	def updateFlows(self):
		for f in self.cn.Wf[self.id]:
			if not self.cn.fdata[f]['isSat'] and f not in self.myFlows:
				fHelper = FlowHelper(f, self.cn.Wb[f])
				self.myFlows[f] = fHelper
		
		# remove expired flows
		toBeRemoved = []
		for f in self.myFlows.keys():
			if f not in self.cn.Wf[self.id]:
				toBeRemoved.append(f)
		for f in toBeRemoved:
			del self.myFlows[f]
		# remove already satisfied flows
		toBeRemoved = []
		for f in self.myFlows.keys():
			if self.cn.fdata[f]['isSat']:
				toBeRemoved.append(f)
		for f in toBeRemoved:
			del self.myFlows[f]
	
	def flowControl(self): 
		for f in self.myFlows.keys():	
			
			if self.myFlows[f].mainNode <> self.id:
				# for every DFG, there is only one main node responsible for getting it satisfied
				continue
			
			# cleanup older flow information, it might be worth to try again
			toBeDeleted = []
			for clc in self.myFlows[f].accepted.keys():
				if self.myFlows[f].accepted[clc] < self.time - self.flowInfoTimeout:
					toBeDeleted.append(clc)
			for clc in toBeDeleted:
				del self.myFlows[f].accepted[clc]
			if self.myFlows[f].step == self.myFlows[f].ACCEPTED and len(self.myFlows[f].accepted) == 0:
				self.myFlows[f].step = self.myFlows[f].NEW
				
			toBeDeleted = []
			for clc in self.myFlows[f].denied.keys():
				if self.myFlows[f].denied[clc] < self.time - self.flowInfoTimeout:
					toBeDeleted.append(clc)
			for clc in toBeDeleted:
				del self.myFlows[f].denied[clc]
					
			toBeDeleted = []
			for clc in self.myFlows[f].requested.keys():
				if self.myFlows[f].requested[clc] < self.time - self.flowInfoTimeout:
					toBeDeleted.append(clc)
			for clc in toBeDeleted:
				del self.myFlows[f].requested[clc]
			
			# contact CLCs which were not yet queried
			if self.myFlows[f].searchingIn == self.myFlows[f].MY_CLCS:
				for clc in self.me['CLCs']:
					if clc not in self.myFlows[f].requested:
						self.send(clc, 'Flow Control', [f])
						self.myFlows[f].addRequested(clc,self.time)
			elif self.myFlows[f].searchingIn == self.myFlows[f].ANY_CLCS:
				#print str(self.time) + ' ' + str(self.id) + ' looks for CLCs for a flow everywhere now'
				if self.myFlows[f].search_dist == 0:
					self.myFlows[f].search_dist = max(len(self.getShortestPath(c)) for c in self.me['CLCs'])
					self.myFlows[f].neighbors = self.getNeighbourhood(self.myFlows[f].search_dist)

				for n in self.myFlows[f].neighbors:
					if n in self.cn.C and n not in self.myFlows[f].requested:
						self.send(n, 'Flow Control', [f])
						self.myFlows[f].addRequested(n,self.time)
				if len(self.myFlows[f].denied) == len(self.myFlows[f].requested):
					self.myFlows[f].search_dist += 1
					self.myFlows[f].neighbors = self.getNeighbourhood(self.myFlows[f].search_dist)
			
			# all of my CLCs have denied, switch to any CLCs
			if self.myFlows[f].searchingIn == self.myFlows[f].MY_CLCS \
			and len(self.myFlows[f].accepted) == 0 and len(self.myFlows[f].denied) == len(self.me['CLCs']):
				# if i didn't find anything in my clc list, try all nodes in C around me
				self.myFlows[f].step = self.myFlows[f].NEW
				self.myFlows[f].searchingIn = self.myFlows[f].ANY_CLCS
			
			# Flow initially accepted, send confirmation requests
			if self.myFlows[f].step == self.myFlows[f].ACCEPTED:
				if len(self.myFlows[f].accepted) > 0:
					candidates = self.myFlows[f].accepted.keys()
					candidates.sort(key=lambda c: len(self.getShortestPath(c)))
					clc = candidates[0]
					del self.myFlows[f].accepted[clc]
					self.myFlows[f].step = self.myFlows[f].SECOND_REQUEST
					self.send(clc, 'Flow Confirmation Request', [f])
				else:
					self.myFlows[f].step = self.myFlows[f].NEW
					self.myFlows[f].searchingIn = self.myFlows[f].ANY_CLCS
	
	def cleanUpControl(self):
		# if i have multiple clcs, remove those, which control none of my flows
		if len(self.myFlows) > 0:
			# i might have pending flow requests, so better wait before we remove too much
			return
		if len(self.me['CLCs']) > 1:
			toDelete = []
			for clc in self.me['CLCs']:
				if clc == self.id:
					continue
				delete = True
				for f in self.cn.Wf[self.id]:
					if self.cn.fdata[f]['CLC'] == clc:
						delete = False
						break
				
				if delete:
					toDelete.append(clc)
			
			for clc in toDelete:
				if clc == self.id:
					print "Critical error: Never remove CLC control of myself!"
				self.me['CLCs'].remove(clc)
				self.send(clc, 'No Deal')
				if len(self.me['CLCs']) <= 1:
					break # leave at least 1 CLC
	
	def canControl(self):
		return self.id in self.cn.C
	
	def getNeighbourhood(self, distance):
		fulllist = []		
		for v in self.cn.V:
			if len(self.getShortestPath(v)) <= distance + 1:
				fulllist.append(v)
		fulllist.sort(key=lambda v: len(self.getShortestPath(v)))

		return fulllist

	# Communication
	# -------------------------------------------
	def send(self, receiver, message, arguments = None):
		#self.debugOutput('Sending msg to ' + str(receiver), message, arguments)
		client = self.getAgent(receiver)
		client.receive(self.time, self.id, message, arguments)
	
	def receive(self, stime, sender, message, arguments = None):
		#self.debugOutput('Receiving msg from ' + str(sender), message, arguments)
		self.messages.append({'stime': stime, 'sender': sender, 'msg': message, 'args': arguments})
	
	def processMessages(self): 
		mtmp = [m for m in self.messages if m['stime'] < self.time]
		#for msg in self.messages:
		for msg in mtmp:
			sender = msg['sender']
			command = msg['msg']
			args = msg['args']
			stime = msg['stime']
			
			#print str(self.id) + ' (' + str(self.time) + ')' + str(msg)
			#if (self.id in [18,30] or sender in [18,30]) and command[:4] <> 'Flow':
				#print str(self.id) + ' (' + str(self.time) + ')' + str(msg)
			#if command[:4] == 'Flow':
				#if args[0] == 41:
					#print str(self.id) + ' (' + str(self.time) + ')' + str(msg)
			#if command[:4] <> 'Flow':
				#print str(self.id) + ' (' + str(self.time) + ')' + str(msg)
			#if command == 'Node Control Urgent':
				#print str(self.id) + ' (' + str(self.time) + ')' + str(msg)
			
			# Node Control
			# ------------------------------------------------------------------------
			if command == 'Node Control':
				self.timeControlRequest = self.time
				if self.step == self.SEARCH:
					self.send(sender, 'Node Control Reject')
				else:
					path = self.getShortestPath(sender)
					if self.checkCLC(path):
						if self.state == self.CLCState:
							self.send(sender, 'Connect For Free')
						else:
							self.send(sender, 'Lock')
					else:
						self.send(sender, 'Node Control Reject')
						
			if command == 'Node Control Urgent':
				self.timeControlRequest = self.time
				path = self.getShortestPath(sender)
				if self.checkCLC(path):
					if self.state == self.CLCState:
						self.send(sender, 'Connect For Free')
					else:
						self.send(sender, 'Lock')
					self.NodeControlUrgent[sender] = stime
				else:
					self.send(sender, 'Node Control Reject')
			
			if command == 'Connect For Free':
				if not self.me['CLCs'] and not self.state == self.CLCState:
					self.ConnectForFreePossible[sender] = stime
			
			if command == 'Lock':
				if not self.me['CLCs'] and not self.state == self.CLCState:
					self.LockPossible[sender] = stime
			
			if command == 'Connect For Free Accept' or command == 'Lock Accept':
				self.NodeControlAccepted.append(sender)
			
			if command == 'Node Control Accept':
				# a potential host accepted me
				if not sender in self.me['CLCs']:
					self.me['CLCs'].append(sender)
				
			if command == 'Node Control Reject':
				# a potential host rectected me
				if not self.me['CLCs'] and not self.state == self.CLCState:
					self.NodeControlRejected[sender] = stime
				self.ControlConfirmationSent = False
			
			if command == 'No Deal':
				# a node says that it already has another controller
				if len(set(self.cn.Wf[sender]) & set(self.me['Satisfies'])) == 0:
				# check if something happened since the message was sent
					path = self.getShortestPath(sender)
					self.removeNode(path)
				#print str(self.id) + ' removed ' + str(sender)
			
			# ------------------------------------------------------------------------
			# Flow Control
			# ------------------------------------------------------------------------
			
			if command == 'Flow Control':
				# a node asks, whether I can take control over a flow
				self.timeSatRequest = self.time
				if self.checkFlowSat(args[0]):
					self.send(sender, 'Flow Control Possible', args)
				else:
					self.send(sender, 'Flow Control Impossible', args)
			
			if command == 'Flow Control Possible':
				# a node answered that it can take control over the flow
				f = args[0]
				if f in self.myFlows:
					self.myFlows[f].addAccepted(sender, self.time)
			
			if command == 'Flow Control Impossible':
				# a node answered that it cannot take control over the flow
				if args[0] in self.myFlows:
					self.myFlows[args[0]].addDenied(sender, self.time)
			
			if command == 'Flow Confirmation Request':
				f = args[0]
				if self.checkFlowSat(f):
					self.FlowSatConfirm.append((sender,f,sum(len(self.getShortestPath(c)) for c in self.cn.Wb[f]) / len(self.cn.Wb[f])))
				else:
					self.send(sender, 'Flow Control Reject', args)
				
			if command == 'Flow Control Accept':
				if sender not in self.me['CLCs']:
					self.me['CLCs'].append(sender)
			
			if command == 'Flow Control Reject':
				f = args[0]
				if f in self.myFlows:
					self.myFlows[f].addDenied(sender, self.time)
					if len(self.myFlows[f].accepted) > 0:
						self.myFlows[f].step = self.myFlows[f].ACCEPTED
					else:
						self.myFlows[f].step = self.myFlows[f].NEW
				
			# ------------------------------------------------------------------------
			# Reassignment
			# ------------------------------------------------------------------------
				
			if command == 'Take Over':	
				# a CLC requests work to be taken
				if self.state == self.CLCState and self.attempt_LL == False: # TODO: maybe abort LL attempt if other node is less loaded?
					if self.canTakeWork(sender):
						self.send(sender, 'Take Over Possible')
				else:
					self.send(sender, 'Take Over Impossible')
					
			if command == 'Take Over Possible':
				if not sender in self.TakeOverPossible:
					self.TakeOverPossible[sender] = stime
					
			if command == 'Take Over Impossible':
				if not sender in self.cannotTakeWork:
					self.cannotTakeWork[sender] = stime
			
			if command == 'Take Over Confirmation':
				if self.state == self.CLCState and self.attempt_LL == False:
					if self.canTakeWork(sender):
						self.takeWork(sender)
						self.send(sender, 'Take Over Accept')
				else:
					self.send(sender, 'Take Over Reject')
			
			if command == 'Take Over Accept':
				self.giveAwayWork(sender)
				self.attempt_LL = False
				self.TakeOverRequestsSent = False
				self.TakeOverConfirmationSent = False
			
			if command == 'Take Over Reject':
				if sender in self.TakeOverPossible:
					del self.TakeOverPossible[sender]
				if not sender in self.cannotTakeWork:
					self.cannotTakeWork[sender] = stime
				self.TakeOverConfirmationSent = False
					
			if command == 'Took Over Work':
				# a CLC took over work from another CLC
				if not sender in self.me['CLCs']:
					self.me['CLCs'].append(sender)
				if args in self.me['CLCs']:
					self.me['CLCs'].remove(args)
		
			# We don't wanna process old messages in next iteration
			self.messages.remove(msg)
	
	# (simplified) handling of messages at the end of the simulation that could otherwise create validity erros
	# these messages will still be handled correctly in the next iteration
	# the only effect is that all validation errors are prevented, that result from stopping the simulation at the wrong time
	def processFinalMessages(self): 
		relevant_messages = ['Node Control Accept','No Deal','Flow Control Accept','Take Over Accept','Took Over Work']
		mtmp = [m for m in self.messages if m['msg'] in relevant_messages and m['stime'] <= self.endtime]
		for msg in mtmp:
			#print "(Final message) " + str(self.id) + ' (' + str(self.time) + ')' + str(msg)
		
			sender = msg['sender']
			command = msg['msg']
			args = msg['args']
			
			if command == 'Node Control Accept':
				if not sender in self.me['CLCs']:
					self.me['CLCs'].append(sender)

			if command == 'No Deal':
				path = self.getShortestPath(sender)
				self.removeNode(path)
			
			if command == 'Flow Control Accept':
				if sender not in self.me['CLCs']:
					self.me['CLCs'].append(sender)	

			if command == 'Take Over Accept':
				self.giveAwayWork(sender)
					
			if command == 'Took Over Work':
				# a CLC took over work from another CLC
				if not sender in self.me['CLCs']:
					self.me['CLCs'].append(sender)
				if args in self.me['CLCs']:
					self.me['CLCs'].remove(args)
					
	def acceptNodes(self):
		# potential hosts can reject node control if they are currently searching or attemping handover. But for urgent requests they should still accept.
		if ((self.state <> self.CLCState and self.step == self.SEARCH) \
		or (self.state <> self.CLCState and self.attempt_LL == True)) \
		and len([n for n in self.NodeControlAccepted if n in self.NodeControlUrgent]) == 0:
			for n in self.NodeControlAccepted:
				self.send(n, 'Node Control Reject')
		else:
			self.NodeControlAccepted.sort(key=lambda c: len(self.getShortestPath(c)))
			for n in self.NodeControlAccepted:
				if n not in self.me['CLCcontrol']:
					path = self.getShortestPath(n)
					if self.checkCLC(path):
						self.send(n, 'Node Control Accept')
						self.addNode(path)
				else:
					self.send(n, 'Node Control Reject')
				
		del self.NodeControlAccepted[:]
		
	def acceptFlows(self):
		self.FlowSatConfirm.sort(key=lambda fs: fs[2])
		for fs in self.FlowSatConfirm:
			n = fs[0]
			f = fs[1]
			if self.checkFlowSat(f) and self.attempt_LL == False:
				self.addFlow(f)
				self.globalSharedParameters['flowsSat'] += 1
				for k in self.cn.Wb[f]:
					self.send(k, 'Flow Control Accept', [f])
			else:
				self.send(n, 'Flow Control Reject', [f])
				
		del self.FlowSatConfirm[:]
	
	# Helpers
	# -------------------------------------------
	
	def getShortestPath(self, node):
		if node not in self.shortestPaths:
			self.shortestPaths[node] = nx.shortest_path(self.cn.G, source = self.id, target = node)
		
		return self.shortestPaths[node]
	
	def addNode(self, path):
		self.state = self.CLCState
		procLoad = self.cn.p_CLC/(self.cn.l_CLC - sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in xrange(0,len(path)-1)))
		self.me['p_rem'] -= procLoad
		for i in xrange(0, len(path)-1):
			self.cn.G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.b_CLC
		self.me['ProcCLC'][path[-1]] = procLoad
		self.me['CLCcontrol'].append(path[-1])
		self.me['CLCpaths'][path[-1]] = path
		self.me['isCLC'] = True
		if not self.id in self.me['CLCs']:
			self.me['CLCs'].append(self.id)
		if not self.id in self.me['CLCcontrol']:
			self.addNode([self.id])
	
	def removeNode(self, path):
		if path[-1] not in self.me['CLCcontrol']:
			return
		self.me['p_rem'] += self.cn.p_CLC/(self.cn.l_CLC - sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in xrange(0,len(path)-1)))
		if self.me['p_rem'] > self.me['p_node']:
			self.me['p_rem'] = self.me['p_node']
		for i in xrange(0, len(path)-1):
			self.cn.G.edge[path[i]][path[i+1]]['b_rem'] += self.cn.b_CLC
		self.me['ProcCLC'][path[-1]] = 0
		self.me['CLCcontrol'].remove(path[-1])
	
	def addFlow(self, f):
		self.state = self.CLCState
		self.cn.fdata[f]['isSat'] = True
		self.cn.fdata[f]['CLC'] = self.id
		self.me['isCLC'] = True
		self.me['Satisfies'].append(f)
		maxLatency = 0
		for k in self.cn.Wb[f]:
			path = self.getShortestPath(k)
			if k not in self.me['CLCcontrol']:
				self.addNode(path)
			curLatency = 0
			for i in range(0, len(path)-1):
				curLatency += self.cn.G.edge[path[i]][path[i+1]]['l_cap']
				self.cn.G.edge[path[i]][path[i+1]]['b_rem'] -= self.cn.fdata[f]['b_flow']
			if curLatency > maxLatency:
				maxLatency = curLatency
		self.me['p_rem'] -= self.cn.fdata[f]['p_flow']/(self.cn.fdata[f]['l_flow'] - maxLatency)
		self.me['ProcFlow'][f] = self.cn.fdata[f]['p_flow']/(self.cn.fdata[f]['l_flow'] - maxLatency)
		
	#------------------------------------------------------------------------
	
	# checks if a certain CLC control can be established
	def checkCLC(self, path):
		for i in range(0,len(path)-1):
			if self.cn.G.edge[path[i]][path[i+1]]['b_rem'] < self.cn.b_CLC:
				return False
		
		procLoad = self.cn.p_CLC/(self.cn.l_CLC - sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)))
		if self.me['p_rem'] - procLoad < 0:
			return False
		
		return True
		
	# checks if a flow f can be satisfied by a controller v
	def checkFlowSat(self, f):
		if f not in self.cn.F:
			# the flow has expired meanwhile
			return False
		if self.cn.fdata[f]['isSat'] == True:
			# if the flow is already controlled, return false, so the controller doesn't try anymore
			return False
		
		potRem = self.me['p_rem']
		potEdgeLoad = {}
		
		maxLatency = 0
		for k in self.cn.Wb[f]:
			# First calculate potential load after node control
			path = self.getShortestPath(k)
			if k not in self.me['CLCcontrol']:
				potRem -= self.cn.p_CLC/(self.cn.l_CLC - sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)))
				for i in range(0, len(path)-1):
					if path[i] not in potEdgeLoad:
						potEdgeLoad[path[i]] = {}
					if path[i+1] not in potEdgeLoad[path[i]]:
						potEdgeLoad[path[i]][path[i+1]] = 0
					potEdgeLoad[path[i]][path[i+1]] += self.cn.b_CLC
					if self.cn.G.edge[path[i]][path[i+1]]['b_rem'] - potEdgeLoad[path[i]][path[i+1]] < 0:
						return False

			# second calculate potential load after flow control		
			curLatency = 0
			for i in range(0, len(path)-1):	
				curLatency += 2*self.cn.G.edge[path[i]][path[i+1]]['l_cap']
				if path[i] not in potEdgeLoad:
					potEdgeLoad[path[i]] = {}
				if path[i+1] not in potEdgeLoad[path[i]]:
					potEdgeLoad[path[i]][path[i+1]] = 0
				potEdgeLoad[path[i]][path[i+1]] += self.cn.fdata[f]['b_flow']
				if self.cn.G.edge[path[i]][path[i+1]]['b_rem'] - potEdgeLoad[path[i]][path[i+1]] < 0:
					return False
			if curLatency > maxLatency:
				maxLatency = curLatency
		
		potRem -= self.cn.fdata[f]['p_flow']/(self.cn.fdata[f]['l_flow'] - maxLatency)
		
		# now check, if potential load is too high
		if potRem < 0:
			return False
		
		return True
	
	#------------------------------------------------------------------------

	def canTakeWork(self, node):
		client = self.getAgent(node)
		
		potRem = self.me['p_rem']
		potEdgeLoad = {}
			
		# first calculate load for node and for edges
		for n in client.me['CLCcontrol']:
			if n not in self.me['CLCcontrol']:
				path = self.getShortestPath(n)
				for i in range(0, len(path)-1):	
					if path[i] not in potEdgeLoad:
						potEdgeLoad[path[i]] = {}
					if path[i+1] not in potEdgeLoad[path[i]]:
						potEdgeLoad[path[i]][path[i+1]] = 0
					potEdgeLoad[path[i]][path[i+1]] += self.cn.b_CLC
				procLoad = self.cn.p_CLC/(self.cn.l_CLC - sum(2*self.cn.G.edge[path[i]][path[i+1]]['l_cap'] for i in range(0,len(path)-1)))
				potRem -= procLoad
					
		for f in client.me['Satisfies']:
			maxLatency = 0
			for k in self.cn.Wb[f]:
				path = self.getShortestPath(k)		
				curLatency = 0
				for i in range(0, len(path)-1):	
					curLatency += 2*self.cn.G.edge[path[i]][path[i+1]]['l_cap']
					if path[i] not in potEdgeLoad:
						potEdgeLoad[path[i]] = {}
					if path[i+1] not in potEdgeLoad[path[i]]:
						potEdgeLoad[path[i]][path[i+1]] = 0
					potEdgeLoad[path[i]][path[i+1]] += self.cn.fdata[f]['b_flow']
				if curLatency > maxLatency:
					maxLatency = curLatency
			procLoad = self.cn.fdata[f]['p_flow']/(self.cn.fdata[f]['l_flow'] - maxLatency)
			potRem -= procLoad
			
		# consider no longer used link capacity
		for n in client.me['CLCcontrol']:
			path = client.me['CLCpaths'][n]
			for i in range(0, len(path)-1):
				if path[i] in potEdgeLoad:
					if path[i+1] in potEdgeLoad[path[i]]:
						potEdgeLoad[path[i]][path[i+1]] -= self.cn.b_CLC
		for f in client.me['Satisfies']:
			for n in self.cn.Wb[f]:
				path = client.me['CLCpaths'][n]
				for i in range(0, len(path)-1):
					if path[i] in potEdgeLoad:
						if path[i+1] in potEdgeLoad[path[i]]:
							potEdgeLoad[path[i]][path[i+1]] -= self.cn.fdata[f]['b_flow']
							
		# check if node and edges can support additional load					
		if potRem < 0:
			return False
		for i in potEdgeLoad:
			for j in potEdgeLoad[i]:
				if potEdgeLoad[i][j] > self.cn.G.edge[i][j]['b_rem']:
					return False
		
		return True
	
	def giveAwayWork(self, node):
		self.state = self.NodeState
		self.me['isCLC'] = False
		self.me['p_rem'] = self.me['p_node']
		if not node in self.me['CLCs']:
			self.me['CLCs'].append(node)
		self.me['Satisfies'] = []
		self.me['CLCcontrol'] = []
		self.me['ProcCLC'] = {}
		self.me['ProcFlow'] = {}
		self.me['CLCpaths'] = {}
	
	def takeWork(self, node):
		#print str(self.time) + ' ' + str(self.id) + ' took work of ' + str(node)
		client = self.getAgent(node)
		for n in client.me['CLCcontrol']:
			path = client.me['CLCpaths'][n]
			for i in range(0, len(path)-1):
				self.cn.G.edge[path[i]][path[i+1]]['b_rem'] += self.cn.b_CLC
		for f in client.me['Satisfies']:
			for n in self.cn.Wb[f]:
				path = client.me['CLCpaths'][n]
				for i in range(0, len(path)-1):
					self.cn.G.edge[path[i]][path[i+1]]['b_rem'] += self.cn.fdata[f]['b_flow']
		
		if node not in self.me['CLCcontrol']:
			path = self.getShortestPath(node)
			self.addNode(path)
		for n in client.me['CLCcontrol']:
			if n not in self.me['CLCcontrol']:
				path = self.getShortestPath(n)
				self.addNode(path)
			self.send(n, 'Took Over Work', node) # send to all. Otherwise, it would be a problem if a node rejects that CLC at the same time.
		for f in client.me['Satisfies']:
			self.addFlow(f)
	
	# -------------------------------------------
	
	def debugOutput(self, prefix, message, arguments = None):
		debugMsg = prefix + ' saying: ' + message + '['
		if arguments != None:
			for a in arguments:
				debugMsg += str(a) + ', '
			if debugMsg.endswith(', '):
				debugMsg = debugMsg[0: -2]
		debugMsg += ']'
		print str(self.time) + ' ' + str(self.id) + ' says: ' + debugMsg
			

	# -------------------------------------------
	
	def clearOldInformation(self):
		self.controlInfoTimeout = 100
		for i in list(self.ConnectForFreePossible.keys()):
			if self.ConnectForFreePossible[i] < self.time - self.controlInfoTimeout:
				del self.ConnectForFreePossible[i]
		for i in list(self.LockPossible.keys()):
			if self.LockPossible[i] < self.time - self.controlInfoTimeout:
				del self.LockPossible[i]
		for i in list(self.NodeControlRejected.keys()):
			if self.NodeControlRejected[i] < self.time - self.controlInfoTimeout:
				del self.NodeControlRejected[i]
		for i in list(self.NodeControlRequested.keys()):
			if self.NodeControlRequested[i] < self.time - self.controlInfoTimeout:
				del self.NodeControlRequested[i]
		for i in list(self.NodeControlUrgentRequested.keys()):
			if self.NodeControlUrgentRequested[i] < self.time - self.controlInfoTimeout:
				del self.NodeControlUrgentRequested[i]
				
		if self.canControl():
			for i in list(self.NodeControlUrgent.keys()):
				if self.NodeControlUrgent[i] < self.time - self.controlInfoTimeout:
					del self.NodeControlUrgent[i]
			for i in list(self.TakeOverPossible.keys()):
				if self.TakeOverPossible[i] < self.time - self.controlInfoTimeout:
					del self.TakeOverPossible[i]
			for i in list(self.cannotTakeWork.keys()):
				if self.cannotTakeWork[i] < self.time - self.controlInfoTimeout:
					del self.cannotTakeWork[i]
	
	def saveResumeData(self):
		self.globalSharedParameters['resumeData'][self.id] = {}
		
		self.globalSharedParameters['resumeData'][self.id]['Flows'] = dict(self.myFlows)
		self.globalSharedParameters['resumeData'][self.id]['messages'] = list(self.messages)
		self.globalSharedParameters['resumeData'][self.id]['step'] = self.step
		self.globalSharedParameters['resumeData'][self.id]['searchDist'] = self.search_dist
		self.globalSharedParameters['resumeData'][self.id]['ConnectForFreePossible'] = dict(self.ConnectForFreePossible)
		self.globalSharedParameters['resumeData'][self.id]['LockPossible'] = dict(self.LockPossible)
		self.globalSharedParameters['resumeData'][self.id]['NodeControlRejected'] = dict(self.NodeControlRejected)
		self.globalSharedParameters['resumeData'][self.id]['NodeControlRequested'] = dict(self.NodeControlRequested)
		self.globalSharedParameters['resumeData'][self.id]['NodeControlUrgentRequested'] = dict(self.NodeControlUrgentRequested)
		
		if self.canControl():
			self.globalSharedParameters['resumeData'][self.id]['timeForNextStep'] = self.timeForNextStep - self.endtime
			self.globalSharedParameters['resumeData'][self.id]['timeControlRequest'] = self.timeControlRequest - self.endtime
			self.globalSharedParameters['resumeData'][self.id]['timeSatRequest'] = self.timeSatRequest - self.endtime
			self.globalSharedParameters['resumeData'][self.id]['NodeControlUrgent'] = dict(self.NodeControlUrgent)
			self.globalSharedParameters['resumeData'][self.id]['NodeControlAccepted'] = list(self.NodeControlAccepted)
			self.globalSharedParameters['resumeData'][self.id]['FlowSatConfirm'] = list(self.FlowSatConfirm)
			self.globalSharedParameters['resumeData'][self.id]['attempt_LL'] = self.attempt_LL
			self.globalSharedParameters['resumeData'][self.id]['timeAttemptLL'] = self.timeAttemptLL - self.endtime
			self.globalSharedParameters['resumeData'][self.id]['TakeOverPossible'] = dict(self.TakeOverPossible)
			self.globalSharedParameters['resumeData'][self.id]['cannotTakeWork'] = dict(self.cannotTakeWork)
			self.globalSharedParameters['resumeData'][self.id]['TakeOverRequestsSent'] = self.TakeOverRequestsSent
			self.globalSharedParameters['resumeData'][self.id]['TakeOverConfirmationSent'] = self.TakeOverConfirmationSent
			
		for f in self.globalSharedParameters['resumeData'][self.id]['Flows']:
			for k in self.globalSharedParameters['resumeData'][self.id]['Flows'][f].accepted:
				self.globalSharedParameters['resumeData'][self.id]['Flows'][f].accepted[k] -= self.endtime
			for k in self.globalSharedParameters['resumeData'][self.id]['Flows'][f].denied:
				self.globalSharedParameters['resumeData'][self.id]['Flows'][f].denied[k] -= self.endtime
			for k in self.globalSharedParameters['resumeData'][self.id]['Flows'][f].requested:
				self.globalSharedParameters['resumeData'][self.id]['Flows'][f].requested[k] -= self.endtime
				
		for m in self.globalSharedParameters['resumeData'][self.id]['messages']:
			m['stime'] -= self.endtime
		
		if self.canControl():
			to_be_adjusted = ['ConnectForFreePossible','LockPossible','NodeControlRejected','NodeControlRequested','NodeControlUrgentRequested','NodeControlUrgent','TakeOverPossible','cannotTakeWork']
		else:
			to_be_adjusted = ['ConnectForFreePossible','LockPossible','NodeControlRejected','NodeControlRequested','NodeControlUrgentRequested']
			
		for attr in to_be_adjusted:
			for k in self.globalSharedParameters['resumeData'][self.id][attr]:
				self.globalSharedParameters['resumeData'][self.id][attr][k] -= self.endtime
				
	def loadResumeData(self):
		self.myFlows = self.globalSharedParameters['resumeData'][self.id]['Flows']
		self.messages = self.globalSharedParameters['resumeData'][self.id]['messages']
		self.step = self.globalSharedParameters['resumeData'][self.id]['step']
		self.search_dist = self.globalSharedParameters['resumeData'][self.id]['searchDist']
		self.ConnectForFreePossible = self.globalSharedParameters['resumeData'][self.id]['ConnectForFreePossible']
		self.LockPossible = self.globalSharedParameters['resumeData'][self.id]['LockPossible']
		self.NodeControlRejected = self.globalSharedParameters['resumeData'][self.id]['NodeControlRejected']
		self.NodeControlRequested = self.globalSharedParameters['resumeData'][self.id]['NodeControlRequested']
		self.NodeControlUrgentRequested = self.globalSharedParameters['resumeData'][self.id]['NodeControlUrgentRequested']
		
		if self.canControl():
			self.timeForNextStep = self.globalSharedParameters['resumeData'][self.id]['timeForNextStep']
			self.timeControlRequest = self.globalSharedParameters['resumeData'][self.id]['timeControlRequest']
			self.timeSatRequest = self.globalSharedParameters['resumeData'][self.id]['timeSatRequest']
			self.NodeControlUrgent = self.globalSharedParameters['resumeData'][self.id]['NodeControlUrgent']
			self.NodeControlAccepted = self.globalSharedParameters['resumeData'][self.id]['NodeControlAccepted']
			self.FlowSatConfirm = self.globalSharedParameters['resumeData'][self.id]['FlowSatConfirm']
			self.cannotTakeWork = self.globalSharedParameters['resumeData'][self.id]['cannotTakeWork']
			self.attempt_LL = self.globalSharedParameters['resumeData'][self.id]['attempt_LL']
			self.timeAttemptLL = self.globalSharedParameters['resumeData'][self.id]['timeAttemptLL']
			self.TakeOverPossible = self.globalSharedParameters['resumeData'][self.id]['TakeOverPossible']
			self.TakeOverRequestsSent = self.globalSharedParameters['resumeData'][self.id]['TakeOverRequestsSent']
			self.TakeOverConfirmationSent = self.globalSharedParameters['resumeData'][self.id]['TakeOverConfirmationSent']
		
		# in case of dynamic operation it might happen that a DFG that was not satisfied in a
		# (possibly very short) execution run has already expired in the next execution run
		# such DFGs have to be removed from the resume data to prevent errors
		# ftmp = [f for f in self.myFlows if not f in self.cn.Wf[self.id]]
		# for f in ftmp: 
			# del self.myFlows[f]
		# mtmp = [m for m in self.messages if m['msg'][:4] == 'Flow']
		# for m in mtmp:
			# f = m['args'][0]
			# if not f in self.cn.F:
				# self.messages.remove(m)
		# if self.canControl():
			# ftmp = [f for f in self.FlowSatConfirm if not f in self.cn.F]
			# for f in ftmp:
				# self.FlowSatConfirm.remove(f)
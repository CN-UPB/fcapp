from __future__ import division 
from coopr.pyomo import *

model = AbstractModel()

############################################################################
##### relevant entities: 

# set of nodes (WiFi APs, LTE BSs, routers/switches)
model.V = Set()
# set of nodes that can serve as controller (CRC or CLC) 
model.C = Set(within=model.V)
# Set of links
# Note: links are unidirectional! 
model.E = Set (within=model.V*model.V) 
# flows connected to at least one node in the network
model.F = Set() 

######################################################################
# input parameters: 

#################
## for nodes: 

# how much processing capacity is there per controller to execute control and flow processing? 
model.p_node = Param(model.V, within=NonNegativeReals) #p_node in TeX
# a node needs a certain capacity to its CLC
model.b_CLC = Param(within=NonNegativeReals)
# a CLC needs a certain capacity to its CRC
model.b_CRC = Param(within=NonNegativeReals)
# a node needs a certain roundtrip latency to its CLC
model.l_CLC = Param(within=NonNegativeReals)
# a CLC needs a certain roundtrip latency to its CRC
model.l_CRC = Param(within=NonNegativeReals)
# a node requires a certain processing capacity at its CLC
model.p_CLC = Param(within=NonNegativeReals)
# a CLC requires a certain processing capacity at its CRC
model.p_CRC = Param(within=NonNegativeReals)


##################
## for links: 

# maximum data rate
model.b_cap = Param(model.E, within=NonNegativeReals)
# latency
model.l_cap = Param(model.E, within=NonNegativeReals) 

#################
## for flows: 

# a flow has a data rate over the WIRELESS link to each node it is connected to, this rate needs to be carried through the network 
# with a certain latency and needs a certain processing capacity at a controller
model.W = Param(model.F, model.V, within=Binary)
model.b_flow = Param(model.F, within=NonNegativeReals) 
model.l_flow = Param(model.F, within=NonNegativeReals) 

def pflowHelp (m, x):
	return 4 * m.b_flow[x] * sum(m.W[x,v] for v in m.V)

model.p_flow = Param(model.F, within=NonNegativeReals, initialize=pflowHelp) 

################
## misc

model.bigM = Param(mutable=True)

#######################################################################

### auxilliary variables, to make counting easier: 

model.NumSats = Var()
model.NumCLCs = Var()
model.NumCRCs = Var()
model.isCLC = Var (model.C, within=Binary) 
model.isCRC = Var (model.C, within=Binary) 
model.isSat = Var (model.F, within=Binary) 
model.Proc = Var (model.C, within=NonNegativeReals)

# decision variables 

# for each basestation, we need to find one or multiple CLC, each one has to satisfy constraints 
model.CLC = Var(model.C, model.V, within=Binary)
# for each basestation, we need to find exactly one CRC 
model.CRC = Var(model.C, model.C, within=Binary)
# for each flow, there should be a CLC controlling all the nodes it is connected to being able to process it
model.Sat = Var(model.C, model.F, within=Binary)
# routing variables (nodes to CLC)
model.f = Var (model.C, model.V, model.E, within=Binary)
# routing variables (nodes to CLC)
model.g = Var (model.C, model.C, model.E, within=Binary)  

#misc stuff that is irrelevant for this MIQCP but needs to be here for compatibility reasons
try:
	model.bx = Param(model.V)
	model.by = Param(model.V)
	model.fx = Param(model.F)
	model.fy = Param(model.F)
	model.dist = Param()
	model.dim1 = Param()
	model.dim2 = Param()
except:
	pass

###################################################################
# constraints 

# node to CLC routing constraints
def routeCLCstartHelp (m, c, d):
	if (c != d):
		return sum(m.f[c, d, v, w] for (v,w) in m.E if v == c) == m.CLC[c, d]
	else:
		return Constraint.Skip
		
model.routeCLCstart = Constraint (model.C, model.V, rule = routeCLCstartHelp)
model.routeCLCstart2 = Constraint (model.C, model.V, rule = lambda m, c, d: sum(m.f[c, d, v, w] for (v, w) in m.E if w == c) == 0)

def routeCLCendHelp (m, c, d):
	if (c != d):
		return sum(m.f[c, d, v, w] for (v,w) in m.E if w == d) == m.CLC[c, d]
	else:
		return Constraint.Skip

model.routeCLCend = Constraint (model.C, model.V, rule = routeCLCendHelp)
model.routeCLCend2 = Constraint (model.C, model.V, rule = lambda m, c, d: sum(m.f[c, d, v, w] for (v, w) in m.E if v == d) == 0)

def routeCLCinOutHelp (m, c, d, v):
	if (c != d and c != v and d != v):
		return sum(m.f[c, d, u, w] for (u,w) in m.E if (w == v)) == sum(m.f[c, d, u, w] for (u,w) in m.E if (u == v))
	else:
		return Constraint.Skip
	
model.routeCLCinOut = Constraint (model.C, model.V, model.V, rule = routeCLCinOutHelp)
	
# CLC to CRC routing constraints
def routeCRCstartHelp (m, c, d):
	if (c != d):
		return sum(m.g[c, d, v, w] for (v,w) in m.E if v == c) == m.CRC[c, d] * m.isCLC[d]
	else:
		return Constraint.Skip
		
model.routeCRCstart = Constraint (model.C, model.C, rule = routeCRCstartHelp)
model.routeCRCstart2 = Constraint (model.C, model.C, rule = lambda m, c, d: sum(m.g[c, d, v, w] for (v, w) in m.E if w == c) == 0)

def routeCRCendHelp (m, c, d):
	if (c != d):
		return sum(m.g[c, d, v, w] for (v,w) in m.E if w == d) == m.CRC[c, d] * m.isCLC[d]
	else:
		return Constraint.Skip

model.routeCRCend = Constraint (model.C, model.C, rule = routeCRCendHelp)
model.routeCRCend2 = Constraint (model.C, model.C, rule = lambda m, c, d: sum(m.g[c, d, v, w] for (v, w) in m.E if v == d) == 0)

def routeCRCinOutHelp (m, c, d, v):
	if c != d and c != v and d != v:
		return sum(m.g[c, d, u, w] for (u,w) in m.E if (w == v)) == sum(m.g[c, d, u, w] for (u,w) in m.E if (u == v))
	else:
		return Constraint.Skip
	
model.routeCRCinOut = Constraint (model.C, model.C, model.V, rule = routeCRCinOutHelp)
	
# Requiring controllers: each node needs at least one CLC and each CLC needs exactly one CRC
model.requireCLC = Constraint (model.V, rule = lambda m, v: sum(m.CLC[c,v] for c in m.C) >= 1)
model.requireCRC = Constraint (model.C, rule = lambda m, d: sum(m.CRC[c,d] for c in m.C) == m.isCLC[d])	

# Activate controllers
model.CLCused1 = Constraint (model.C, rule = lambda m, c: m.bigM * m.isCLC[c] >= sum(m.CLC[c,v] for v in m.V))
model.CRCused1 = Constraint (model.C, rule = lambda m, c: m.bigM * m.isCRC[c] >= sum(m.CRC[c,d] for d in m.C))

# Flow constraints: every flow should have a controller being able to process it properly
model.CLCsatisfiesFlow = Constraint (model.C, model.F, rule = lambda m, c, x: m.bigM * (m.Sat[c,x] - 1) <= sum((m.CLC[c,v] - 1) * m.W[x,v] for v in m.V))
model.oneCLCperFlow = Constraint (model.F, rule = lambda m, x: sum(m.Sat[c,x] for c in m.C) <= 1)
model.flowSatisfied = Constraint (model.F, rule = lambda m, x: m.isSat[x] == sum(m.Sat[c,x] for c in m.C))

## Data rate constraints
# make sure that the maximum data rate of each link is not exceeded
model.dataRateLinks = Constraint (model.E, rule = lambda m, v, w: sum(m.f[c,d,v,w] * (m.b_CLC + sum(m.W[x,d] * m.Sat[c,x] * m.b_flow[x] for x in m.F)) for c in m.C for d in m.V) \
																	+ sum(m.g[c,d,v,w] * m.b_CRC for c in m.C for d in m.C) \
																	+ sum(m.f[c,d,w,v] * (m.b_CLC + sum(m.W[x,d] * m.Sat[c,x] * m.b_flow[x] for x in m.F)) for c in m.C for d in m.V) \
																	+ sum(m.g[c,d,w,v] * m.b_CRC for c in m.C for d in m.C) <= (m.b_cap[v,w]+m.b_cap[w,v])/2)
 
## Latency constraints
# summing up the processing time that is needed at a controller
model.procCapSum = Constraint (model.C, rule = lambda m, c: m.Proc[c] == sum(m.Sat[c,x] for x in m.F) + sum(m.CLC[c,d] for d in m.V) + sum(m.CRC[c,d] for d in m.C))

# latency constraint for flows

def latencyFlowsHelp (m, c, d, x):
	if m.W[x,d] == 1:
		return sum(m.f[c,d,v,w] * (m.l_cap[v,w] + m.l_cap[w,v]) for (v,w) in m.E) + m.Proc[c] * m.p_flow[x] / m.p_node[c] <= m.l_flow[x] + m.bigM * (1 - m.Sat[c,x])
	else:
		return Constraint.Skip
		
model.latencyFlows = Constraint (model.C, model.V, model.F, rule = latencyFlowsHelp)

# lantency constraint for CLCs
model.latencyCLCs = Constraint (model.C, model.V, rule = lambda m, c, d: sum(m.f[c,d,v,w] * (m.l_cap[v,w] + m.l_cap[w,v]) for (v,w) in m.E) + m.Proc[c]*m.p_CLC/m.p_node[c] <= m.l_CLC + m.bigM * (1 - m.CLC[c,d]))
# lantency constraint for CRCs
model.latencyCRCs = Constraint (model.C, model.C, rule = lambda m, c, d: sum(m.g[c,d,v,w] * (m.l_cap[v,w] + m.l_cap[w,v]) for (v,w) in m.E) + m.Proc[c]*m.p_CRC/m.p_node[c] <= m.l_CRC + m.bigM * (1 - m.CRC[c,d]))

################################################################
# Loop and corner case constraints
model.loopsCLC = Constraint (model.C, model.V, model.E, rule = lambda m, c, d, v, w: m.f[c,d,v,w] + m.f[c,d,w,v] <= 1)
model.loopsCRC = Constraint (model.C, model.C, model.E, rule = lambda m, c, d, v, w: m.g[c,d,v,w] + m.g[c,d,w,v] <= 1)
model.selfCLC = Constraint (model.C, rule = lambda m, c: m.CLC[c,c] == m.isCLC[c])
model.selfCRC = Constraint (model.C, rule = lambda m, c: m.CRC[c,c] == m.isCRC[c]*m.isCLC[c])

################################################################
# counting variables for evaluation
model.ConNumSats = Constraint (rule = lambda m: m.NumSats == sum(m.isSat[x] for x in m.F))
model.ConNumCLCs = Constraint (rule = lambda m: m.NumCLCs == sum(m.isCLC[c] for c in m.C))
model.ConNumCRCs = Constraint (rule = lambda m: m.NumCRCs == sum(m.isCRC[c] for c in m.C))

################################################################
# objective 

## simple: minimize number of active controllers 

model.ObjectiveFunction = Objective (rule = lambda m: sum(m.isCRC[c] for c in m.C) + sum(m.isCLC[c] for c in m.C) \
													- sum(3 for c in m.C) * sum(m.isSat[x] for x in m.F))
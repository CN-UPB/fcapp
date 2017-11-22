from __future__ import division
from time import *
from math import exp,sqrt,pow
from ChModel import *
import sys, random, os

ft_file = {"CoMP": "flowtypes_CoMP.csv", "generic": "flowtypes_new.csv"}

def distance(x1,y1,x2,y2):
	return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))
	
def signum(x):
	if x == 0:
		return 0
	else:
		return x/abs(x)
		
def scal_prod((a,b),(c,d)):
	return a*c + b*d

class Basestation:
	pass
class Link:
	pass
class Flow:
	pass

# initialize

try: 
	dim = int(sys.argv[1])
except:
	print("Error: dimension missing!")
	exit(1)
	
if dim <= 2:
	print("Error: dimension for ring must be greater than 2!")
	exit(1)
	
no_bs = dim * dim

try:
	no_flows = int(sys.argv[2])
except:
	no_flows = no_bs
	
try: 
	instance = str(sys.argv[3])
except:
	instance = str(time())

try:
	if not os.path.exists(os.path.dirname(instance)):
		os.makedirs(os.path.dirname(instance))
except:
	pass
	
dist = 1000.0
sdev = 0.125
contrProb = 0.6
evalscen = "generic"
random.seed()

while True:
	no_links = 0
	BSs = []
	Links = []
	Flows = []
	W = [[0 for x in xrange(no_bs)] for x in xrange(no_flows)]

	# generate nodes

	for i in range(0, dim):
		for j in range(0, dim):
			
			bs = Basestation()
			bs.name = i * dim + j
			bs.index = i * dim + j
			bs.neighbors = [(i+a) * dim + (j+b) for a in [-1,0,1] for b in [-1,0,1] if (i+a) in range(0, dim) and (j+b) in range(0, dim) and (a,b) <> (0,0)]
			
			c = random.random()
			if c < contrProb:
				bs.isContr = 1
			else:
				bs.isContr = 0			
				
			bs.p_node = 2.0e11
			bs.x = i * dist + random.gauss(0,dist*sdev)
			bs.y = j * dist + random.gauss(0,dist*sdev)
			
			bs.isConnected = 0
			
			BSs.append(bs)
			
	# generate edges
	## determine ring center and radius
	center = (dim - 1) * dist / 2
	rad = sum(distance(bs.x,bs.y,center,center) for bs in BSs) / dim / dim
	
	## create metro ring
	tmp = range(0,no_bs)
	tmp.sort(key=lambda k: abs(distance(BSs[k].x,BSs[k].y,center,center) - rad))
	first_ring_index = tmp[0]
	BSs[first_ring_index].isConnected = 1
	curr_node = first_ring_index
	ring_completed = False
	can_close_ring = False
	
	while ring_completed == False:
		if can_close_ring == True and first_ring_index in BSs[curr_node].neighbors:
			tmp = [first_ring_index]
		else:
			# prevent going in the wrong direction
			grad = -1 * (BSs[curr_node].x - center) / (BSs[curr_node].y - center)
			(a,b) = (signum(BSs[curr_node].y - center), grad*signum(BSs[curr_node].y - center))
			tmp = [k for k in BSs[curr_node].neighbors if BSs[k].isConnected == 0 and scal_prod((a,b),(BSs[k].x-BSs[curr_node].x,BSs[k].y-BSs[curr_node].y)) >= 0]
			tmp.sort(key=lambda k: abs(distance(BSs[k].x,BSs[k].y,center,center) - rad))	
		
		l1 = Link()
		l2 = Link()
		l1.start = curr_node
		l1.end = tmp[0]
		l2.start = tmp[0]
		l2.end = curr_node
		l1.b_cap = 5e9
		l2.b_cap = 5e9
		l1.l_cap = distance(BSs[tmp[0]].x,BSs[tmp[0]].y,BSs[curr_node].x,BSs[curr_node].y) * 1.45 / 299792458.0
		l2.l_cap = distance(BSs[tmp[0]].x,BSs[tmp[0]].y,BSs[curr_node].x,BSs[curr_node].y) * 1.45 / 299792458.0
		Links.append(l1)
		Links.append(l2)
		no_links = no_links + 2
		BSs[tmp[0]].isConnected = 1
		curr_node = tmp[0]
		if first_ring_index not in BSs[curr_node].neighbors:
			can_close_ring = True
		if curr_node == first_ring_index:
			ring_completed = True
		
	## connect all other nodes	
	ring_nodes = [v.index for v in BSs if v.isConnected == 1]
	for v in ring_nodes:
		BSs[v].ring_dist = 0
	other_nodes = [v.index for v in BSs if v.isConnected == 0]
	other_nodes.sort(key=lambda k: min([distance(BSs[k].x,BSs[k].y,BSs[v].x,BSs[v].y) for v in ring_nodes]))
	
	for l in other_nodes:
		tmp = []
		for k in [v.index for v in BSs if v.isConnected == 1 and v.name in BSs[l].neighbors]:
			tmp.append((k,l,distance(BSs[k].x,BSs[k].y,BSs[l].x,BSs[l].y),BSs[k].ring_dist))
				
		tmp.sort(key=lambda t: t[2]*sqrt(max(0.5,t[3])))
		l1 = Link()
		l2 = Link()
		l1.start = tmp[0][0]
		l1.end = tmp[0][1]
		l2.start = tmp[0][1]
		l2.end = tmp[0][0]
		l1.b_cap = 2.5e9
		l2.b_cap = 2.5e9
		l1.l_cap = tmp[0][2] * 1.45 / 299792458.0
		l2.l_cap = tmp[0][2] * 1.45 / 299792458.0
		Links.append(l1)
		Links.append(l2)
		no_links = no_links + 2
		BSs[tmp[0][1]].isConnected = 1
		BSs[tmp[0][1]].ring_dist = BSs[tmp[0][0]].ring_dist + 1
				
	if sum(bs.isConnected for bs in BSs) == no_bs:
		break
	else:
		print "Warning: Graph not connected!"
			
# generate flows

# load flow type parameters
ftypes = []
ftypedata = {}
fin = open(ft_file[evalscen], "r")
attributes = [att.translate(None, ' \n\t\r') for att in fin.readline().split(";")]
while True:
	try:
		tmp = fin.readline().split(";")
		if len(tmp[0]) == 0:
			break
		ftypes.append(tmp[0])
		ftypedata[tmp[0]] = {}
		for i,att in enumerate(attributes[1:],start=1):
			ftypedata[tmp[0]][att] = float(tmp[i])
	except:
		break

if sum(ftypedata[type]['prob'] for type in ftypes) < 0.999 or sum(ftypedata[type]['prob'] for type in ftypes) > 1.001:
	print("ERROR: flow probabilities don't sum up to 1.0!")
	exit(1)

for i in range(0, no_flows):

	f = Flow()
	f.name = i
	f.index = i
	sinr_insufficient = True
	
	while (sinr_insufficient):
		f.x = random.uniform(-dist, dim * dist)
		f.y = random.uniform(-dist, dim * dist)
		f.connections = 0
		
		rspw = []
		for bs in BSs:
			s = sqrt(pow(bs.x - f.x, 2) + pow(bs.y - f.y, 2))
			rspw.append([bs,received_signal_power_watts(s),s])
			
		rspw.sort(key=lambda rspw: rspw[1], reverse=True)
		
		wattsum = rspw[0][1]
		f.connections += 1
		# SINR threshold = 0.0 dB (formerly -7.5 dB)
		while (sinr(rspw, f.connections, no_bs) < 0.0 and f.connections < min(3, no_bs)):
			f.connections += 1
		
		if (sinr(rspw, f.connections, no_bs) >= 0.0):
			sinr_insufficient = False
			
	for j in range(0, f.connections):
		W[i][rspw[j][0].index] = 1
		
	c = random.random()
	pcheck = 0.0
	
	for type in ftypes:
		f.type = type
		pcheck += ftypedata[type]['prob']
		if pcheck > c:
			break
	
	# generate DFG parameters
	db = random.random()
	f.b_flow = db * (ftypedata[f.type]['bflowubound'] - ftypedata[f.type]['bflowlbound']) + ftypedata[f.type]['bflowlbound']
	dl = random.random()
	f.l_flow = dl * (ftypedata[f.type]['lflowubound'] - ftypedata[f.type]['lflowlbound']) + ftypedata[f.type]['lflowlbound']
	dp = random.random()
	f.p_flow = f.connections * (dp * (ftypedata[f.type]['opubound'] - ftypedata[f.type]['oplbound']) + ftypedata[f.type]['oplbound'])
	
	Flows.append(f)

# generate output
	
fout = open(instance, "w")	
fout.write("set V := ")
for bs in BSs:
	fout.write(str(bs.name) + " ")
fout.write(";\n")

fout.write("set C := ")
for bs in BSs:
	if bs.isContr == 1:
		fout.write(str(bs.name) + " ")
fout.write(";\n")

fout.write("set F := ")
for f in Flows:
	fout.write(str(f.name) + " ")
fout.write(";\n")

fout.write("set E := ")
for l in Links:
	fout.write("(" + str(l.start) + "," + str(l.end) + ") ")
fout.write(";\n\n")

fout.write("param : p_node bx by :=\n")
for bs in BSs:
	if bs.isContr == 1:
		fout.write(str(bs.name) + " " + str(bs.p_node) + " " + str(bs.x) + " " + str(bs.y) + "\n")
	else: 
		fout.write(str(bs.name) + " 0 " + str(bs.x) + " " + str(bs.y) + "\n")
fout.write(";\n")

fout.write("param : b_cap l_cap :=\n")
for l in Links:
	fout.write(str(l.start) + " " + str(l.end) + " " + str(l.b_cap) + " " + str(l.l_cap) + "\n")
fout.write(";\n")

fout.write("param : b_flow l_flow p_flow fx fy :=\n")
for f in Flows:
	fout.write(str(f.name) + " " + str(f.b_flow) + " " + str(f.l_flow) + " " + str(f.p_flow) + " " + str(f.x) + " " + str(f.y) + "\n")
fout.write(";\n")

fout.write("param : b_CLC := 1e5 ;\n")
fout.write("param : b_CRC := 1e5 ;\n")
fout.write("param : l_CLC := 1e-3 ;\n")
fout.write("param : l_CRC := 1e-2 ;\n")
fout.write("param : p_CLC := 1e6 ;\n")
fout.write("param : p_CRC := 1e6 ;\n")
fout.write("\n")
fout.write("param : bigM := 1e10 ;\n")
fout.write("\n")
fout.write("param : dist := " + str(dist) + " ;\n")
fout.write("param : dim1 := " + str(dim) + " ;\n")
fout.write("param : dim2 := " + str(dim) + " ;\n")

fout.write("\n")
fout.write("param : W :=\n")
for f in Flows:
	for bs in BSs:
		fout.write(str(f.name) + " " + str(bs.name) + " " + str(W[f.index][bs.index]) + "\n")
fout.write(";\n")
		
fout.close()

print "Generated: " + instance + " (" + str(len([c for c in BSs	if c.isContr == 1])) + " nodes in C)"
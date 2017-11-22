from __future__ import division
from time import *
from math import exp,sqrt,pow
from ChModel import *
import sys, random, os

ft_file = {"CoMP": "flowtypes_CoMP.csv", "generic": "flowtypes_new.csv"}

class Basestation:
	pass
class Link:
	pass
class Flow:
	pass

# initialize

try: 
	dim1 = int(sys.argv[1])
except:
	print("Error: dimension missing!")
	exit(1)
	
try: 
	dim2 = int(sys.argv[2])
except:
	dim2 = dim1
	
no_bs = dim1 * dim2

try:
	no_flows = int(sys.argv[3])
except:
	no_flows = no_bs
	
try: 
	instance = str(sys.argv[4])
except:
	instance = str(time())

try:
	if not os.path.exists(os.path.dirname(instance)):
		os.makedirs(os.path.dirname(instance))
except:
	pass
	
dist = 1000.0
sdev = 0.125
contrProb = 1.0
r_con = 1.5
evalscen = "generic"
random.seed()

while True:
	no_links = 0
	BSs = []
	Links = []
	Flows = []
	W = [[0 for x in xrange(no_bs)] for x in xrange(no_flows)]

	# generate nodes

	for i in range(0, dim1):
		for j in range(0, dim2):
			
			bs = Basestation()
			bs.name = i * dim2 + j
			bs.index = i * dim2 + j
			
			c = random.random()
			if c < contrProb:
				bs.isContr = 1
			else:
				bs.isContr = 0			
				
			bs.p_node = 2.0e5
			bs.x = i * dist + random.gauss(0,dist*sdev)
			bs.y = j * dist + random.gauss(0,dist*sdev)
			
			bs.isConnected = 0
			
			BSs.append(bs)
			
	# generate edges
			
	for k in range(0, no_bs):
		for l in range(k, no_bs):                                                                                                                                                                                                       
		
			s = sqrt(pow(BSs[k].x - BSs[l].x, 2) + pow(BSs[k].y - BSs[l].y, 2))
			
			if k != l and s < r_con * dist:
				l1 = Link()
				l2 = Link()
				l1.start = k
				l1.end = l
				l2.start = l
				l2.end = k
				l1.b_cap = 2.5e3
				l2.b_cap = 2.5e3
				l1.l_cap = s * 1.45 / 299792458.0
				l2.l_cap = s * 1.45 / 299792458.0
				Links.append(l1)
				Links.append(l2)
				no_links = no_links + 2
				BSs[k].isConnected = 1
				BSs[l].isConnected = 1
				
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
		f.x = random.uniform(-dist, dim1 * dist)
		f.y = random.uniform(-dist, dim2 * dist)
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
	f.b_flow *= 1.0e-6
	dl = random.random()
	f.l_flow = dl * (ftypedata[f.type]['lflowubound'] - ftypedata[f.type]['lflowlbound']) + ftypedata[f.type]['lflowlbound']
	dp = random.random()
	f.p_flow = f.connections * (dp * (ftypedata[f.type]['opubound'] - ftypedata[f.type]['oplbound']) + ftypedata[f.type]['oplbound'])
	f.p_flow *= 1.0e-6
	
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

fout.write("param : b_CLC := 0.1 ;\n")
fout.write("param : b_CRC := 0.1 ;\n")
fout.write("param : l_CLC := 1e-3 ;\n")
fout.write("param : l_CRC := 1e-2 ;\n")
fout.write("param : p_CLC := 1.0 ;\n")
fout.write("param : p_CRC := 1.0 ;\n")
fout.write("\n")
fout.write("param : bigM := 1e10 ;\n")
fout.write("\n")
fout.write("param : dist := " + str(dist) + " ;\n")
fout.write("param : dim1 := " + str(dim1) + " ;\n")
fout.write("param : dim2 := " + str(dim2) + " ;\n")

fout.write("\n")
fout.write("param : W :=\n")
for f in Flows:
	for bs in BSs:
		fout.write(str(f.name) + " " + str(bs.name) + " " + str(W[f.index][bs.index]) + "\n")
fout.write(";\n")
		
fout.close()

print "Generated: " + instance + " (" + str(len([c for c in BSs	if c.isContr == 1])) + " nodes in C)"
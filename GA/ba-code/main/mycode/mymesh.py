from __future__ import division
from math import sqrt, pow

from existing_code.ChModel import *
from constants import *
from mycode import settings
from mycode.settings import config
from mycode.utilf import println


def create(fout, dim1, dim2, no_flows):
	no_bs = dim1 * dim2

	class Basestation:
		pass

	class Link:
		pass

	class Flow:
		pass

	dist = 1000.0
	sdev = 0.125
	r_con = 1.5
	SingleConnectionFlowprocessing = True

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
				if c < config.CONTROLLER_PROB:
					bs.isContr = 1
				else:
					bs.isContr = 0

				bs.p_node = config.DEFAULT_P_NODE
				bs.x = i * dist + random.gauss(0, dist * sdev)
				bs.y = j * dist + random.gauss(0, dist * sdev)

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
					l1.b_cap = 2.5e9
					l2.b_cap = 2.5e9
					l1.l_cap = s * 1.45 / 299792458.0
					l2.l_cap = s * 1.45 / 299792458.0
					Links.append(l1)
					Links.append(l2)
					no_links = no_links + 2
					BSs[k].isConnected = 1
					BSs[l].isConnected = 1

		if sum(bs.isConnected for bs in BSs) == no_bs:
			break
		# else:
		# 	println("Warning: Graph not connected!")

	# generate flows

	ftypes = []
	ftypedata = {}
	fin = open("../flowtypes.csv", "r")
	tmp = fin.readline()
	while True:
		try:
			tmp = fin.readline().split(";")
			if len(tmp[0]) == 0:
				break
			ftypes.append(tmp[0])
			ftypedata[tmp[0]] = {}
			ftypedata[tmp[0]]['prob'] = float(tmp[1])
			ftypedata[tmp[0]]['bflowlbound'] = float(tmp[2])
			ftypedata[tmp[0]]['bflowubound'] = float(tmp[3])
			ftypedata[tmp[0]]['lflow'] = float(tmp[4])
		except:
			break

	if sum(ftypedata[type]['prob'] for type in ftypes) < 0.999 or sum(
			ftypedata[type]['prob'] for type in ftypes) > 1.001:
		println("ERROR: flow probabilities don't sum up to 1.0!")
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
				rspw.append([bs, received_signal_power_watts(s), s])

			rspw.sort(key=lambda rspw: rspw[1], reverse=True)

			wattsum = rspw[0][1]
			f.connections += 1
			while (sinr(rspw, f.connections, no_bs) < -7.5 and f.connections < min(3, no_bs)):
				f.connections += 1

			if (sinr(rspw, f.connections, no_bs) >= -7.5):
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

		d = random.random()
		f.b_flow = (d * (ftypedata[f.type]['bflowubound'] - ftypedata[f.type]['bflowlbound']) + ftypedata[f.type][
			'bflowlbound'])
		f.l_flow = ftypedata[f.type]['lflow']

		Flows.append(f)

	# generate output

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
		if SingleConnectionFlowprocessing or f.connections > 1:
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

	if True or no_flows > 0:
		if SingleConnectionFlowprocessing or sum(f.connections for f in Flows) > no_flows:
			fout.write("param : b_flow l_flow fx fy :=\n")
			for f in Flows:
				if SingleConnectionFlowprocessing or f.connections > 1:
					fout.write(str(f.name) + " " + str(f.b_flow) + " " + str(f.l_flow) + " " + str(f.x) + " " + str(
						f.y) + "\n")
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
	fout.write("param : dim1 := " + str(dim1) + " ;\n")
	fout.write("param : dim2 := " + str(dim2) + " ;\n")

	if no_flows > 0:
		if SingleConnectionFlowprocessing or sum(f.connections for f in Flows) > no_flows:
			fout.write("\n")
			fout.write("param : W :=\n")
			for f in Flows:
				if SingleConnectionFlowprocessing or f.connections > 1:
					for bs in BSs:
						fout.write(str(f.name) + " " + str(bs.name) + " " + str(W[f.index][bs.index]) + "\n")
			fout.write(";\n")

if __name__ == "__main__":
	for dim in 10,:
		for numFlows in range(100,1100,100):
			for counter in range(48):
				fout = open("/home/swante/tmpb/networks/{}-{}-{}".format(dim, numFlows, counter), "w")
				create(fout, dim, dim, no_flows=numFlows)

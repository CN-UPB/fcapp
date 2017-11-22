from __future__ import division
import sys
import math
#from pprint import pprint

import pylab as P

from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties

from collections import defaultdict

from ci import calc_sample_mean

manual_input = False
instances_path = {"ldf": "Results_ldf/ESvsPS", "mdf": "Results/ESvsPS"}
plot_path = "plots_ldf/ES"
outputlabel = "es"

labels = {}
labels["nodes"] = "Number of nodes" 
labels["flows"] = "Number of DFGs" 
labels["RCAs"] = "Number of RCAs used" 
labels["LCAs"] = "Number of LCAs used" 
labels["Sats"] = "DFGs satisfied (%)" 
labels["rt"] = "Average runtime (s)" 
labels["Flex_es"] = "GreedyFCAPA"
labels["Flex_es_mdf"] = "GreedyFCAPA (MDF)"
labels["Flex_es_ldf"] = "GreedyFCAPA (LDF)"

results = {}
no_nodes = []
Properties = []
#Properties = ["Flex_es"]
xupper = 6010

inputfiles = []
tests = [51,52]
obj = ["LCAs"]#,"rt","Sats"]	

if manual_input:
	for i in xrange(1,len(sys.argv)):
		inputfiles.append(sys.argv[i])
	Properties = []
else:
	for t in tests:
		for p in ["Flex_es"]:
			for k in ["ldf","mdf"]:
				inputfiles.append(instances_path[k] + "\_Results_test_" + str(t) + "_" + p + ".dat")

for i in inputfiles:
	fin = open(i, "r")
	tmp = fin.readline().split(" ")
	n = int(tmp[0])
	if not n in no_nodes:
		no_nodes.append(n)
	no_inst = int(tmp[1])
	flow_mult = int(tmp[2])
	if i[:len(instances_path["ldf"])] == instances_path["ldf"]:
		prop = str(tmp[3]) + "_ldf"
	else:
		prop = str(tmp[3]) + "_mdf"
	if not prop in Properties:
		Properties.append(prop)
	while True:
		tmp = fin.readline().split(" ")
		try:
			if tmp[1] <> "timelimit":
				r = {}
				r["nodes"] = n
				r["flows"] = int(math.ceil(int(tmp[0]) / no_inst) * flow_mult)
				r["prop"] = prop
				r["RCAs"] = float(tmp[1])
				r["LCAs"] = float(tmp[2])
				r["Sats"] = float(tmp[3]) / r["flows"]
				r["rt"] = float(tmp[4])
				counter = len(results)
				results[counter] = r
		except:
			break

for p in Properties:
	for n in no_nodes:
		labels[(p,n)] = labels[p][:-1] + ", " + str(n) + " nodes)"
			
for o in obj:
			
	x_label = "Number of DFGs"
	y_label = labels[o]

	lines = []
	for n in no_nodes:
		for p in Properties:
			lines.append((n,o,p))

	plotdata = {}
	plotconfidence = {}
	xaxis = {}

	xvalues = range(1,xupper)

	for l in lines:
		print l
		di = []
		ci = []
		xaxis[l] = []
		for x in xvalues:
			values = []
			for r in results:
				if l[0] == results[r]["nodes"] and x == results[r]["flows"] and l[2] == results[r]["prop"]:
					values.append(results[r][l[1]])
			if len(values) > 20:
				#print "ISAMPLES",x,l,len(values)
				#print "IVALUES",x,l,values
				(xd,xc) = calc_sample_mean(values, 0.95)
				xaxis[l].append(x)
				di.append(xd)
				ci.append(xc)
			# else:
				# print "ISAMPLES",x,l,len(values),"!!!"
				# if len(values) > 0:
					# (xd,xc) = (values[0],0)
			
				
		plotdata[l] = di
		plotconfidence[l] = ci

	#colors = ['#FF0000','#00FF00','#0000FF','#FFFF00','#FF00FF','#00FFFF','#800000','#008000','#000080','#808000','#800080','#008080','#808080','#FFFFFF']
	markers = ['^','*','o','v']

	font = FontProperties(size=20)
	font_smaller = FontProperties(size=16)
	
	curr_xaxis = range(1,xupper)
	for k in lines:
		curr_xaxis = sorted(list(set(curr_xaxis).intersection(set(xaxis[k]))))

	F = P.figure()
	AX1 = F.add_subplot(111)
	plotlines = []
	plotlabels = []
	for i,l in enumerate(lines):
		#pl = AX1.plot(xaxis, plotdata[l], label=l, lw=2,markersize=12)
		pl = AX1.errorbar(curr_xaxis, plotdata[l][0:len(curr_xaxis)], yerr=plotconfidence[l][0:len(curr_xaxis)], label=(l), lw=2, marker=markers[i], markersize=12, elinewidth=2,ls="--")
		#pl = AX1.errorbar([x for x in xaxis[l]], plotdata[l], yerr=plotconfidence[l], label=(l), lw=2, markersize=12, elinewidth=2, color=colors[i], marker=markers[i],markevery=(i,3))
		plotlines.append(pl[0])
		plotlabels.append(labels[(l[2],l[0])]) 
		#plotlabels.append("Algorithm ({0} GBps/WL)".format(l[0]/1e9))
		#plotlabels.append("Algorithm (d={0} GBps)".format(l[3]/1e9))
		#pl = AX1.errorbar([x for x in xaxis], plotdata[(l,"i")], yerr=plotconfidence[(l,"i")], label=(l,"i"), lw=2, markersize=12, elinewidth=2,ls="--", color=colors[i], marker=markers[i],markevery=(i,3))
		#plotlines.append(pl[0])
		#plotlabels.append((l,"i"))
		#plotlabels.append("ILP Solver ({0} GBps/WL)".format(l[0]/1e9))
		#plotlabels.append("Optimization (d={0} GBps)".format(l[3]/1e9))
	#AX1.hlines([4.515,3.69],-1,21, colors='#606060', linestyles='dotted')
	#AX1.axhline(4.515,color='#606060', linestyle='--',lw=2)
	#AX1.axhline(3.69,color='#606060', linestyle='--',lw=2)
	#AX1.axhline(1.77,color='#606060', linestyle='--',lw=2)
	AX1.set_xlabel(x_label, fontproperties=font)
	AX1.set_ylabel(y_label, fontproperties=font)
	AX1.set_xlim(0, max(curr_xaxis)+10)
	if o == "Sats":
		AX1.set_ylim(0,1.1)
	#elif o == "rt":
		#AX1.set_ylim(0,2)
	#elif o == "LCAs":
		#AX1.set_ylim(0,25)
	#AX1.set_yscale('log')
	for tick in AX1.xaxis.get_major_ticks():
		tick.label1.set_fontsize(16)
	for tick in AX1.yaxis.get_major_ticks():
		tick.label1.set_fontsize(16)
	#AX1.legend()
	P.savefig(plot_path + '/plot_' + l[1] + '_' + str(outputlabel) + '.pdf', bbox_inches='tight')
	#P.savefig(plot_path + '/plot_es_fcfs_' + l[1] + '_' + str(l[0]) + '_nodes.pdf', bbox_inches='tight')
	F = P.figure(2)
	F.legend(plotlines, plotlabels, loc='upper left', shadow=False, fancybox=True, prop=font_smaller, ncol=1)
	bb = Bbox.from_bounds(0, 0, 12.8, 3.4)
	#bb = Bbox.from_bounds(0, 0, 6.4, 3.4)
	#bb = Bbox.from_bounds(0, 0, 6.4, 4)
	P.savefig(plot_path + '/plot_legend_' + str(outputlabel) + '.pdf', bbox_inches=bb)

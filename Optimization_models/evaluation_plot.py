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
#output_path = 'plots/ES'
#output_path = 'plots/ESvsPS'
#output_path = 'plots/BB'
#output_path = 'plots/CoMP'
#output_path = 'plots/ES_ldf'
#output_path = 'plots/ESvsPS_ldf'
#output_path = 'plots/BB_ldf'
#output_path = 'plots/CoMP_ldf'
output_path = 'plots/PS_for_presentation'

labels = {}
labels["nodes"] = "Number of nodes" 
labels["flows"] = "Number of DFGs" 
labels["RCAs"] = "Number of RCAs used" 
#labels["LCAs"] = "Number of LCAs used" 
labels["LCAs"] = "Average number of LCAs used" 
labels["Sats"] = "DFGs satisfied (%)" 
#labels["avg"] = "Average flow satisfaction" 
labels["rt"] = "Average runtime (s)"
#labels["Flex_es"] = "GreedyFCAPA (MDF)"
#labels["Flex_es_ldf"] = "GreedyFCAPA (LDF)"
labels["Flex_es"] = "GreedyFCAPA$_{es}$ (MDF)"
labels["Flex_es_ldf"] = "GreedyFCAPA$_{es}$ (LDF)"
#labels["Flex_fcfs"] = "GreedyFCAPA$_{ps}$ (MDF)"
#labels["Flex_fcfs_ldf"] = "GreedyFCAPA$_{ps}$ (LDF)"
#labels["Flex_fcfs"] = "FlexCAPF ($P_{BB}$ = 0.0)"
#labels["Flex_fcfs_ldf"] = "FlexCAPF ($P_{BB}$ = 0.0)"
labels["Flex_fcfs"] = "FlexCAPF"
#labels["Flex_fcfs_ldf"] = "FlexCAPF"
labels["Flex_fcfs_ldf"] = "GreedyFCAPA"
labels["es"] = "OPT$_{es}$"
#labels["fcfs"] = "OPT$_{ps}$"
#labels["fcfs"] = "OPT$_{BB}$ ($P_{BB}$ = 0.0)"
labels["fcfs"] = "Opt. model"

for lbb in [0.0,2.5,5.0]:
	prop = "fcfs_BB_" + str(lbb)
	labels[prop] = "OPT$_{BB}$ ($P_{BB}$ = 1.0, $l_{BB}$ = " + str(lbb) + "ms)"
	labels["Flex_" + prop] = "FlexCAPF ($P_{BB}$ = 1.0, $l_{BB}$ = " + str(lbb) + "ms)"
	labels["Flex_" + prop + "_ldf"] = "FlexCAPF ($P_{BB}$ = 1.0, $l_{BB}$ = " + str(lbb) + "ms)"

results = {}
xvals = {}
no_nodes = []
indeces = {}
#opt_props = ["es"] 
#opt_props = ["es","fcfs"]
#opt_props = ["fcfs", "fcfs_BB_0.0", "fcfs_BB_2.5", "fcfs_BB_5.0"]
opt_props = ["fcfs"]
#Properties = opt_props + ["Flex_" + p for p in opt_props]
#Properties = opt_props + ["Flex_" + p for p in opt_props] + ["Flex_" + p + "_ldf" for p in opt_props]
Properties = opt_props + ["Flex_" + p + "_ldf" for p in opt_props]
obj = ["rt","LCAs","Sats"]		

inputfiles = []
#tests = [91,92]
tests = [101,102] 
#tests = [111,112] 

x_lim = {4: 1601, 9: 801}
legend_loc = {"LCAs": 'lower right', "rt": 'upper left', "Sats": 'lower left'}

if manual_input:
	for i in xrange(1,len(sys.argv)):
		inputfiles.append(sys.argv[i])
	Properties = []
else:
	for t in tests:
		for p in Properties:
			inputfiles.append("Instances/_Results_test_" + str(t) + "_" + p + ".dat")

for i in inputfiles:
	fin = open(i, "r")
	tmp = fin.readline().split(" ")
	n = int(tmp[0])
	if not n in results:
		results[n] = {}
		xvals[n] = []
		indeces[n] = {}
		no_nodes.append(n)
	no_inst = int(tmp[1])
	flow_mult = int(tmp[2])
	prop = str(tmp[3])
	if not prop in indeces[n]:
		indeces[n][prop] = []
	while True:
		tmp = fin.readline().split(" ")
		try:
			if tmp[1] == "None":
				continue
			r = {}
			index = int(tmp[0])
			if prop[-4:] == "_ldf":
				tmpprop = prop[:-4]
			else:
				tmpprop = prop
			if tmpprop[:4] == "Flex" and index not in indeces[n][tmpprop[5:]]:
				continue
			r["index"] = index
			r["nodes"] = n
			flows = int(math.ceil(index / no_inst) * flow_mult)
			if prop[:4] == "fcfs" and flows > x_lim[n]:
				continue
			indeces[n][prop].append(index)
			r["flows"] = flows
			if not flows in xvals[n]:
				xvals[n].append(flows)
			r["prop"] = prop
			r["RCAs"] = float(tmp[1])
			r["LCAs"] = float(tmp[2])
			r["Sats"] = float(tmp[3]) / r["flows"]
			r["rt"] = float(tmp[4])
			counter = len(results[n])
			results[n][counter] = r
		except:
			break
			
# for n in no_nodes:
	# for p in Properties:
		# s = sum(r["RCAs"] for r in results if r["nodes"] == n and r["prop"] == p)/sum(1 for r in results if r["nodes"] == n and r["prop"] == p)
		# print str(p) + " (" + str(n) + "nodes): " + str(s) + " RCAs"
		# if len([r["index"] for r in results if r["nodes"] == n and r["prop"] == p and r["RCAs"] > 1.0 + 1e-6]) > 0:
			# print [r["index"] for r in results if r["nodes"] == n and r["prop"] == p and r["RCAs"] > 1.0 + 1e-6]
			
# for n in no_nodes:
	# for p in [p for p in Properties]:# if p[:4] <> "Flex"]:
		# print "Consistency check for " + str(p) + " (" + str(n) + "nodes, " + str(len([r for r in results[n].values() if r["prop"] == p])) + " results):"
		# for r in results[n].values():
			# if r["prop"] == p:
				# for s in results[n].values():
					# if s["prop"] == "Flex_" + p and r["index"] == s["index"]:
						# if r["RCAs"] > s["RCAs"] + 1e-4:
							# print "RCA fail: " + str(r["index"])
						# if r["LCAs"] > s["LCAs"] + 1e-4:
							# print "LCA fail: " + str(r["index"])
						# #if s["LCAs"] - r["LCAs"] > 1 + 1e-4:
							# #print "Heuristic fail: " + str(r["index"])
						# if r["Sats"] < s["Sats"] - 1e-4:
							# print "Sat fail: " + str(r["index"])

#exit(1)

colors = ['#FF0000','#00FF00','#0000FF','#FF00FF','#00FFFF','#800000','#008000','#000080','#808000','#800080','#008080','#808080','#FFFFFF','#FFFF00']
markers = ['^','*','o','v', '<', '>', '8', 's', 'p', 'h', 'H', 'D', 'd', 'P', 'X']
font = FontProperties(size=20)
font_smaller = FontProperties(size=16)

for n in no_nodes:
	for o in obj:
				
		x_label = "Number of DFGs"
		y_label = labels[o]

		lines = []
		for p in Properties:
			lines.append((n,o,p))

		plotdata = {}
		plotconfidence = {}
		xaxis = {}

		xvalues = xvals[n]
		xvalues.sort()

		for l in lines:
			print l
			di = []
			ci = []
			xaxis[l] = []
			for x in xvalues:
				values = []
				for r in results[n].values():
					if l[0] == r["nodes"] and x == r["flows"] and l[2] == r["prop"]:
						values.append(r[l[1]])
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
		
		curr_xaxis = range(0,x_lim[n]+1)
		for k in lines:
			curr_xaxis = sorted(list(set(curr_xaxis).intersection(set(xaxis[k]))))

		F = P.figure()
		AX1 = F.add_subplot(111)
		plotlines = []
		plotlabels = []
		for i,l in enumerate(lines):
			#pl = AX1.plot(xaxis, plotdata[l], label=l, lw=2,markersize=12)
			pl = AX1.errorbar(xaxis[l], plotdata[l][0:len(xaxis[l])], yerr=plotconfidence[l][0:len(xaxis[l])], label=(l), lw=2, marker=markers[i], color=colors[i], markersize=6, elinewidth=2,ls="--")
			#pl = AX1.errorbar([x for x in xaxis[l]], plotdata[l], yerr=plotconfidence[l], label=(l), lw=2, markersize=12, elinewidth=2, color=colors[i], marker=markers[i],markevery=(i,3))
			plotlines.append(pl[0])
			plotlabels.append(labels[l[2]]) #+ " (" + str(l[0]) + " nodes)")
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
		#AX1.xaxis.set_ticks([i*20 for i in range(0,11)])
		#AX1.set_xlim(0, max(curr_xaxis)+10)
		AX1.set_xlim(0, max([max(xaxis[l]) for l in lines])+10)
		if l[1] == "rt":
			AX1.set_yscale('log')
		for tick in AX1.xaxis.get_major_ticks():
			tick.label1.set_fontsize(16)
		for tick in AX1.yaxis.get_major_ticks():
			tick.label1.set_fontsize(16)
		#AX1.legend()
		P.legend(plotlines, plotlabels, loc='best', shadow=False, prop=font_smaller, ncol=1)
		P.savefig(output_path + '/plot_' + l[1] + '_' + str(l[0]) + '_nodes.pdf', bbox_inches='tight')
		#F = P.figure(2)
		#F.legend(plotlines, plotlabels, shadow=False, fancybox=True, prop=font_smaller)#, ncol=2) , loc='upper left'
		#bb = Bbox.from_bounds(0, 0, 6.4, 4)
		#P.savefig(output_path + '/plot_legend.pdf', bbox_inches='tight')

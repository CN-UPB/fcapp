#!/usr/bin/env python
from __future__ import division
import sys
import os
import fnmatch
import re
import traceback
import random
import math

import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt

def loadlevel(i,scaling=1):  # time i is provided in seconds, scaling if necessary, default is 1
    i = 24 * (i / 3600) % 24  # switch from seconds to day time
    if i <= 3:
        return 0.9 * (-1 / 27 * math.pow(i, 2) + 1) * scaling
    elif i <= 6:
        return 0.9 * (1 / 27 * math.pow(i - 6, 2) + 1 / 3) * scaling
    elif i <= 15:
        return 0.9 * (1 / 243 * math.pow(i - 6, 2) + 1 / 3) * scaling
    else:
        return 0.9 * (-1 / 243 * math.pow(i - 24, 2) + 1) * scaling

use_realtime = True

obj = ["#Satisfied","#CRCs","#CLCs","#CLCDiff","#nodeDiff","#flowDiff","CRCpathlength","CLCpathlength","CLCload","controlRatio","runtime", "netmodtime", "realtime"]

class TrafficDistribution:
	def __init__(self, logDir,network,scenario):
		self.LogDir = logDir
		self.network = network
		self.scenario = scenario
		self.FileList = []
		self.AllTraffic = {}

	def readclientlogfile(self):
		totalClientFile = 0
		totalFlowConnected = 0
		totalFlowStatistics = 0
		# read input file
		try:
			# filename = "sim_results_pfo_fcfs_Test_36_mesh_gen.dat"
			# filepath = self.LogDir + "/" + filename
			# self.FileList.append(filepath)
			filename = "emu_results_MaxiNet_7200_" + str(self.scenario) + "_Network_" + str(self.network) + ".dat"
			filepath = self.LogDir + "/" + filename
			self.FileList.append(filepath)
			timepat = "Time: *"
			systimepat = "System Time Passed: *"
			flowsatpat = "Flows satisfied: *"
			for file in self.FileList:
				tfile = os.path.basename(file)
				self.AllTraffic[tfile] = []

				fin = open(file, "r")
				tmp = fin.readline()

				while True:
					tmp = fin.readline().split(" ")
					entry = {}
					try:
						# entry["counter"] += 1
						entry["time"] = float(tmp[0])
						entry["flows"] = int(tmp[1])
						for i in range(0, 6):
							entry[obj[i]] = int(tmp[i + 2])
						for i in range(6, len(obj)):
							entry[obj[i]] = float(tmp[i + 2])
						self.AllTraffic[tfile].append(entry)
					except:
						#traceback.print_exc(file=sys.stdout)
						break
			emutime = []
			# simtime = []
			emuclcused = []
			# simclcused = []
			# filename = "sim_results_pfo_fcfs_Test_36_mesh_gen.dat"
			# for entry in self.AllTraffic[filename]:
				# simtime.append(entry['time'])
				# simclcused.append(entry['#CLCs'])

			filename = "emu_results_MaxiNet_7200_" + str(self.scenario) + "_Network_" + str(self.network) + ".dat"
			for entry in self.AllTraffic[filename]:
				if use_realtime == True:
					emutime.append(entry['realtime'])
				else:
					emutime.append(entry['time'])
				emuclcused.append(entry['#CLCs'])

			# plt.plot(simtime, simclcused, 'bv')
			# # figtxt = "Simulation"
			# # plt.figtext(0.2, 0.80, figtxt, bbox=dict(facecolor='cyan'))
			# plt.ylabel('Number of LCA used')
			# plt.xlabel('Simulation time in Sec')
			# plt.show()

			plt.plot(emutime, emuclcused, 'rv', label='Number of LCAs used')
			x = range(0,7201)
			s = max(emuclcused)
			y = [loadlevel(i,s) for i in x]
			plt.plot(x, y, lw=1, color='blue', label='loadlevel curve (scaled)')
			# figtxt = "Emulation"
			# plt.figtext(0.2, 0.85, figtxt, bbox=dict(facecolor='red'))
			plt.ylabel('Number of LCAs used')
			plt.ylim(0,s+1)
			plt.yticks([i*2 for i in range(0,1+int((s+1)/2))])
			if use_realtime == True:
				plt.xlabel('System time (since $t = 0$) in seconds')
			else:
				plt.xlabel('Emulation time in seconds')
			plt.legend(loc='lower left', shadow=False, ncol=1)
			plt.savefig('plots/plot_emu_LCAs_' + str(network) + '_' + str(scenario) + '.pdf', bbox_inches='tight')


		except:
			traceback.print_exc(file=sys.stdout)
			#traceback.print_stack()
			return False

if '__main__' == __name__:
	logDir = "results"
	network = str(sys.argv[1])
	scenario = str(sys.argv[2])
	tf = TrafficDistribution(logDir,network,scenario)
	tf.readclientlogfile()

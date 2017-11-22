from __future__ import division
import sys, math, random, time, pdb
from math import exp, sqrt, pow
from cp_flex_fcfs import *
import datetime
import thread
from seeds import sim_seeds
from mininet.cli import CLI

import os
# We want to traffic pattern of whole 24 hours in 2 hours so here assuming a hours has only 300 sec
def loadlevel(i,scaling=1):  # time i is provided in seconds, scaling if necessary, default is 1
    i = 24 * (i / 3600) % 24  # switch from seconds to day time
    if i <= 3:
        return 0.9 * (-1 / 27 * pow(i, 2) + 1) * scaling
    elif i <= 6:
        return 0.9 * (1 / 27 * pow(i - 6, 2) + 1 / 3) * scaling
    elif i <= 15:
        return 0.9 * (1 / 243 * pow(i - 6, 2) + 1 / 3) * scaling
    else:
        return 0.9 * (-1 / 243 * pow(i - 24, 2) + 1) * scaling


def output(cpf, trun=None):
    print "State: " + cpf.state
    if cpf.state == "NOT SOLVED":
        print "Remaining nodes: " + str([i for i in cpf.cn.V if not i in cpf.Controlled])
    print "CRCs: " + str(len(cpf.CRCs))
    print str(cpf.CRCs)
    print "LCAs: " + str(len(cpf.CLCs)) + " (out of " + str(len(cpf.cn.C)) + " available)"
    print str(cpf.CLCs)
    print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
    if trun is not None:
        print "Runtime: " + str(trun) + " seconds"


def slimoutput(cpf, trun=None):
    if cpf.state == "NOT SOLVED":
        print "State: " + cpf.state + ", Remaining nodes: " + str(
            len([i for i in cpf.cn.V if not i in cpf.Controlled])) + " out of " + str(len(cpf.cn.V))
    else:
        print "State: " + cpf.state
    print "CRCs: " + str(len(cpf.CRCs)) + ", CLCs: " + str(len(cpf.CLCs)) + " (out of " + str(
        len(cpf.cn.C)) + " available), Control ratio: " + str(cpf.CLCcontrolRatio()) \
          + ", Average load: " + str(cpf.getAverageCLCload())
    print "Latest CRCs: " + str(cpf.CRCs) + " and , CLCs: " + str(cpf.CLCs)
    print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
    if trun is not None:
        print "Runtime: " + str(trun) + " seconds"



def simstep(cpf, calctime, starttime):
    tmpCLCs = list(cpf.CLCs)
    cpf.cpgreedy()
    trun = cpf.lastruntime
    iperfstoptime = cpf.lastiperfstoptime
    nodeDiff = cpf.newCLCcontrols
    flowDiff = cpf.newFlowSats

    CLCDiff = len(set(cpf.CLCs).symmetric_difference(set(tmpCLCs)))

    tmodstart = time.time()
    # print "Start Adding routing entry:" + str(time.time())
    cpf.modifyRoutingTable()
    # print "End Adding routing entry:" + str(time.time())
    tmodend = time.time()
    # print "Start the iperf client:" + str(time.time())
    iperfcount = cpf.generateTrafficFlow()
    # print "End the iperf client:" + str(time.time())
    tgenend = time.time()
    
    tmod = tmodend - tmodstart
    tgen = tgenend - tmodend
    tnetrun = tgenend - tmodstart
    realtime = tgenend - starttime

    if display_output:
        print "Time: " + str(calctime)
        print "System Time Passed: " + str(realtime)
        slimoutput(cpf, trun)
        print "\n"

    if graph_output:
        cpf.cn.output()

    global graph_output_once
    if graph_output_once:
        graph_output_once = False
        cpf.cn.output(results_path + '/graph_fcfs_' + filename[:-4] + '.pdf')
        if only_graph_output:
            exit(1)

    if results_output and t >= 0:
        foutmain = open(results_filename, "a")
        foutmain.write(str(calctime) + " " + str(len(cpf.cn.F)) + " " + str(len(cpf.Satisfied)) + " " + str(len(cpf.CRCs)) + " " + str(len(cpf.CLCs)) + " " + str(CLCDiff) + " " + str(nodeDiff) + " " + str(flowDiff) \
                       + " " + str(cpf.getAverageCRCpathlength()) + " " + str(cpf.getAverageCLCpathlength()) + " " + str(cpf.getAverageCLCload()) + " " + str(cpf.CLCcontrolRatio()) + " " + str(trun) + " " + str(tnetrun) \
                       + " " + str(realtime) + " " + str(tmod) + " " + str(tgen) + " " + str(iperfstoptime) + " " + str(iperfcount) + " \n")
        foutmain.close()

# initialize
try:
    emulator = str(sys.argv[1])
except:
    emulator = "Mininet"

print "Info: Emulator " + emulator + " is used."

try:
    sim_duration = int(sys.argv[2])
except:
    sim_duration = 600

print "Info: The test will run for " + str(sim_duration) + " seconds"

try:
    filename = str(sys.argv[3])
except:
    filename = 'Test_9_mesh.dat'
    
try:
    escen = str(sys.argv[4])
except:
    escen = "generic"

print "Info: The test will use topology specified in " + filename

time.sleep(10)

results_path = 'results'
results_filename = results_path + '/emu_results_' + emulator + '_' + str(sim_duration) + '_' + escen + '_' + filename
display_output = True
graph_output = False
results_output = True
graph_output_once = False
only_graph_output = False

cpf = CPFlex(filename, flowOption="LeastDemanding", emulator=emulator, evalscen=escen)
cpf.flexOperation = True
cpf.clearFlows()
no_nodes = len(cpf.cn.V)
if escen == "generic":
    d_LL = 0.9
    random.seed(sim_seeds[41])
elif escen == "CoMP":
    d_LL = 0.8
    random.seed(sim_seeds[42])
else:
    print "Error: Invalid evaluation scenario!"
    exit(1)
cpf.L_lowload = d_LL
cpf.T_lowload = 60.0
cpf.cn.flowDurationMode = "expo"
cpf.iperf_log_tag = escen + "_" + filename[-11:-4] + "/"

cpf.setupEmulationNetwork()
time.sleep(20)
cpf.populateNetworkLinks()
time.sleep(10)

if results_output:
    foutmain = open(results_filename, "a")
    foutmain.write(
        "time #flows #Satisfied #CRCs #CLCs #CLCDiff #nodeDiff #flowDiff CRCpathlength CLCpathlength CLCload controlRatio runtime netmodtime realtime tmod tgen tstop #flowGen \n")
    foutmain.close()

simstart = -1800.0 #0.0
t = simstart
tlast = t
perform_simstep = False
lastdisp = simstart
calctime = simstart
llalarm = False
if escen == "generic":
    ll_scale = 0.20
elif escen == "CoMP":
    ll_scale = 0.02
else:
    print "Error: Invalid evaluation scenario!"
    exit(1)
lambdamax = max([loadlevel(i, ll_scale) for i in range(0, sim_duration)]) * no_nodes

rejectedFlows = 0
remcount = 0
addcount = 0
lastsleeptime = 0
lastcontr = 0
stt = datetime.datetime.now()
starttime = time.time()

while t < sim_duration:
    t1 = datetime.datetime.now()
    nextvar = random.expovariate(lambdamax)
    t += nextvar
    c = random.random()
    if c < loadlevel(t, ll_scale) * no_nodes / lambdamax:
        d = random.expovariate(0.02)
        
        tt1 = time.time()
        to_be_removed = [f for f in cpf.cn.F if cpf.cn.fdata[f]['genstime'] + cpf.cn.fdata[f]['duration'] < tt1]
        for f in to_be_removed:
            cpf.remFlow(f, stopiperf=False)
            remcount += 1
                    
        tt1 = time.time()
        cpf.addFlow(stime=tt1-starttime, dur=d)
        f = cpf.cn.F[-1]
        if cpf.cn.fdata[f]['isSat'] == True:
            cpf.generateTrafficForSingleFlow(f)
        else:
            cpf.TotalUnsatisfied.append(f)
            #print "Flow not satisfied : " + str(cpf.cn.fdata[f])
        addcount += 1

        tlast = t
        cpf.updateTime(t)

        if cpf.state <> "Solved":  # for reality purpose in case of a CLC or CRC failure, should currently not happen
            perform_simstep = True
            reason = 1

        if len(cpf.cn.F) > len(cpf.Satisfied) and len(cpf.cn.C) > len(cpf.CLCs):
            perform_simstep = True
            reason = 2  # Incoming data flows

        if cpf.LL_execution == True:
            perform_simstep = True
            reason = 3  # Low load situation

        if perform_simstep:
            print "Reason: " + str(reason) + ", t = " + str(t)
            calctime = t
            lastdisp = t
            if t >= 0:
                simstep(cpf, calctime, starttime - simstart)
            else:
                cpf.cpgreedy()
                print "Using " + str(len(cpf.CLCs)) + " CLCs out of " + str(len(cpf.cn.C))
                print "Adding routing entry:" + str(time.time())
                cpf.modifyRoutingTable()
                print "Start of iperf client for the satisfied flow:" + str(time.time())
                cpf.generateTrafficFlow()
                print "End of iperf client for the satisfied flow:" + str(time.time())
            if reason == 2 and len(cpf.cn.F) > len(cpf.Satisfied): # Remove not satisfied DFGs
                btmp = list(set(cpf.cn.F) - set(cpf.Satisfied))
                for f in btmp:
                    cpf.remFlow(f, stopiperf=False)
                    remcount += 1
                    rejectedFlows += 1
            perform_simstep = False

        if t - lastdisp > 10:
            print "Time: " + str(t)
            print "System Time Passed: " + str(time.time()-starttime)
            print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
            if len(cpf.cn.F) > 0:
                print "Next flow removed at: " + str(min([cpf.cn.fdata[f]['genstime'] - starttime + cpf.cn.fdata[f]['duration'] for f in cpf.cn.F]))
            #print "Average CLC load: " + str(cpf.getAverageCLCload())
            print "addcount:" + str(addcount) + " and remcount:" + str(remcount)
            print "\n"
            lastdisp = t
            
    t2 = datetime.datetime.now()
    # Sleep/Deduct the duration moved ahead minus the processing time
    delta = t2 - t1
    deltafloat = delta.seconds + delta.microseconds / 1000000.0
    startdelta = t2 - stt
    startdeltafloat = startdelta.seconds + startdelta.microseconds / 1000000.0
    sleeptime = min(nextvar-deltafloat, t-simstart-startdeltafloat)
    if sleeptime > 0.0009 and t - simstart > startdeltafloat:
        time.sleep(sleeptime)

print "At the end"
print "starttime:" + str(starttime)
print "difftime:" + str(time.time() - starttime)
print "realtime:" + str(time.time() - starttime + simstart)
print "t:" + str(t)

if emulator == "Mininet":
    # Mininet
    # cpf.TestbedNetwork.startTerms()
    CLI(cpf.TestbedNetwork)
elif emulator == "MaxiNet":
    # MaxiNet
    cpf.TestbedNetwork.CLI(locals(), globals())
else:
    print("Error: Emulator missing!")
    exit(1)

print "At the end addcount:" + str(addcount) + " and remcount:" + str(remcount) + " and rejectedFlows:" + str(rejectedFlows)
cpf.TotalSatisfied = set(cpf.TotalSatisfied)
cpf.TotalUnsatisfied = set(cpf.TotalUnsatisfied)
print "At the end TotalSatisfied:" + str(len(cpf.TotalSatisfied)) + " and TotalUnsatisfied:" + str(len(cpf.TotalUnsatisfied)) + " and TotalFlowStopped:" + str(len(cpf.TotalFlowStopped))
cpf.TestbedNetwork.stop()
print "At the end starttime:" + str(starttime) + " and endtime:" + str(time.time())

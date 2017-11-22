from ComplexNetworkSim import NetworkAgent, Sim
import sys, math, random, time, pdb
from math import exp,sqrt,pow
from lib import cp_flex_fcfs



# This class initializes all nodes with their initial data
# Also changes the flows during the simulation
class Manager(NetworkAgent):

  def __init__(self, state, initialiser):
    NetworkAgent.__init__(self, 0, initialiser)

  def Run(self):
    yield Sim.passivate, self
    
# Flow processing-aware Control Application Placement

Author: Sébastien Auroux

This repository contains all code for my solution approaches for the Flow processing-aware Control Application Placement Problem (FCAPP) as described in my Phd thesis.

## Abstract: 

The traffic demand in mobile access networks has grown substantially in recent years and is expected to continue to do so, both in terms of total volume and data rate required by individual users. The infrastructure of mobile access networks has to keep up with this trend and provide the data rates to satisfy the increasing demands. To achieve this, employing coordination mechanisms is essential to use the available resources efficiently. By exploiting recent network softwarization approaches, such coordination mechanisms can be handled by virtualized *Control Applications (CAs)* that can be flexibly positioned in the network.

In my thesis, I explore the problem of placing these CAs appropriately in the backhaul network of a mobile access network, which I introduce as *Flow processing-aware Control Application Placement Problem (FCAPP)*. FCAPP is a challenging placement problem including tight latency, data rate and processing capacity constraints on the backhaul infrastructure. In particular, coordination mechanisms require a considerable amount of control information and user data to be exchanged between the base stations and to be jointly processed at the host of a CA. To tackle this, FCAPP considers *Data Flow Groups (DFGs)*, a concept that ensures the aforementioned joint processing and, in addition, also allows to express various types of coordination mechanisms.

Over the course of my research, I have considered multiple variations and several solution approaches for FCAPP to (1) efficiently decide initial CA placement and (2) to quickly and flexibly adapt placement decisions during network operation in reaction to traffic load changes. In my Phd thesis, I have described my investigation results on FCAPP, my developed solution approaches and I have presented extensive evaluation results for all of them. Most notably, I have presented a fast centralized placement framework (FlexCAPF) including prototype implementation and a distributed algorithm (DistCAPA), which both fulfill the aforementioned goals.

## Content

The repository consists of the following folder structure:

* Optimization_models: all FCAPP optimization models
* FlexCAPF: all Greedy-based FCAPP heurstic approaches (FlexCAPF & GreedyFCAPA)
* DistCAPA: distributed FCAPP algorithm (DistCAPA)
* testbed: SDN-based emulation environment for FCAPP & FlexCAPF proof of concept implementation
* GA: FCAPP Genetic algorithm approaches (however, only for inferior equal-share scheduling)

All implementations are based on Python 2.7 and require additional packages and/or software as described in the individual README.md files in the respective folders. 
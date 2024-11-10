import os
import pdb
from collections import deque, defaultdict
from .utility import utility
import inspect
from controller.NodeGenerator import RestrictionNode
from controller.NodeGenerator import TimeWindowNode
from .Node import Node

class RestrictionController:
    def __init__(self, graph_processor):
        self.restrictionEdges = defaultdict(list)
        self.alpha = graph_processor.alpha
        self.beta = graph_processor.beta
        self.gamma = graph_processor.gamma
        self.H = graph_processor.H 
        self.ur = graph_processor.ur
        self.M = graph_processor.M
        self.graph_processor = graph_processor
    
    def add_nodes_and_ReNode(self, forward_to_aS, rise_from_aT, restriction, aS, aT):
        #pdb.set_trace()
        #if( isinstance(node, RestrictionNode)):
        key = tuple(restriction)
        if(not key in self.restrictionEdges):
            self.restrictionEdges[key] = []
        found = False
        for to_aS, from_aT, _, _ in self.restrictionEdges[key]:
            if(to_aS == forward_to_aS and from_aT == rise_from_aT):
                found = True
                break
        if(not found):
            self.restrictionEdges[key].append([forward_to_aS, rise_from_aT, aS, aT])

    def remove_restriction_edges(self, key):
        if(key in self.restrictionEdges):
            del self.restrictionEdges[key]

    def generate_restriction_edges(self, start_node, end_node, nodes, adj_edges):
        space_source = start_node.id % self.M if start_node.id % self.M != 0 else self.M
        space_destination = end_node.id % self.M if end_node.id % self.M != 0 else self.M
        time_source = start_node.id // self.M - (1 if start_node.id % self.M == 0 else 0)
        time_destination = end_node.id // self.M - (1 if end_node.id % self.M == 0 else 0)
        if(not (time_source >= self.graph_processor.end_ban or time_destination <= self.graph_processor.start_ban)):
            key = tuple([space_source, space_destination])
            if(key in self.restrictionEdges):
                found = False
                for element in self.restrictionEdges[key]:
                    if(element[0] == start_node.id and element[1] == end_node.id):
                        aS = element[2]
                        aT = element[3]
                        found = True
                        break
                if(found):
                    pdb.set_trace()
                    e1 = (start_node.id, aS, 0, 1, 0)
                    temp1 = start_node.create_edge(self.graph_processor.find_node[aS], self.M, self.graph_processor.d, e1)
                    print("edge: ", temp1, end = '')
                    adj_edges[start_node.id].append([aS, temp1])
                    e2 = (end_node.id, aT, 0, 1, time_destination - time_source)
                    temp2 = self.graph_processor.find_node(aT).create_edge(end_node, self.M, self.graph_processor.d, e2)
                    adj_edges[aT].append(end_node.id, temp2)

import os
import pdb
from collections import defaultdict

class RestrictionController:
    def __init__(self, graph_processor):
        self.restriction_edges = defaultdict(list)
        self.alpha = graph_processor.alpha
        self.beta = graph_processor.beta
        self.gamma = graph_processor.gamma
        self.H = graph_processor.H 
        self.ur = graph_processor.ur
        self.M = graph_processor.M
        self.graph_processor = graph_processor
    
    def add_nodes_and__re_node(self, forward_to_a_s, rise_from_a_t, restriction, a_s, a_t):
        #pdb.set_trace()
        #if( isinstance(node, RestrictionNode)):
        key = tuple(restriction)
        if(key not in self.restriction_edges):
            self.restriction_edges[key] = []
        found = False
        for to_a_s, from_a_t, _, _ in self.restriction_edges[key]:
            if(to_a_s == forward_to_a_s and from_a_t == rise_from_a_t):
                found = True
                break
        if(not found):
            self.restriction_edges[key].append([forward_to_a_s, rise_from_a_t, a_s, a_t])

    def remove_restriction_edges(self, key):
        if(key in self.restriction_edges):
            del self.restriction_edges[key]

    def generate_restriction_edges(self, start_node, end_node, nodes, adj_edges):
        space_source = start_node.id % self.M if start_node.id % self.M != 0 else self.M
        space_destination = end_node.id % self.M if end_node.id % self.M != 0 else self.M
        time_source = start_node.id // self.M - (1 if start_node.id % self.M == 0 else 0)
        time_destination = end_node.id // self.M - (1 if end_node.id % self.M == 0 else 0)
        if(not (time_source >= self.graph_processor.end_ban or time_destination <= self.graph_processor.start_ban)):
            key = tuple([space_source, space_destination])
            if(key in self.restriction_edges):
                found = False
                for element in self.restriction_edges[key]:
                    if(element[0] == start_node.id and element[1] == end_node.id):
                        a_s = element[2]
                        a_t = element[3]
                        found = True
                        break
                if(found):
                    pdb.set_trace()
                    e1 = (start_node.id, a_s, 0, 1, 0)
                    temp1 = start_node.create_edge(self.graph_processor.find_node[a_s], self.M, self.graph_processor.d, e1)
                    print("edge: ", temp1, end = '')
                    adj_edges[start_node.id].append([a_s, temp1])
                    e2 = (end_node.id, a_t, 0, 1, time_destination - time_source)
                    temp2 = self.graph_processor.find_node(a_t).create_edge(end_node, self.M, self.graph_processor.d, e2)
                    adj_edges[a_t].append(end_node.id, temp2)

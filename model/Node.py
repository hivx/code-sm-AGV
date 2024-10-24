#from .TimeWindowEdge import TimeWindowEdge
#from .Edge import HoldingEdge, MovingEdge
#from .RestrictionEdge import RestrictionEdge
#from .RestrictionNode import RestrictionNode
#from .TimeWindowNode import TimeWindowNode
import pdb
from inspect import currentframe, getframeinfo
import inspect

class Node:
    def __init__(self, id,label=None):
        if not isinstance(id, int):
            raise ValueError(f"Tham số {id} truyền vào phải là số nguyên")
        self._id = id
        """if(id == 19685):
            print(f'{getframeinfo(currentframe()).filename.split("/")[-1]}:{getframeinfo(currentframe()).lineno} {self.id}', end=' ')
            print("==========Nghi ngo van de o day!========", end='')
            current_frame = inspect.currentframe()
            caller_name = inspect.getframeinfo(current_frame.f_back).function
            print(caller_name)"""
            #pdb.set_trace()
        self.label=label
        self.edges = []
        self.agv = None

    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, value):
        """if(value == 13899):
            print(f'{getframeinfo(currentframe()).filename.split("/")[-1]}:{getframeinfo(currentframe()).lineno} {self.id}', end=' ')
            print("==========Nghi ngo van de o day!========")"""
        self._id = value
    def create_edge(self, node, M, d, e, debug = False):
        if(debug):
            pdb.set_trace()
        from .RestrictionNode import RestrictionNode
        from .TimeWindowNode import TimeWindowNode
        from .Edge import HoldingEdge
        from .RestrictionEdge import RestrictionEdge
        from .TimeWindowEdge import TimeWindowEdge 
        from .Edge import MovingEdge
        if(isinstance(node, int)):
            pdb.set_trace()
        if node.id % M == self.id % M and \
        ((node.id - self.id) // M == d) and \
        isinstance(node, Node) and \
        not isinstance(node, RestrictionNode) and \
        not isinstance(node, TimeWindowNode):
            return HoldingEdge(self, node, e[2], e[3], d, d)
        elif isinstance(node, RestrictionNode):
            return RestrictionEdge(self, node, e, "Restriction")
        elif isinstance(node, TimeWindowNode):
            return TimeWindowEdge(self, node, e[4], "TimeWindows")
        elif isinstance(node, Node):
            if node.id % M != self.id % M:
                return MovingEdge(self, node, e[2], e[3], e[4])
        else:
            return None
        
    def connect(self, other_node, weight, graph):
        graph.add_edge(self.id, other_node.id, weight)
        
    def getEventForReaching(self, event):
        #next_vertex = event.agv.getNextNode().id
        #event.agv.path.add(self.id)
        #print(f"========={event.agv.path}")
        from .HoldingEvent import HoldingEvent
        from .ReachingTargetEvent import ReachingTargetEvent
        
        current_node = event.agv.current_node.id if isinstance(event.agv.current_node, Node) else event.agv.current_node

        # Xác định kiểu sự kiện tiếp theo
        deltaT = (self.id // event.graph.numberOfNodesInSpaceGraph \
                                #- (event.graph.graph_processor.d if self.id % event.graph.numberOfNodesInSpaceGraph == 0 else 0)) - (
                                - (1 if self.id % event.graph.numberOfNodesInSpaceGraph == 0 else 0)) - (
            current_node // event.graph.numberOfNodesInSpaceGraph \
                                #- (event.graph.graph_processor.d if current_node % event.graph.numberOfNodesInSpaceGraph == 0 else 0)
                                - (1 if current_node % event.graph.numberOfNodesInSpaceGraph == 0 else 0)
        )

        if (self.id % event.graph.numberOfNodesInSpaceGraph) == (
            current_node % event.graph.numberOfNodesInSpaceGraph
        ):
            from .StartEvent import StartEvent
            if(not isinstance(event, StartEvent)):
                event.agv.move_to(event)
            return HoldingEvent(
                event.end_time,
                event.end_time + deltaT,
                event.agv,
                event.graph,
                deltaT,
            )
        elif self.id == event.agv.target_node.id:
            print(f"Target {event.agv.target_node.id}")
            #deltaT = getReal()
            return ReachingTargetEvent(
                event.end_time, event.end_time, event.agv, event.graph, self.id
            )
        else:
            """print(f'{self.id}')
            if self.id == 30091:
                pdb.set_trace()"""
            return self.goToNextNode(event)

    # TODO Rename this here and in `getEventForReaching`
    def goToNextNode(self, event):
        from .Event import Event
        from .StartEvent import StartEvent
        from .MovingEvent import MovingEvent
        from .HaltingEvent import HaltingEvent
        from .ReachingTargetEvent import ReachingTargetEvent
        #if(len(event.agv.get_traces()) == 0):
        #    pdb.set_trace()
        if(not isinstance(event, StartEvent)):
            #if(event.agv.id == 'AGV31'):
            #    pdb.set_trace()
            event.agv.move_to(event)
        ##if(len(event.agv.get_traces()) == 0):
        #    pdb.set_trace()
        """print(f'Node.py:94 {event.agv.id}', end=' ')
        for node in event.agv.get_traces():
            print(node.id, end= ' ')
        print()"""
        M = event.graph.graph_processor.M
        #if(event.agv.id == 'AGV30' and self.id % M == 14):
        #    pdb.set_trace()
        if(len(event.agv.get_traces()) > 0):
            #pdb.set_trace()
            next_vertex = event.agv.get_traces()[0].id
        else:
            #if(event.agv.target_node is None):
            #    pdb.set_trace()
            #next_vertex = event.agv.target_node.id
            next_vertex = -1
            reaching_time = self.id // M - (1 if self.id % M == 0 else 0)
            for source_id in event.graph.graph_processor.time_window_controller.TWEdges:
                if(source_id % M == self.id % M):
                    #pdb.set_trace()
                    if(event.graph.graph_processor.time_window_controller.TWEdges[source_id] is not None):
                        edges = event.graph.graph_processor.time_window_controller.TWEdges[source_id]
                        if(len(edges) == 0):
                            pdb.set_trace()
                        else:
                            max_cost = edges[0][0].calculate(reaching_time)
                            index = 0
                            for i in range(1, len(edges)):
                                temp = edges[i][0].calculate(reaching_time)
                                if temp > max_cost:
                                    max_cost = temp
                                    index = i
                            next_vertex = edges[index][0].id
                            if(event.agv.target_node is None or event.agv.target_node.id != next_vertex):
                                event.agv.target_node = edges[index][0]
                            break
            if(next_vertex == -1):
                pdb.set_trace()
        
        """edges_with_cost = { (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])] for edge in event.graph.graph_processor.space_edges \
            if edge[3] == '0' and int(edge[4]) >= 1 }
        space_start_node = event.agv.current_node % M + (M if event.agv.current_node % M == 0 else 0)
        space_end_node = next_vertex % M + (M if next_vertex % M == 0 else 0)
        min_moving_time = edges_with_cost.get((space_start_node, space_end_node), [-1, -1])[1]
        if(min_moving_time == -1):
            pdb.set_trace()"""
        #if(event.agv.current_node != self.id):
        #    #pass
        #    #pdb.set_trace()
        #if (event.agv.id == 'AGV30'):
        #    real_current_node = event.agv.current_node % M + (M if event.agv.current_node % M == 0 else 0)
        #    if(real_current_node == 21):
        #        pass
        #        #pdb.set_trace()
        deltaT = event.graph.getReal(event.agv.current_node, next_vertex, event.agv)
        #if(deltaT <= 10):
        #    pdb.set_trace()
        #    deltaT= event.graph.getReal(event.agv.current_node, next_vertex, event.agv)
        allIDsOfTargetNodes = [node.id for node in event.graph.graph_processor.targetNodes]
        if(next_vertex in allIDsOfTargetNodes):
            #if(event.agv.id == 'AGV30'):
            #    pdb.set_trace()
            return ReachingTargetEvent(\
                event.end_time, event.end_time, event.agv, event.graph, next_vertex)
        if(deltaT == 0):
            #pdb.set_trace()
            pass
        if event.end_time + deltaT < event.graph.graph_processor.H:
                #pdb.set_trace()
            #pdb.set_trace()
            return MovingEvent(
                event.end_time,
                event.end_time + deltaT,
                event.agv,
                event.graph,
                event.agv.current_node,
                next_vertex,
            )
        if(event.graph.graph_processor.printOut):
            print(f"H = {event.graph.graph_processor.H} and {event.end_time} + {deltaT}")
            #pdb.set_trace()
        #pdb.set_trace()
        return HaltingEvent(
            event.end_time,
            event.graph.graph_processor.H,
            event.agv,
            event.graph,
            event.agv.current_node,
            next_vertex,
            deltaT
        )
    
    def __repr__(self):
        return f"Node(id={self.id}, label='{self.label}', agv='{self.agv}')"   

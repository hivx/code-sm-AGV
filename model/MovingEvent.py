from .Event import Event
from .HaltingEvent import HaltingEvent
import inspect
import pdb
from discrevpy import simulator
from datetime import datetime

class MovingEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, start_node, end_node):
        super().__init__(start_time, end_time, agv, graph)
        #pdb.set_trace()
        self.start_node = start_node
        self.end_node = end_node
        self.force_quit = False
        #print(self)
        M = self.graph.numberOfNodesInSpaceGraph
        t1 = self.start_node // M - (self.graph.graph_processor.d if self.start_node % M == 0 else 0)
        if(t1 != self.start_time):
            if(self.graph.graph_processor.printOut):
                print("Errror")
            #pdb.set_trace()
            # Lấy thông tin về khung hiện tại
            """current_frame = inspect.currentframe()
            # Lấy tên của hàm gọi my_function
            caller_name = inspect.getframeinfo(current_frame.f_back).function
            if(self.graph.graph_processor.printOut):
                print(f'MovingEvent.py:19 {caller_name}')"""
    def __str__(self):
        M = self.graph.numberOfNodesInSpaceGraph
        space_start_node = self.start_node % M + (M if self.start_node % M == 0 else 0)
        space_end_node = self.end_node % M + (M if self.end_node % M == 0 else 0)
        now = datetime.now()
        formatted_time = now.strftime("%j-%m-%y:%H-%M-%S")
        return f"\t . Now: {formatted_time}. MovingEvent for {self.agv.id} to move from {self.start_node}({space_start_node}) at {self.start_time} and agv reaches {space_end_node} at {self.end_time}"
        
    def updateGraph(self):
        actual_time = self.end_time - self.start_time
        #pdb.set_trace()
        #if(self.start_node == 10 or self.agv.id == 'AGV10'):
        #    pdb.set_trace()
        #weight_of_edge = self.graph.get_edge(self.start_node, self.end_node)  # Use self.graph instead of Graph
        M = self.graph.numberOfNodesInSpaceGraph
        #t2 = self.end_node // M - (self.graph.graph_processor.d if self.end_node % M == 0 else 0)
        #t1 = self.start_node // M - (self.graph.graph_processor.d if self.start_node % M == 0 else 0)
        t2 = self.end_node // M - (1 if self.end_node % M == 0 else 0)
        t1 = self.start_node // M - (1 if self.start_node % M == 0 else 0)
        #if(t1 != self.start_time):
        #    pdb.set_trace()
        real_end_node = self.end_time*M + (M if self.end_node % M == 0 else self.end_node % M)
        #if(real_end_node == 2186):
        #    pdb.set_trace()
        #24 09 01
        """self.agv.path.add(real_end_node)"""
        
        if(real_end_node in self.graph.nodes):
            if(self.graph.nodes[real_end_node].agv is not None):
                if (self.graph.nodes[real_end_node].agv.id != self.agv.id):
                    #print(f'{self.graph.nodes[real_end_node].agv.id} != {self.agv.id}')
                    #pdb.set_trace()
                    deltaT = 0
                    new_event = None
                    while(True):
                        deltaT = deltaT + 1
                        real_end_node = real_end_node + M*deltaT
                        if(self.end_time + deltaT < self.graph.graph_processor.H):
                            if(real_end_node in self.graph.nodes):
                                if(self.graph.nodes[real_end_node].agv is not None):
                                    if (self.graph.nodes[real_end_node].agv.id != self.agv.id):
                                        continue
                            new_event = MovingEvent(self.start_time, \
                                self.end_time + deltaT, self.agv, self.graph, self.agv.current_node, real_end_node)
                            break
                        else:
                            new_event = HaltingEvent(self.end_time, \
                                self.graph.graph_processor.H, self.agv, self.graph, self.agv.current_node, real_end_node, deltaT)    
                            break                                    
                    simulator.schedule(new_event.end_time, new_event.process)
                    self.force_quit = True
                    return
                
            self.graph.nodes[real_end_node].agv = self.agv
        if self.start_node in self.graph.nodes:
            if self.start_node != real_end_node:
                self.graph.nodes[self.start_node].agv = None
            """pdb.set_trace()
            self.graph.nodes[real_end_node].agv = self.graph.nodes[self.start_node].agv \
                if(self.graph.nodes[self.start_node].agv is not None) else self.graph.nodes[self.end_node].agv
        self.graph.nodes[self.start_node].agv = None"""
        
        weight_of_edge = t2 - t1
        predicted_time = weight_of_edge or None
        #if(self.start_time == 682 and self.end_time == 713 and self.agv.id == 'AGV4'):
        #    print("Gonna out of range exception")
        #    pdb.set_trace()
        #if(real_end_node == 14987):
        #    pdb.set_trace()
        #pdb.set_trace()

        #if actual_time != predicted_time:
        if real_end_node != self.end_node:
            if self.end_node in self.graph.nodes:
                self.graph.nodes[self.end_node].agv = None
            self.agv.current_node = real_end_node
            """if(real_end_node == 41987 or real_end_node == 53700):
                pdb.set_trace()"""
            self.graph.update_graph(self.start_node, self.end_node, real_end_node, self.agv.id)
            #self.agv.set_traces([self.graph.nodes[real_end_node]])
            self.agv.update_traces(self.end_node, self.graph.nodes[real_end_node])
            #if(len(self.agv.get_traces()) == 0):
            #    pdb.set_trace()
            #self.graph.nodes[real_end_node].agv = self.agv
            self.graph.reset_agv(real_end_node, self.agv)
            
            #self.graph.update_edge(self.start_node, self.end_node, actual_time)  # Use self.graph instead of Graph
            #self.graph.handle_edge_modifications(self.start_node, self.end_node, self.agv)  # Use self.graph instead of Graph

    def calculateCost(self):
        #pdb.set_trace()
        # Tính chi phí dựa trên thời gian di chuyển thực tế
        cost_increase = self.graph.graph_processor.alpha*(self.end_time - self.start_time)
        self.agv.cost += cost_increase  # Cập nhật chi phí của AGV
        return cost_increase

    def process(self):
        #if(self.agv.id == 'AGV4'):
        #    pdb.set_trace()
        if(self.graph.graph_processor.printOut):
            print(self)
        self.calculateCost()
        # Thực hiện cập nhật đồ thị khi xử lý sự kiện di chuyển
        self.updateGraph()
        if(self.force_quit):
            return
        if(self.graph.graph_processor.printOut):
            print(
                f"AGV {self.agv.id} moves from {self.start_node} to {self.end_node} taking actual time {self.end_time - self.start_time}"
                )
        #pdb.set_trace()
        #debug = self.start_time == 682 and self.end_time == 713
        #self.getNext("""debug""")
        #self.getNext()
        self.solve()
        #pdb.set_trace()
        next_node = self.graph.nodes[self.agv.current_node]
        #if(self.agv.id == 'AGV30' and next_node.id == 12046):
        #    pdb.set_trace()
        #new_event = next_node.getEventForReaching(self)
        new_event = next_node.goToNextNode(self)
        simulator.schedule(new_event.end_time, new_event.process)

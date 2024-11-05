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
        M = self.graph.number_of_nodes_in_space_graph
        t1 = self.start_node // M - (self.graph.graph_processor.d if self.start_node % M == 0 else 0)
        if(t1 != self.start_time):
            if(self.graph.graph_processor.print_out):
                print("Errror")
            #pdb.set_trace()
            # Lấy thông tin về khung hiện tại
            """current_frame = inspect.currentframe()
            # Lấy tên của hàm gọi my_function
            caller_name = inspect.getframeinfo(current_frame.f_back).function
            if(self.graph.graph_processor.print_out):
                print(f'MovingEvent.py:19 {caller_name}')"""
    def __str__(self):
        M = self.graph.number_of_nodes_in_space_graph
        space_start_node = self.start_node % M + (M if self.start_node % M == 0 else 0)
        space_end_node = self.end_node % M + (M if self.end_node % M == 0 else 0)
        now = datetime.now()
        formatted_time = now.strftime("%j-%m-%y:%H-%M-%S")
        return f"\t . Now: {formatted_time}. MovingEvent for {self.agv.id} to move from {self.start_node}({space_start_node}) at {self.start_time} and agv reaches {space_end_node} at {self.end_time}"
      
    def updateGraph(self):
        M = self.graph.number_of_nodes_in_space_graph
        real_end_node = self.calculate_real_end_node(M)

        if real_end_node in self.graph.nodes:
            if self.graph.nodes[real_end_node].agv is not None:
                if self.graph.nodes[real_end_node].agv.id != self.agv.id:
                    self.handle_event(real_end_node, M)
                    return
            
            self.graph.nodes[real_end_node].agv = self.agv

        self.update_agv_nodes(real_end_node)

        if real_end_node != self.end_node:
            self.update_graph_and_traces(real_end_node)

    def calculate_real_end_node(self, M):
        return self.end_time * M + (M if self.end_node % M == 0 else self.end_node % M)

    def handle_event(self, real_end_node, M):
        delta_t = 0
        while True:
            delta_t += 1
            real_end_node += M * delta_t
            if self.end_time + delta_t < self.graph.graph_processor.H:
                if real_end_node in self.graph.nodes and self.graph.nodes[real_end_node].agv is not None:
                    if self.graph.nodes[real_end_node].agv.id != self.agv.id:
                        continue
                new_event = MovingEvent(self.start_time, self.end_time + delta_t, self.agv, self.graph, self.agv.current_node, real_end_node)
                break
            else:
                new_event = HaltingEvent(self.end_time, self.graph.graph_processor.H, self.agv, self.graph, self.agv.current_node, real_end_node, delta_t)    
                break                                    
        simulator.schedule(new_event.end_time, new_event.process)
        self.force_quit = True

    def update_agv_nodes(self, real_end_node):
        if self.start_node in self.graph.nodes:
            if self.start_node != real_end_node:
                self.graph.nodes[self.start_node].agv = None
        if self.end_node in self.graph.nodes:
            self.graph.nodes[self.end_node].agv = None

    def update_graph_and_traces(self, real_end_node):
        self.agv.current_node = real_end_node
        self.graph.update_graph(self.start_node, self.end_node, real_end_node, self.agv.id)
        self.agv.update_traces(self.end_node, self.graph.nodes[real_end_node])
        self.graph.reset_agv(real_end_node, self.agv)

    def calculateCost(self):
        #pdb.set_trace()
        # Tính chi phí dựa trên thời gian di chuyển thực tế
        cost_increase = self.graph.graph_processor.alpha*(self.end_time - self.start_time)
        self.agv.cost += cost_increase  # Cập nhật chi phí của AGV
        return cost_increase

    def process(self):
        if(self.graph.graph_processor.print_out):
            print(self)
        self.calculateCost()
        # Thực hiện cập nhật đồ thị khi xử lý sự kiện di chuyển
        self.updateGraph()
        if(self.force_quit):
            return
        if(self.graph.graph_processor.print_out):
            print(
                f"AGV {self.agv.id} moves from {self.start_node} to {self.end_node} taking actual time {self.end_time - self.start_time}"
                )
        self.solve()
        #pdb.set_trace()
        next_node = self.graph.nodes[self.agv.current_node]
        new_event = next_node.goToNextNode(self)
        simulator.schedule(new_event.end_time, new_event.process)

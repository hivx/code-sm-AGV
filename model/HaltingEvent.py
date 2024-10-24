from .Event import Event
import inspect
import pdb
import config
class HaltingEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, start_node, end_node, deltaT):
        super().__init__(start_time, end_time, agv, graph)
        self.start_node = start_node
        self.end_node = end_node
        self.deltaT = deltaT
        #pdb.set_trace()
        current_frame = inspect.currentframe()
        # Lấy tên của hàm gọi my_function
        caller_name = inspect.getframeinfo(current_frame.f_back).function
        if(self.graph.graph_processor.printOut):
            print(f'HaltingEvent.py:14 {caller_name}')
        #print(self)

    def updateGraph(self):
        if(self.end_time >= self.graph.H):
            pass
            #self.graph.update_edge(self.start_node, self.end_node, actual_time)  # Use self.graph instead of Graph
            #self.graph.handle_edge_modifications(self.start_node, self.end_node, self.agv)  # Use self.graph instead of Graph

    def calculateCost(self):
        #pdb.set_trace()
        # Tính chi phí dựa trên thời gian di chuyển thực tế
        cost_increase = float('inf') if(self.end_node != self.agv.target_node.id) else self.end_time - self.start_time
        self.agv.cost += cost_increase  # Cập nhật chi phí của AGV
        return cost_increase

    def re_calculate(self, path):
        cost = 0
        deltaCost = 0
        prev = 0
        M = self.graph.numberOfNodesInSpaceGraph 
        D = self.graph.graph_processor.d
        P = len(path)
        for i in range(P):
            node = path[i]
            real_node = node % M + (M if node % M == 0 else 0)
            #pdb.set_trace()
            t2 = node // M - (1 if node % M == 0 else 0)
            t1 = prev // M - (1 if prev % M == 0 else 0)
            deltaCost = self.graph.graph_processor.alpha*(t2 - t1)
            if(i != P - 1):
                #print('===', end='')
                if(i > 0):
                    # print('===', end='')                                                            
                    cost = cost + deltaCost
                    print(f'({deltaCost})===', end='')
                print(f'{real_node}===', end='')
            else:
                deltaCost = (float('inf') if(self.end_node != self.agv.target_node.id) else self.end_time - self.start_time)
                cost = cost + deltaCost
                print(f'({self.deltaT})/({deltaCost})==={real_node}===END. ', end='')
            prev = path[i]
        print(f'Total cost: {cost}. The AGV reaches its destination at {self.end_time}')
    
    def process(self):
        #pdb.set_trace()
        # Thực hiện cập nhật đồ thị khi xử lý sự kiện di chuyển
        #self.updateGraph()
        M = self.graph.graph_processor.M
        start = self.agv.path[0]
        space_start_node = start % M + (M if start % M == 0 else 0)
        space_end_node = self.end_node % M + (M if self.end_node % M == 0 else 0)
        print(
            f"AGV {self.agv.id} moves from {start}({space_start_node}) to {self.end_node}({space_end_node}) but time outs!!!!"
        )
        print(f'Because it left {self.start_node }({self.start_node % M + (M if self.start_node % M == 0 else 0)}) as {self.start_time} and spending {self.deltaT} for moving')
        self.re_calculate(self.agv.path)
        self.calculateCost()
        print(f"The total cost of {self.agv.id} is {self.agv.cost}")
        config.haltingAGVs = config.haltingAGVs + 1
        #self.getNext()
    
    def __str__(self):
        return f"HaltingEvent for {self.agv.id} because it leaves {self.start_node} at {self.start_time} and its finished time at {self.end_time}"

from .Event import Event
from discrevpy import simulator
import pdb
    
class StartEvent(Event):
    def __init__(self, start_time, end_time, agv, graph):
        super().__init__(start_time, end_time, agv, graph)
        print(self)

    def process(self):
        #pdb.set_trace()
        if(self.graph.graph_processor.print_out):
            print(f"StartEvent processed at time {self.start_time} for {self.agv.id}. The AGV is currently at node {self.agv.current_node}.")
        #self.determine_next_event()
        #self.getNext(True)
        self.getNext()
        
    def __str__(self):
        return f"StartEvent for {self.agv.id} to kick off its route from {self.agv.current_node} at {self.start_time}"
    
    def getNext(self, debug = False):
        self.solve()
        #next_vertex = self.agv.getNextNode()
        if(debug):
            pdb.set_trace()
        next_node = self.graph.nodes[self.agv.current_node]
        #new_event = next_node.getEventForReaching(self)
        new_event = next_node.goToNextNode(self)
        simulator.schedule(new_event.end_time, new_event.process)

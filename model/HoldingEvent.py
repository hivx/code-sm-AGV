from .Event import Event
import pdb
class HoldingEvent(Event):
    def __init__(self, start_time, end_time, agv, graph, duration):
        
        super().__init__(start_time, end_time, agv, graph)
        self.duration = duration
        #print("Create event")
        #self.largest_id = get_largest_id_from_map("map.txt")
        self.numberOfNodesInSpaceGraph = Event.get_value("numberOfNodesInSpaceGraph")
        #print(self)

    def updateGraph(self):
        # Calculate the next node based on the current node, duration, and largest ID
        current_node = self.agv.current_node if isinstance(self.agv.current_node, int) else self.agv.current_node.id
        next_node = current_node + (self.duration * self.numberOfNodesInSpaceGraph) + 1

        # Check if this node exists in the graph and update accordingly
        if next_node in self.graph.nodes:
            self.graph.update_node(current_node, next_node)
        else:
            #print("Calculated next node does not exist in the graph.")
            pass

        #self.agv.current_node = next_node

    def process(self):
        added_cost = self.calculateCost()
        # Assuming next_node is calculated or retrieved from some method
        #next_node = self.calculate_next_node()
        #pdb.set_trace() 
        #Lần 2 gọi get_next_node của AGV 
        #next_node = self.agv.get_next_node("""ended_event = True""")
        next_node = self.agv.get_next_node()
        #print(f"Processed HoldingEvent for AGV {self.agv.id}, added cost: {added_cost}, moving from node ID {self.agv.current_node} to node ID {next_node}")
        #self.agv.current_node = next_node  # Update the AGV's current node
        self.updateGraph()  # Optional, if there's a need to update the graph based on this event
        self.getNext()
        
    def __str__(self):
        return f"HoldingEvent for {self.agv.id} at {self.agv.current_node} in {self.duration}(s)"

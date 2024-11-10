from model.Edge import Edge
import inspect
import pdb
class RestrictionEdge(Edge):
    def __init__(self, start_node, end_node, edge, label):
        super().__init__(start_node, end_node, edge[2], edge[3], edge[4])
        self.label = label
        """current_frame = inspect.currentframe()
        # Lấy tên của hàm gọi my_function
        caller_name = inspect.getframeinfo(current_frame.f_back).function
        #if(self.graph.graph_processor.print_out):
        print(f'RestrictionEdge.py:12 {caller_name}')"""

    def make_permanent(self):
        # This method could be used to convert a temporary edge into a permanent one
        self.temporary = False
        print(f"RestrictionEdge from {self.start_node.id} to {self.end_node.id} made permanent.")

    def __repr__(self):
        return f"RestrictionEdge({self.start_node}, {self.end_node}, weight={self.weight}, restrictions={self.label})"

from model.Edge import Edge

class TimeWindowEdge(Edge):
    def __init__(self, start_node, end_node, weight, label):
        super().__init__(start_node, end_node, 0, 1, weight)
        self.label = label

    def __repr__(self):
        return f"TimeWindowEdge({self.start_node}, {self.end_node}, weight={self.weight}, label={self.label})"
    
    def make_permanent(self):
        # This method could be used to convert a temporary edge into a permanent one
        self.temporary = False
        print(f"TimeWindowEdge from {self.start_node.id} to {self.end_node.id} made permanent.")
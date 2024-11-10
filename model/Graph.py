import os
import pdb
from collections import deque, defaultdict
from model.utility import utility
import inspect
from controller.NodeGenerator import RestrictionNode
from controller.NodeGenerator import TimeWindowNode
from controller.NodeGenerator import TimeoutNode
from model.Node import Node
import config
from model.hallway_simulator_module.HallwaySimulator import BulkHallwaySimulator
import json

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
class Graph:
    def __init__(self, graph_processor):
        self.graph_processor = graph_processor 
        self.adjacency_list = defaultdict(list)
        self.nodes = {node.id: node for node in graph_processor.ts_nodes}
        self.adjacency_list = {node.id: [] for node in graph_processor.ts_nodes}
        self.list1 = []
        self.neighbour_list = {}
        self.visited = set()
        self.version = -1
        self.file_path = None
        self.cur = []
        self.map = {}
        self.number_of_nodes_in_space_graph = -1 if graph_processor is None else graph_processor.M
        self.calling = 0
        self.continue_debugging = True
        self.history = []
    def getReal(self, start_id, next_id, agv):
        from controller.NodeGenerator import TimeWindowNode
        M = self.number_of_nodes_in_space_graph
        result = -1
        
        real_start_id, old_real_path = self._get_real_start_id_and_path(start_id, agv, M)
        start_time, end_time = self._calculate_times(start_id, next_id, M)
        space_start_node, space_end_node = self._get_space_nodes(start_id, next_id, M)
        
        min_moving_time = self._get_min_moving_time(space_start_node, space_end_node)
        end_time = max(end_time, start_time + min_moving_time)

        if self._is_target_node(next_id):
            result = 0
            self._update_agv_path(agv, next_id)
        
        result = self._handle_special_cases(next_id, start_time, end_time, result)
        
        if config.sfm:
            result = self._calculate_sfm_runtime(space_start_node, space_end_node, agv, start_time, result)
        
        result = self._calculate_final_result(result, start_time, end_time)
        
        return self._handle_collisions(result, next_id, agv, M)

    def _get_real_start_id_and_path(self, start_id, agv, M):
        if agv is None:
            return start_id % M + (M if start_id % M == 0 else 0), []
        old_real_path = [(node % M + (M if node % M == 0 else 0)) for node in agv.path]
        real_start_id = start_id % M + (M if start_id % M == 0 else 0)
        if real_start_id in old_real_path:
            return real_start_id, old_real_path
        agv.path.add(start_id)
        return real_start_id, old_real_path

    def _calculate_times(self, start_id, next_id, M):
        start_time = start_id // M - (1 if start_id % M == 0 else 0)
        end_time = next_id // M - (1 if next_id % M == 0 else 0)
        return start_time, end_time

    def _get_space_nodes(self, start_id, next_id, M):
        space_start_node = start_id % M + (M if start_id % M == 0 else 0)
        space_end_node = next_id % M + (M if next_id % M == 0 else 0)
        return space_start_node, space_end_node

    def _get_min_moving_time(self, space_start_node, space_end_node):
        edges_with_cost = {
            (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])]
            for edge in self.graph_processor.space_edges
            if edge[3] == '0' and int(edge[4]) >= 1
        }
        return edges_with_cost.get((space_start_node, space_end_node), [-1, -1])[1]

    def _is_target_node(self, next_id):
        all_ids_of_target_nodes = [node.id for node in self.graph_processor.target_nodes]
        return next_id in all_ids_of_target_nodes

    def _update_agv_path(self, agv, node_id):
        if agv is not None:
            agv.path.add(node_id)

    def _handle_special_cases(self, next_id, start_time, end_time, result):
        from controller.NodeGenerator import TimeWindowNode
        try:
            if isinstance(self.nodes[next_id], TimeWindowNode):
                return end_time - start_time if result == -1 else result
        except KeyError:
            for e in self.graph_processor.ts_edges:
                if e[0] % self.number_of_nodes_in_space_graph == start_id % self.number_of_nodes_in_space_graph:
                    result = e[4] if result == -1 else result
            return abs(end_time - start_time) if result == -1 else result
        return result

    def _calculate_sfm_runtime(self, space_start_node, space_end_node, agv, start_time, result):
        runtime = self.getAGVRuntime(config.filepath, config.functions_file, space_start_node, space_end_node, agv, start_time)
        if runtime != -1:
            print(f"{bcolors.OKGREEN}{agv.id} from {space_start_node} to {space_end_node} at time {start_time} has runtime {runtime}.{bcolors.ENDC}")
            return runtime
        return result

    def _calculate_final_result(self, result, start_time, end_time):
        if result == -1:
            return 3 if (end_time - start_time <= 3) else 2 * (end_time - start_time) - 3
        return result

    def _handle_collisions(self, result, next_id, agv, M):
        all_ids_of_target_nodes = [node.id for node in self.graph_processor.target_nodes]
        collision = True
        while collision:
            collision = False
            if next_id not in all_ids_of_target_nodes and next_id in self.nodes:
                node = self.nodes[next_id]
                if node.agv and node.agv != agv:
                    print(f'{node.agv.id} != {agv.id}')
                    collision = True
                    result += 1
                    next_id += M
        return result
        
    def getReal_preprocess(self, Map_file, function_file):
        # read files
        map_data = None
        function_data = None
        with open(Map_file, 'r', encoding='utf-8') as file:
            map_data = file.readlines()
        with open(function_file, 'r', encoding='utf-8') as file:
            function_data = file.readlines()
        hallways_list = []
        functions_list = []
        for line in map_data:
            line = line.strip()
            parts = line.split(" ")
            if len(parts) == 8:
                hallway = {
                    "hallway_id": parts[6],
                    "length": int(int(parts[5]) * 0.6),
                    "width": 4,
                    "agents_distribution": int(parts[7]),
                    "src": int(parts[1]),
                    "dest": int(parts[2])
                }
                hallways_list.append(hallway)
        for line in function_data:
            line = line.strip()
            functions_list.append(line)
        return hallways_list, functions_list

    def getAGVRuntime(self, Map_file, function_file, start_id, next_id, agv, current_time):
        hallways_list, functions_list = self.getReal_preprocess(Map_file, function_file)
        agv_id = self._extract_agv_id(agv)
        direction, hallway_id = self._get_hallway_direction(hallways_list, start_id, next_id)
        
        if hallway_id is None:
            print(f"{bcolors.WARNING}Hallway not found!{bcolors.ENDC}")
            return -1

        events_list = self._create_event_list(agv_id, direction, current_time, hallway_id)
        hallways_list = self._filter_hallways_list(hallways_list, hallway_id, direction)
        
        return self._simulate_bulk_runtime(agv_id, hallway_id, hallways_list, functions_list, events_list)

    def _extract_agv_id(self, agv):
        return int(agv.id[3:])

    def _get_hallway_direction(self, hallways_list, start_id, next_id):
        for hallway in hallways_list:
            if hallway["src"] == start_id and hallway["dest"] == next_id:
                return 1, hallway["hallway_id"]
            elif hallway["src"] == next_id and hallway["dest"] == start_id:
                return 0, hallway["hallway_id"]
        return 0, None

    def _create_event_list(self, agv_id, direction, time_stamp, hallway_id):
        event = {
            "AgvIDs": [agv_id],
            "AgvDirections": [direction],
            "time_stamp": int(time_stamp),
            "hallway_id": hallway_id
        }
        return [event]

    def _filter_hallways_list(self, hallways_list, hallway_id, direction):
        return [
            hallway for hallway in hallways_list
            if hallway["hallway_id"] == hallway_id and (hallway["src"] - hallway["dest"]) * direction > 0
        ]

    def _simulate_bulk_runtime(self, agv_id, hallway_id, hallways_list, functions_list, events_list):
        bulk_sim = BulkHallwaySimulator("test", 3600, hallways_list, functions_list, events_list)
        result = bulk_sim.run_simulation()
        completion_time = result[agv_id][hallway_id]["completion_time"]
        print(f"{bcolors.OKGREEN}AGV {agv_id} has runtime {completion_time} in hallway {hallway_id}.{bcolors.ENDC}")
        return completion_time
#=======================================================================================================

    def count_edges(self):
        count = 0
        for node in self.adjacency_list:
            count = count + len(self.adjacency_list[node])
        return count
            
    def insertEdgesAndNodes(self, start, end, edge):
        from model.Node import Node
        start_id = start if isinstance(start, int) else start.id
        end_id = end if isinstance(end, int) else end.id
        self.adjacency_list[start_id].append((end_id, edge))
        start_node = start if isinstance(start, Node) else self.graph_processor.find_node(start)
        end_node = end if isinstance(end, Node) else self.graph_processor.find_node(end)
        if self.nodes[start_id] is None:
            self.nodes[start_id] = start_node
        if self.nodes[end_id] is None:
            self.nodes[end_id] = end_node
    
    def find_unique_nodes(self, file_path = 'traces.txt'):
        """ Find nodes that are only listed as starting nodes in edges. """
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return []
        
        target_ids = set()
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('a'):
                    parts = line.split()
                    target_ids.add(int(parts[3]))

        unique_ids = set()
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('a'):
                    parts = line.split()
                    node_id = int(parts[1])
                    if node_id not in target_ids:
                        unique_ids.add(node_id)

        return list(unique_ids)
    
    def find_unpredicted_node(self, id, forceFinding = False, isTargetNode = False):
        node = None
        idIsAvailable = id in self.nodes
        if idIsAvailable and not forceFinding:
            node = self.nodes[id]
        else:
            #if start == -1:
            found = False
            M = self.number_of_nodes_in_space_graph
            for x in self.nodes:
                if(x % M == id % M and (self.nodes[x].agv is not None or isTargetNode)):
                    if(idIsAvailable):
                        if(type(self.nodes[x]) == type(self.nodes[id])):
                            found = True
                    elif(isinstance(self.nodes[x], Node)\
                                and not isinstance(self.nodes[x], TimeWindowNode)\
                                    and not isinstance(self.nodes[x], RestrictionNode)):
                        found = True
                    if(found):
                        node = self.nodes[x]
                        break
        return node
        
    def build_path_tree(self, file_path = 'traces.txt'):
        """ Build a tree from edges listed in a file for path finding. """
        #pdb.set_trace()
        id1_id3_tree = defaultdict(list)
        M = self.number_of_nodes_in_space_graph
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('a'):
                    numbers = line.split()
                    id1 = int(numbers[1])
                    id3 = int(numbers[2])
                    id2 = id1 % M
                    id4 = id3 % M
                    node1 = self.find_unpredicted_node(id1) 
                    if (node1 is not None):
                        #pdb.set_trace()
                        isTargetNode = True
                        node3 = self.find_unpredicted_node(id3, node1.id != id1, isTargetNode)
                        if(node3 is None):
                            print(f"{node1.id}/{id1} {id3}")
                        id3 = node3.id
                        self.neighbour_list[id1] = id2
                        self.neighbour_list[id3] = id4
                        if(node1.id in self.graph_processor.started_nodes or\
                            node1.agv is not None):
                            #pdb.set_trace()
                            self.list1.append(node1.id)
                        id1_id3_tree[node1.id].append(node3)
                        id1_id3_tree[id3].append(node1)
        return id1_id3_tree

    def dfs(self, tree, start_node):
        self.visited.add(start_node)
        for node in tree[start_node]:
            node_id = node if isinstance(node, int) else node.id
            if node_id not in self.visited:
                #print(node, end=' ')
                self.cur.append(node)
                #self.id2_id4_list.append(self.neighbour_list[node_id])
                self.dfs(tree, node_id)

    def setTrace(self, file_path = 'traces.txt'):
        #pdb.set_trace()
        self.file_path = file_path #'traces.txt'
        self.list1 = []
        self.neighbour_list = {}
        self.visited = set()
        self.map = {}
        edges_with_cost = { (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])] for edge in self.graph_processor.space_edges \
            if edge[3] == '0' and int(edge[4]) >= 1 }
        M = self.graph_processor.M
        id1_id3_tree = self.build_path_tree()#self.list1 sẽ được thay đổi ở đâyđây
        for number in self.list1:
            if number not in self.visited:
                self.cur = []
                self.dfs(id1_id3_tree, number)
                self.visited = set()
                if len(self.cur) >= 1:
                    start = number % M + (M if number % M == 0 else 0)
                    end = self.cur[0].id % M + (M if self.cur[0].id % M == 0 else 0)
                    start_time = number // M - (1 if number % M == 0 else 0)
                    end_time = self.cur[0].id // M - (1 if self.cur[0].id % M == 0 else 0)
                    min_cost = edges_with_cost.get((start, end), [-1, -1])[1]
                    if(min_cost == -1):
                        need_to_remove_first_cur = True
                        if(start == end and number != self.cur[0].id and end_time - start_time == self.graph_processor.d):
                            need_to_remove_first_cur = False
                        if need_to_remove_first_cur:
                            found = False
                            for source_id, edges in self.graph_processor.time_window_controller.TWEdges.items():
                                if edges is not None and source_id % M == start:
                                    for index, e in enumerate(edges):
                                        if e[0].id ==end:
                                            found = True
                                            break
                            if(not found):                                    
                                self.cur = self.cur[1:]
                self.map[number] = self.cur #[1: ] if len(self.cur) > 1 else self.cur
    
    def getTrace(self, agv):
        #pdb.set_trace()
        idOfAGV = int(agv.id[3:])

        if idOfAGV in self.map:
            return self.map[idOfAGV]  
        else:
            found = False
            temp = []
            for id in self.nodes:
                if self.nodes[id].agv == agv:
                    #    pdb.set_trace()
                    if(id not in self.map):
                        for old_id in self.map.keys():
                            if(self.nodes[id].agv == self.nodes[old_id].agv):
                                temp = self.map[old_id]
                                found = True
                                break
                            else:
                                if isinstance(self.map[old_id], list):
                                    for node in self.map[old_id]:
                                        if node.agv == agv:
                                            temp = self.map[old_id]
                                            found = True
                                            break
                            if found:
                                break
                    else:
                        temp = self.map[id]#13899
                        found = True
                    node = self.nodes[id]
                    #    pdb.set_trace()
                    return [node, *temp]
                    #return s self.map[id]
        return None
    
    def has_initial_movement(self, node):
        # Check if there are any outgoing edges from 'node'
        return node in self.edges and len(self.edges[node]) > 0
    
    def update(self,currentpos,nextpos,realtime):
        list = utility()
        del self.matrix[currentpos,nextpos]
        q = deque()
        q.append(nextpos)
        while q:
            pos = q[0]
            q.pop()
            for i in list.findid(pos):
                if (pos,i) in self.matrix:
                    del self.matrix[pos,i]
                    q.append(i)
        nextpos = list.M*(int(currentpos/list.M)+ realtime) + list.getid(nextpos)
        self.matrix[currentpos,nextpos] = realtime
        q.append(nextpos)
        while q:
            pos = q[0]
            q.pop()
            for i in list.findid(pos):
                if (pos,i) not in self.matrix:
                    self.matrix[pos,i] = int((pos-i)/list.M)
                    q.append(i)      
              
    def update_node(self, node, properties):
        return
 
    def add_edge(self, from_node, to_node, weight):
        self.adjacency_list[from_node].append((to_node, weight))
        print(f"Edge added from {from_node} to {to_node} with weight {weight}.")

    def display_graph(self):
        print("Displaying graph structure:")
        for start_node in self.adjacency_list:
            for end, weight in self.adjacency_list[start_node]:
                print(f"{start_node} -> {end} (Weight: {weight})")
            
    def get_edge(self, start_node, end_node):
        for neighbor, weight in self.adjacency_list[start_node]:
            if neighbor == end_node:
                print(f"Edge found from {start_node} to {end_node} with weight {weight}.")
                return weight
        print(f"No edge found from {start_node} to {end_node}.")
        return None
    
    def find_edge_by_weight(self, start_node, weight):
        # Find all edges from a node with a specific weight
        return [edge for edge in self.edges if edge.start_node == start_node and edge.weight == weight]
    
    def find_path(self, start_node, end_node):
        # Placeholder for a pathfinding algorithm like Dijkstra's
        queue = deque([start_node])
        visited = set()
        path = []
        
        while queue:
            node = queue.popleft()
            if node == end_node:
                break
            visited.add(node)
            for neighbor, weight in self.adjacency_list[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
                    path.append((node, neighbor, weight))
        return path
    
    def update_graph(self, id1=-1, id2=-1, end_id=-1, agv_id=None):
        """Cập nhật đồ thị với thông tin cạnh mới."""
        ID1, ID2, endid = self.get_ids(id1, id2, end_id)
        M = self.number_of_nodes_in_space_graph
        current_time, new_node_id = self.calculate_times(ID1, ID2, endid, M)

        self.process_adjacency_list(current_time, new_node_id, M)
        
        q = self.update_new_started_nodes(new_node_id)
        new_edges = self.graph_processor.insert_from_queue(q, self.adjacency_list)
        self.process_new_edges(new_edges)

        if self.version_check(current_time):
            self.version += 1

        new_halting_edges = self.collect_new_halting_edges()
        self.write_to_file([agv_id, new_node_id], new_halting_edges)

    def get_ids(self, id1, id2, end_id):
        """Nhận ID từ người dùng hoặc sử dụng giá trị mặc định."""
        ID1 = int(input("Nhap ID1: ")) if id1 == -1 else id1
        ID2 = int(input("Nhap ID2: ")) if id2 == -1 else id2
        endid = int(input("Nhap ID thực sự khi AGV kết thúc hành trình: ")) if end_id == -1 else end_id
        return ID1, ID2, endid

    def calculate_times(self, ID1, ID2, endid, M):
        """Tính thời gian và ID nút mới."""
        time2 = ID1 // M - (1 if ID1 % M == 0 else 0)
        current_time = endid // M - (1 if endid % M == 0 else 0)
        new_node_id = current_time * M + (M if ID2 % M == 0 else ID2 % M)
        return current_time, new_node_id

    def process_adjacency_list(self, current_time, new_node_id, M):
        """Duyệt qua từng phần tử của adjacency_list và cập nhật thông tin."""
        for source_id, edges in list(self.adjacency_list.items()):
            isContinued = any(node.id == source_id for node in self.graph_processor.target_nodes)
            if isContinued:
                continue

            if source_id in self.nodes:
                node = self.nodes[source_id]
                time = source_id // M - (1 if source_id % M == 0 else 0)
                if time < current_time and not isinstance(node, (TimeWindowNode, RestrictionNode)):
                    self.update_nodes(source_id, current_time, M)

    def update_nodes(self, source_id, current_time, M):
        """Cập nhật thông tin nút và xóa khỏi danh sách."""
        del self.adjacency_list[source_id]
        if self.nodes[source_id].agv is not None:
            space_id = M if (source_id % M == 0) else source_id % M
            new_source_id = current_time * M + space_id
            self.transfer_agv(source_id, new_source_id)
        del self.nodes[source_id]

    def transfer_agv(self, source_id, new_source_id):
        """Chuyển AGV từ nút cũ sang nút mới."""
        try:
            if new_source_id in self.nodes:
                self.nodes[new_source_id].agv = self.nodes[source_id].agv
            index = self.graph_processor.started_nodes.index(source_id)
            self.graph_processor.started_nodes[index] = new_source_id
        except ValueError:
            pass

    def update_new_started_nodes(self, new_node_id):
        """Cập nhật danh sách các nút mới bắt đầu và trả về hàng đợi."""
        q = deque([new_node_id])
        new_started_nodes = self.getAllNewStartedNodes()
        for start in new_started_nodes:
            if start != new_node_id:
                q.append(start)
        return q

    def process_new_edges(self, new_edges):
        """Xử lý và cập nhật các cạnh mới vào đồ thị."""
        for edge in new_edges:
            arr = self.parse_string(edge)
            source_id, dest_id = arr[0], arr[1]
            self.add_edge_to_graph(source_id, dest_id, arr)

    def add_edge_to_graph(self, source_id, dest_id, arr):
        """Thêm một cạnh mới vào đồ thị."""
        if source_id not in self.nodes:
            self.nodes[source_id] = self.graph_processor.find_node(source_id)
        if dest_id not in self.nodes:
            self.nodes[dest_id] = self.graph_processor.find_node(dest_id)

        if source_id not in self.adjacency_list:
            self.adjacency_list[source_id] = []
        
        found = any(end_id == dest_id for end_id, _ in self.adjacency_list[source_id])
        if not found:
            anEdge = self.nodes[source_id].create_edge(self.nodes[dest_id], self.graph_processor.M, self.graph_processor.d, [source_id, dest_id, arr[2], arr[3], arr[4]])
            self.adjacency_list[source_id].append([dest_id, anEdge])
        
        # Add TimeWindowEdge and RestrictionEdge
        self.graph_processor.time_window_controller.generate_time_window_edges(self.nodes[source_id], self.adjacency_list, self.number_of_nodes_in_space_graph)
        self.graph_processor.restriction_controller.generate_restriction_edges(self.nodes[source_id], self.nodes[dest_id], self.nodes, self.adjacency_list)

    def version_check(self, current_time):
        """Kiểm tra nếu phiên bản cần được cập nhật."""
        time2 = self.number_of_nodes_in_space_graph // self.graph_processor.M - (1 if self.number_of_nodes_in_space_graph % self.graph_processor.M == 0 else 0)
        return time2 != current_time

    def collect_new_halting_edges(self):
        """Thu thập các cạnh dừng mới cần được thêm vào."""
        sorted_edges = sorted(self.adjacency_list.items(), key=lambda x: x[0])
        new_nodes = set()
        new_halting_edges = []

        for source_id, edges in sorted_edges:
            for edge in edges:
                t = edge[0] // self.graph_processor.M - (1 if edge[0] % self.graph_processor.M == 0 else 0)
                if t >= self.graph_processor.H and edge[0] not in new_nodes and isinstance(self.nodes[edge[0]], TimeoutNode):
                    new_nodes.add(edge[0])
                    for target in self.graph_processor.get_targets():
                        dest_id = target.id
                        new_halting_edges.append([edge[0], dest_id, 0, 1, self.graph_processor.H * self.graph_processor.H])

        return new_halting_edges

    def reset_agv(self, real_node_id, agv):
        for node_id in self.nodes.keys():
            if(node_id != real_node_id):
                if self.nodes[node_id].agv == agv:
                    self.nodes[node_id].agv = None
        self.nodes[real_node_id].agv = agv
    
    def parse_string(self, input_string):
        parts = input_string.split()
        if len(parts) != 6 or parts[0] != "a":
            return None  # Chuỗi không đúng định dạng
        try:
            ID1, ID2, L, U, C = map(int, parts[1:])
            return [ID1, ID2, L, U, C]
        except ValueError:
            return None  # Không thể chuyển thành số nguyên
    
    def get_current_node(self, agv_id_and_new_start, start):
        if(agv_id_and_new_start is None):
            return start
        if agv_id_and_new_start[0] == f'AGV{str(start)}':
            #print(agv_id_and_new_start[1])
            return agv_id_and_new_start[1]
        return start
    
    def getAllNewStartedNodes(self, excludedAgv = None):
        from model.AGV import AGV
        allAGVs = AGV.all_instances()
        started_nodes = set()
        from controller.EventGenerator import ReachingTargetEvent
        for agv in allAGVs:
            if(not isinstance(agv.event, ReachingTargetEvent)):
                started_nodes.add(agv.current_node)
        if(len(started_nodes) == 0):
            return self.graph_processor.started_nodes
        return started_nodes
        
    def write_to_file(self, agv_id_and_new_start = None, new_halting_edges = None, filename="TSG.txt"):
        #self.calling = self.calling + 1rite
        #print("Call write_to_file of Graph.py")
        #if(config.count == 2):
        #    pdb.set_trace()
        M = max(target.id for target in self.graph_processor.get_targets())
        m1 = max(edge[1] for edge in new_halting_edges)
        M = max(M, m1)
        num_halting_edges = len(new_halting_edges) if new_halting_edges is not None else 0
        #pdb.set_trace()
        sorted_edges = sorted(self.adjacency_list.items(), key=lambda x: x[0])
        num_edges = self.count_edges()
        num_edges = num_edges + num_halting_edges
        
        with open(filename, 'w') as file:
            file.write(f"p min {M} {num_edges}\n")
            #    pdb.set_trace()
            
            started_nodes = self.getAllNewStartedNodes()

            for start_node in started_nodes:
                file.write(f"n {start_node} 1\n")
            for target in self.graph_processor.get_targets():
                target_id = target.id
                file.write(f"n {target_id} -1\n")
            #for edge in self.ts_edges:
            #for edge in self.tsedges:
            new_nodes = set()
            for source_id, edges in sorted_edges:
                for edge in edges:
                    t = edge[0] // self.graph_processor.M - (1 if edge[0] % self.graph_processor.M == 0 else 0)
                    file.write(f"a {source_id} {edge[0]} {edge[1].lower} {edge[1].upper} {edge[1].weight}\n")  
            for edge in new_halting_edges:
                file.write(f"a {edge[0]} {edge[1]} {edge[2]} {edge[3]} {edge[4]}\n")

    def remove_node_and_origins(self, node_id):
        from model.Node import Node
        node = None
        if isinstance(node_id, Node):
            node = node_id
        elif node_id in self.nodes:
            node = self.nodes[node_id]
        else:
            return
        node = node_id if isinstance(node_id, Node) else self.nodes[node_id]
        R = [node]  # Khởi tạo danh sách R với nút cần xóa
        while R:  # Tiếp tục cho đến khi R rỗng
            current_node = R.pop()  # Lấy ra nút cuối cùng từ R
            if current_node.id in self.nodes:  # Kiểm tra xem nút có tồn tại trong đồ thị hay không
                del self.nodes[current_node.id]  # Nếu có, xóa nút khỏi danh sách các nút
            for id in self.adjacency_list:
                edges = []
                found = False
                for end_id, edge in self.adjacency_list[id]:
                    if(end_id == node.id):
                        #del self.adjacency_list
                        found = True
                    else:
                        edges.append([end_id, edge])
                if(found):
                    self.adjacency_list[id] = edges
            #self.edges.pop(current_node, None)  # Xóa tất cả các cạnh liên kết với nút này
            #for edge_list in self.edges.values():  # Duyệt qua tất cả các cạnh còn lại trong đồ thị
            #    edge_list[:] = [(n, w) for n, w in edge_list if n != current_node]  # Loại bỏ nút khỏi danh sách các nút kết nối với mỗi cạnh
            # Thêm các nút chỉ được dẫn đến bởi nút hiện tại vào R
            #R.extend([n for n in self.edges if all(edge[0] == current_node for edge in self.edges[n])])

    def remove_edge(self, start_node, end_node, agv_id):
        if (start_node, end_node) in self.edges:
            del self.edges[(start_node, end_node)]
            self.lastChangedByAGV = agv_id  # Update the last modified by AGV

    def handle_edge_modifications(self, start_node, end_node, agv):
        # Example logic to adjust the weights of adjacent edges
        print(f"Handling modifications for edges connected to {start_node} and {end_node}.")
        #pdb.set_trace()
        adjacent_nodes_with_weights = self.adjacency_list.get(end_node, [])
        # Check adjacent nodes and update as necessary
        for adj_node, weight in adjacent_nodes_with_weights:
            if (end_node, adj_node) not in self.lastChangedByAGV or self.lastChangedByAGV[(end_node, adj_node)] != agv.id:
                # For example, increase weight by 10% as a traffic delay simulation
                new_weight = int(weight * 1.1)
                self.adjacency_list[end_node][adj_node] = new_weight
                print(f"Updated weight of edge {end_node} to {adj_node} to {new_weight} due to changes at {start_node}.")
    
    def __str__(self):
        return "\n".join(f"{start} -> {end} (Weight: {weight})" for start in self.adjacency_list for end, weight in self.adjacency_list[start])


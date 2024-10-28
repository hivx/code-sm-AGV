import os
import re
import json
from model.Edge import Edge
from model.Edge import HoldingEdge
from model.Edge import MovingEdge
from model.Edge import ArtificialEdge
from model.TimeoutNode import TimeoutNode
from model.ArtificialNode import ArtificialNode
from model.TimeWindowNode import TimeWindowNode
from model.RestrictionNode import RestrictionNode
from model.RestrictionController import RestrictionController
from model.Node import Node
from collections import deque
from scipy.sparse import lil_matrix
import numpy as np
import pdb
import config
"""
Mô tả yêu cầu của code:
https://docs.google.com/document/d/13S_Ycg-aB4GjEm8xe6tAoUHzhS-Z1iFnM4jX_bWFddo/edit?usp=sharing
"""

class GraphProcessor:
    def __init__(self):
        self.adj = []  # Adjacency matrix
        self.M = 0
        self.H = 0
        self.d = 0
        self.alpha = 1
        self.beta = 1
        self.gamma = 1
        self.ID = []
        self.earliness = 0
        self.tardiness = 0
        self.space_edges = []
        self.ts_edges = []
        self.ts_nodes = []
        self.tsedges = []
        self.started_nodes = []
        self._target_nodes = []
        self.print_out = True
        self.time_window_controller = None 
        self.restriction_controller = None
        self.start_ban = -1
        self.end_ban = -1
        self._seed = 0
        self.num_max_agvs = 0

        
    @property
    def target_nodes(self):
        return self._target_nodes
    
    @target_nodes.setter
    def target_nodes(self, value):
        self._target_nodes = value
    
    def append_target(self, target_node):
        if isinstance(target_node, TimeWindowNode):
            #pdb.set_trace()
            pass
        self._target_nodes.append(target_node)
        
    def get_targets(self, index = -1):
        if (index != -1):
            return self._target_nodes[index]
        return self._target_nodes
    
    def get_target_by_id(self, id):
        for node in self._target_nodes:
            if(node.id == id):
                return node
        return None
        
    def process_input_file(self, filepath):
        self.space_edges = []
        try:
            with open(filepath, 'r') as file:
                self.M = 0
                for line in file:
                    parts = line.strip().split()
                    if parts[0] == 'a' and len(parts) >= 6:
                        id1, id2 = int(parts[1]), int(parts[2])
                        self.space_edges.append(parts)
                        self.M = max(self.M, id1, id2)
                    elif parts[0] == 'n':
                        if(parts[2] == '1'):
                            self.started_nodes.append(int(parts[1]))
                        if(parts[2] == '-1'):
                            self.ID.append(int(parts[1]))
                            if isinstance(self.earliness, int):
                                self.earliness = []
                            if isinstance(self.tardiness, int):
                                self.tardiness = []
                            self.earliness.append(int(parts[3]))
                            self.tardiness.append(int(parts[4]))
                    elif parts[0] == 'alpha':
                        self.alpha = int(parts[1])
                    elif parts[0] == 'beta':
                        self.beta = int(parts[1])
            if(self.print_out):
                print("Doc file hoan tat, M =", self.M)
        except FileNotFoundError:
            if(self.print_out):
                print("File khong ton tai!")
            return

    def find_node(self, _id):
        _id = int(_id)
        # Tìm kiếm đối tượng Node có ID tương ứng
        """for node in self.ts_nodes:
            if node.id == id:
                return node
        # Nếu không tìm thấy, tạo mới và thêm vào danh sách
        new_node = Node(id)
        self.ts_nodes.append(new_node)
        return new_node"""
        if not hasattr(self, 'map_nodes'):
            # Nếu chưa tồn tại, chuyển self.ts_nodes thành self.map_nodes
            self.map_nodes = {node.id: node for node in self.ts_nodes}
        # Tìm kiếm trên self.map_nodes
        if _id in self.map_nodes:
            return self.map_nodes[_id]
        else:
            # Nếu không có trên map_nodes, thêm vào cả ts_nodes và map_nodes
            #if(id == 26272):
            #    pdb.set_trace()
            for node in self._target_nodes:
                if(node.id == _id):
                    self.map_nodes[_id] = node
                    return node
            time = _id // self.M - (1 if _id % self.M == 0 else 0)
            new_node = None
            if(time >= self.H):
                new_node = TimeoutNode(_id, "TimeOut")
            else:
                new_node = Node(_id)
            self.ts_nodes.append(new_node)
            self.map_nodes[_id] = new_node
            
            return new_node
	
    def generate_hm_matrix(self):
        self.matrix = [[j + 1 + self.M * i for j in range(self.M)] for i in range(self.H)]
        if(self.print_out):
            print("Hoan tat khoi tao matrix HM!")
        #     print(' '.join(map(str, row)))

    def generate_adj_matrix(self):
        size = (self.H + 1) * self.M + 1
        self.adj = lil_matrix((2*size, 2*size), dtype=int)

        for edge in self.space_edges:
            if len(edge) >= 6 and edge[3] == '0' and int(edge[4]) >= 1:
                u, v, c = int(edge[1]), int(edge[2]), int(edge[5])
                for i in range(self.H + 1):
                    source_idx = i * self.M + u
                    target_idx = (i + c) * self.M + v
                    if(self.print_out):
                        print(f"i = {i} {source_idx} {target_idx} = 1")

                    if source_idx < size and target_idx < size:
                        self.adj[source_idx, target_idx] = 1
                    elif source_idx < size and target_idx >= size and target_idx < 2*size: 
                        self.adj[source_idx, target_idx] = 1

        for i in range(size):
            j = i + self.M * self.d
            if j < size and (i % self.M == j % self.M):
                self.adj[i, j] = 1

        if(self.print_out):
            print("Hoan tat khoi tao Adjacency matrix!")

        rows, cols = self.adj.nonzero()
        with open('adj_matrix.txt', 'w') as file:
            for i, j in zip(rows, cols):
                file.write(f"({i}, {j})\n")
        if(self.print_out):
            print("Cac cap chi so (i,j) khac 0 cua Adjacency matrix duoc luu tai adj_matrix.txt.")

    def check_and_add_nodes(self, args, is_artificial_node = False, label = ""):
        if not hasattr(self, 'map_nodes'):
            # Nếu chưa tồn tại, chuyển self.ts_nodes thành self.map_nodes
            self.map_nodes = {node.id: node for node in self.ts_nodes}
        for id in args:
            # Ensure that Node objects for id exist in ts_nodes
            if not any(node.id == id for node in self.ts_nodes) and isinstance(id, int):
                if(is_artificial_node):
                   if(label == "TimeWindow"):
                       temp = TimeWindowNode(id, label)
                       self.ts_nodes.append(temp)
                       self.map_nodes[id] = temp
                   elif(label == "Restriction"):
                       temp = RestrictionNode(id, label)
                       self.ts_nodes.append(temp)
                       self.map_nodes[id] = temp
                   elif (label == "Timeout"):
                       temp = TimeoutNode(id, label)
                       self.ts_node.append(temp)
                       self.map_nodes[id] = temp
                   else:
                       temp = ArtificialNode(id, label)
                       self.ts_nodes.append(temp)
                       self.map_nodes[id] = temp
                else:
                    time = id // self.M - (1 if id % self.M == 0 else 0)
                    temp = None
                    if(time >= self.H):
                        temp = TimeoutNode(id, "Timeout")
                    else:
                        temp = Node(id)
                    self.ts_nodes.append(temp)
                    self.map_nodes[id] = temp
        #    self.ts_nodes.append(Node(ID2))

    def show(self, Q):
        if len(Q) < 10:
            return list(Q)
        else:
            return list(Q)[:5] + ["..."]

    def insert_from_queue(self, Q, checking_list = None):
        #pdb.set_trace()
        output_lines = []
        edges_with_cost = { (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])] for edge in self.space_edges \
            if edge[3] == '0' and int(edge[4]) >= 1 }
        ts_edges = self.ts_edges if checking_list == None else \
            [[item[1].start_node.id, item[1].end_node.id] for sublist in checking_list.values() for item in sublist]
        #[[edge.start_node, end_node] for (end_node, edge) in checking_list.values()]
        var_value = os.environ.get('PRINT')
        count = 0
        my_dict = {element: 1 for element in Q}
        while Q:
            #if var_value == 'insert_from_queue' or True:
                # Thực hiện khối lệnh của bạn ở đây
            if(count % 1000 == 0):
                #print(f'Vòng lặp thứ {count} và Q có {len(Q)}')
                pass
            count = count + 1
            ID = Q.popleft()
            #print(Q)
            if ID < 0 or ID >= self.adj.shape[0]:
                continue
            
            for j in self.adj.rows[ID]:  # Direct access to non-zero columns for row ID in lil_matrix
                if(not any(edge[0] == ID and edge[1] == j for edge in ts_edges)):
                    #Q.append(j)
                    if j in Q:
                        #print(f'\t{j} đã tồn tại trong {self.show(Q)}')
                        if any(line.startswith(f"a {ID} {j} 0") for line in output_lines):
                            continue
                    else:
                        Q.append(j)
                    u, v = ID % self.M, j % self.M
                    u = u if u != 0 or ID == 0 else self.M
                    #if(v == 0):
                    #if (ID == 1 and j == 11):
                        #pdb.set_trace()
                    v = v if v != 0 or ID == 0 else self.M
                    temp = None
                    #start_time = (ID // self.M) if (ID // self.M) != 0 else ID
                    #if (start_time + edges_with_cost.get((u, v), -1) == j // self.M) and ((u, v) in edges_with_cost):
                    if ((ID // self.M) + edges_with_cost.get((u, v), (-1, -1))[1] == (j // self.M) - (v//self.M)) and ((u, v) in edges_with_cost):
                        [upper, c] = edges_with_cost[(u, v)]
                        if ID // self.M >= self.H:
                            output_lines.append(f"a {ID} {j} 0 1 {c} Exceed")
                        else:
                            output_lines.append(f"a {ID} {j} 0 {upper} {c}")
                        if(checking_list == None):
                            self.ts_edges.append((ID, j, 0, upper, c))
                        self.check_and_add_nodes([ID, j])
                        #    pdb.set_trace()
                            #print()
                        temp = self.find_node(ID).create_edge(self.find_node(j), self.M, self.d, [ID, j, 0, upper, c])
                    elif ID + self.M * self.d == j and ID % self.M == j % self.M:
                        output_lines.append(f"a {ID} {j} 0 1 {self.d}")
                        if(checking_list == None):
                            self.ts_edges.append((ID, j, 0, 1, self.d))
                        self.check_and_add_nodes([ID, j])
                        #self.tsedges.append(HoldingEdge(self.find_node(ID), self.find_node(j), self.d, self.d))
                        temp = self.find_node(ID).create_edge(self.find_node(j), self.M, self.d, [ID, j, 0, 1, self.d])
                    """elif edges_with_cost.get((u, v), (-1, -1))[1] != -1 and (ID // self.M + edges_with_cost.get((u, v), (-1, -1))[1] >= self.H - (1 if ID % self.M == 0 else 0)):
                        [upper, c] = edges_with_cost[(u, v)]
                        #c = abs(self.H 
                        output_lines.append(f"a {ID} {j} 0 {upper} {self.H}")
                        if(checking_list == None):
                            self.ts_edges.append((ID, j, 0, upper, self.H))
                            self.check_and_add_nodes([ID, j], True, "Timeout")"""
                    if(temp != None):
                        if(checking_list == None):
                            self.tsedges.append(temp)
        if(checking_list == None):
            assert len(self.ts_edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self._edges)} != {len(self.ts_edges)}"
        return output_lines

    def create_tsg_file(self):          
        #pdb.set_trace()
        Q = deque()
        Q.extend(self.started_nodes)

        #pdb.set_trace()
        output_lines = self.insert_from_queue(Q)
        with open('TSG.txt', 'w') as file:
            for line in output_lines:
                file.write(line + "\n")
        if(self.print_out):
            print("TSG.txt file created.")

    def init_agvs_n_events(self, all_agvs, events, graph):
        from model.StartEvent import StartEvent
        from model.AGV import AGV
        for node_id in self.started_nodes:
            #pdb.set_trace()
            agv = AGV("AGV" + str(node_id), node_id, graph)  # Create an AGV at this node
            #print(Event.getValue("numberOfNodesInSpaceGraph"))
            start_time = node_id // self.M
            end_time = start_time
            start_event = StartEvent(start_time, end_time, agv, graph)  # Start event at time 0
            events.append(start_event)
            all_agvs.add(agv)  # Thêm vào tập hợp AGV
    
    def init_tasks(self, tasks):
        for node_id in self.getTargets():
            tasks.add(node_id)
    
    def query_edges_by_source_id(self):
        source_id = int(input("Nhap vao ID nguon: "))

        edges = []
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] == 'a' and int(parts[1]) == source_id:
                        edges.append(line.strip())
        except FileNotFoundError:
            if(self.print_out):
                print("File TSG.txt khong ton tai!")
            return

        if edges:
            if(self.print_out):
                print(f"Cac canh co ID nguon la {source_id}:")
            for edge in edges:
                print(edge)
        else:
            if(self.print_out):
                print(f"Khong tim thay canh nao co ID nguon la {source_id}.")

    def init_nodes_n_edges(self, graph):
        for edge in self.tsedges:
            if edge is not None:
                graph.insertEdgesAndNodes(edge.start_node, edge.end_node, edge)
    
    def check_file_conditions(self):
        try:
            seen_edges = set()
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] != 'a':
                        continue
                    ID1, ID2 = int(parts[1]), int(parts[2])

                    # Condition 1: ID1 should not equal ID2
                    if ID1 == ID2:
                        print("False")
                        return

                    # Condition 2: If ID1 before ID2, then ID2 should not come before ID1
                    if (ID1, ID2) in seen_edges or (ID2, ID1) in seen_edges:
                        print("False")
                        return
                    else:
                        seen_edges.add((ID1, ID2))

                    # Condition 3: ID2/self.M should be greater than ID1/self.M
                    if ID2 // self.M <= ID1 // self.M:
                        print("False")
                        return

            print("True")
        except FileNotFoundError:
            print("File TSG.txt khong ton tai!")

    def update_file(self, id1 = -1, id2 = -1, c12 = -1):
        ID1 = int(input("Nhap ID1: ")) if id1 == -1 else id1
        ID2 = int(input("Nhap ID2: ")) if id2 == -1 else id2
        C12 = int(input("Nhap trong so C12: ")) if c12 == -1 else c12

        i1, i2 = ID1 // self.M, ID2 // self.M
        if i2 - i1 != C12:
            print('Status: i2 - i1 != C12')
            ID2 = ID1 + self.M * C12

        existing_edges = set()
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    try:
		     # Chỉ xử lý các dòng có ít nhất 3 phần tử và bắt đầu bằng 'a'
                        if parts[0] == 'a' and len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                            existing_edges.add((int(parts[1]), int(parts[2])))
                    except ValueError:
                    # Bỏ qua các dòng không thể chuyển đổi sang số nguyên
                        continue
                    except IndexError:
                    # Bỏ qua các dòng không có đủ phần tử
                        continue
                    #existing_edges.add((int(parts[1]), int(parts[2])))
        except FileNotFoundError:
            print("File TSG.txt khong ton tai!")
            return

        if (ID1, ID2) not in existing_edges:
            Q = deque([ID2])
            visited = {ID2}
            new_edges = [(ID1, ID2, C12)]
            pdb.set_trace()

            while Q:
                ID = Q.popleft()
                for j in self.adj.rows[ID]:
                    if j not in visited:
                        c = self.d if ID + self.M * self.d == j and ID % self.M == j % self.M else C12
                        if (ID // self.M) + c == j // self.M:
                            new_edges.append((ID, j, c))
                            Q.append(j)
                            visited.add(j)
                            
            edges_with_cost = { (int(edge[1]), int(edge[2])): [int(edge[4]), int(edge[5])] for edge in self.space_edges \
                       if edge[3] == '0' and int(edge[4]) >= 1 }
            with open('TSG.txt', 'a') as file:
                for ID, j, c in new_edges:
                    u, v = ID % self.M + (self.M if ID % self.M == 0 else 0), j % self.M + (self.M if j % self.M == 0 else 0)
                    [upper, cost] = edges_with_cost[(u, v)] 
                    file.write(f"a {ID} {j} 0 {upper} {c}\n")
            print("Da cap nhat file TSG.txt.")

    def add_restrictions(self):
        alpha = input("Nhập vào alpha: ")
        beta = input("Nhập vào beta: ")
        gamma = input("Nhập vào gamma: ")
        self.alpha = int(alpha) if alpha else 1
        self.beta = int(beta) if beta else 1
        self.gamma = int(gamma) if gamma else 1
        restriction_count = input("Hãy nhập số lượng các restriction: ")
        self.restriction_count = int(restriction_count) if restriction_count else 1
        start_ban, end_ban = map(int, input("Khung thời gian cấm (nhập hai số phân tách bằng khoảng trắng a b): ").split())
        self.start_ban = start_ban
        self.end_ban = end_ban
        self.restrictions = []

        for i in range(self.restriction_count):
            print(f"Restriction {i + 1}:")
            u, v = map(int, input("\tKhu vực cấm (nhập hai số phân tách bằng khoảng trắng a b): ").split())

            self.restrictions.append((u, v))
        self.ur = int(input("Số lượng hạn chế: "))

    def create_set_of_edges(self, edges, label = None):
        for e in edges:
            #self.tsedges.append(ArtificialEdge(self.find_node(e[0]), self.find_node(e[1]), e[4]))
            temp = self.find_node(e[0]).create_edge(self.find_node(e[1]), self.M, self.d, e)
            self.tsedges.append(temp)
        
    def process_restrictions(self):
        #pdb.set_trace()
        S = set()
        R = []
        new_a = set()
        if(self.restriction_controller == None):
            self.restriction_controller = RestrictionController(self)
        start_ban = self._ban
        end_ban = self.end_ban #16, 30  # Giả sử giá trị cố định cho ví dụ này
        
        edges_with_cost = { (int(edge[1]), int(edge[2])): int(edge[5]) \
                           for edge in self.space_edges if edge[3] == '0' and int(edge[4]) >= 1 }
        max = self.get_max_id() + 1
        # Xác định các điểm bị cấm
        for restriction in self.restrictions:
            R = []
            for time in range(start_ban, end_ban + 1):
                edge = []
                #S.add(point)
                time_space_point_0 = time*self.M + restriction[0]
                cost = edges_with_cost.get((restriction[0], restriction[1]), -1)
                time_space_point_1 = (time + cost)*self.M + restriction[1]
                edge.append(time_space_point_0)
                edge.append(time_space_point_1)
                edge.append(cost)
                R.append(edge)
                self.adj[edge[0], edge[1]] = 0

            # Xử lý các cung cấm
            #for edge in self.space_edges:
                #ID1, ID2 = int(edge[1]), int(edge[2])
                #t1, u, v, t2 = ID1 // self.M, ID1 % self.M, ID2 % self.M, ID2 // self.M
                #if (u in S and v in S):
                    #if ((t1 <= end_ban and end_ban <= t2) or (t1 <= start_ban and start_ban <= t2) or (t1 <= start_ban and end_ban <= t2)):
                        #R.add((ID1, ID2))
            assert len(self._edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self.ts_edges)} != {len(self.ts_edges)}"
            self.ts_edges = [e for e in self._edges if [e[0], e[1]] not in [r[:2] for r in R]]
            size1 = len(self.tsedges)
            self.tsedges = [e for e in self.tsedges if [e.start_node.id, e.end_node.id] not in [r[:2] for r in R]]
            size2 = len(self.tsedges)
            #assert (size1 == size2 + len(R)), f"Số lượng self.ts_edges phải bị thay đổi, nhưng size1 = {size1}, size2 = {size2} và {len(R)}"
            #self.create_tsg_file()
            # Tạo các cung mới dựa trên các cung cấm
            if R:
                a_s, a_t, a_sub_t = Max, Max + 1, Max + 2
                #pdb.set_trace()
                self.check_and_add_nodes([a_s, a_t, a_sub_t], True, "Restriction")
                self.restriction_controller.\
                    add_nodes_and_ReNode(time_space_point_0, time_space_point_1, restriction, a_s, a_t)
                Max += 3
                e1 = (a_s, a_t, 0, self.H, int(self.gamma/self.alpha))
                e2 = (a_s, a_sub_t, 0, self.ur, 0)
                e3 = (a_sub_t, a_t, 0, self.H, 0)
                new_a.update({e1, e2, e3})
                #print(R)
                for e in R:
                    e4 = (e[0], a_s, 0, 1, 0)
                    e5 = (a_t, e[1], 0, 1, e[2])
                    new_a.update({e4, e5})
            self.ts_edges.extend(e for e in new_a if e not in self.ts_edges)
            self.create_set_of_edges(new_a)
            assert len(self.ts_edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self.ts_edges)} != {len(self.tsedges)}"
        self.ts_edges = sorted(self.ts_edges, key=lambda edge: (edge[0], edge[1]))
        #pdb.set_trace()
        #halting_nodes = 
        self.insert_halting_edges()
        
        self.write_to_file(Max)
        #pdb.set_trace()
        
    def insert_halting_edges(self):
        halting_nodes = set()
        for edge in self.tsedges:
            if(isinstance(edge.end_node, TimeWindowNode)):
                continue
            time = edge.end_node.id // self.M - (1 if edge.end_node.id % self.M == 0 else 0)
            #    pdb.set_trace()
            if(time >= self.H):
                halting_nodes.add(edge.end_node.id)
        targets = self.getTargets()
        new_a = set()
        for h_node in halting_nodes:
            for target in targets:
                e = (h_node, target.id, 0, 1, self.H*self.H)
                new_a.update({e})
        self.ts_edges.extend(e for e in new_a if e not in self.ts_edges)
        self.create_set_of_edges(new_a)
    
    def write_to_file(self, max, filename = "TSG.txt"):
        M = max(target.id for target in self.getTargets())
        with open('TSG.txt', 'w') as file:
            file.write(f"p min {M} {len(self.ts_edges)}\n")
            for start in self.started_nodes:
                file.write(f"n {start} 1\n")
            for target in self.getTargets():
                target_id = target.id
                file.write(f"n {target_id} -1\n")
            #for edge in self.ts_edges:
            for edge in self.tsedges:
                if (edge is not None):   
                    if(edge.weight == self.H*self.H):
                        #pdb.set_trace()
                        file.write(f"c Exceed {edge.weight} {edge.weight // self.M}\na {edge.start_node.id} {edge.end_node.id} {edge.lower} {edge.upper} {edge.weight}\n")
                    else:
                        file.write(f"a {edge.start_node.id} {edge.end_node.id} {edge.lower} {edge.upper} {edge.weight}\n")
        if(self.print_out):
            print("Đã cập nhật các cung mới vào file TSG.txt.")
        
    def get_started_points(self):
        N = int(input("Nhập vào số lượng các xe AGV: "))
        self.started_nodes = []
        for i in range(1, N+1):
            p, t = map(int, input(f"Xe {i} xuất phát ở đâu và khi nào (nhập p t)?: ").split())
            p = t*self.M + p
            self.started_nodes.append(p)

    def get_max_id(self):
      max_val = 0
      try:
        with open('TSG.txt', 'r') as file:
            for line in file:
                parts = line.strip().split()
                if parts[0] == 'a':
                    max_val = max(max_val, int(parts[2]))
      except FileNotFoundError:
        pass
      return max_val
      
    def generate_numbers_student(self, G, H, M, N, df=10):
        while True:
            self._seed = self._seed + 1
            self._seed = self._seed % G
            np.random.seed(self._seed)
            # Sinh 4 số ngẫu nhiên theo phân phối Student
            first_two = np.random.standard_t(df, size=2)
            numbers = np.random.standard_t(df, size=2)
            # Chuyển đổi các số này thành số nguyên trong khoảng từ 1 đến 100
            first_two = np.round((first_two - np.min(first_two)) / (np.max(first_two) - np.min(first_two)) * (G//3) + self._seed).astype(int)
            numbers = np.round((numbers - np.min(numbers)) / (np.max(numbers) - np.min(numbers)) * (H//3) + self._seed).astype(int)
            if first_two[0] < G and first_two[1] < G and numbers[0] < numbers[1] and numbers[1] < H:
                # Kiểm tra điều kiện khoảng cách tối thiểu
                if (abs(first_two[0] - first_two[1]) >= M and abs(numbers[0] - numbers[1]) >= N):
                    return np.concatenate((first_two, numbers))
    
    def add_time_windows_constraints(self):
        #pdb.set_trace()
        from model.TimeWindowController import TimeWindowController
        # Tìm giá trị lớn nhất trong TSG.txt
        max_val = self.get_max_id()
        #print(f"max_val = {max_val}")
        max_val += 1
        target_node = TimeWindowNode(max_val, "TimeWindow")
        self.ts_nodes.append(target_node)
        #self.target_nodes.append(targetNode)
        self.append_target(target_node)
        if(self.time_window_controller == None):
            self.time_window_controller = TimeWindowController(self.alpha, self.beta, self.gamma, self.d, self.H)
        ID = -1
        earliness = 0
        tardiness = 0
        if(isinstance(self.ID, list)):
            self.time_window_controller.add_source_and_TWNode(self.ID[0], target_node, self.earliness[0], self.tardiness[0])
            ID = self.ID[0]
            earliness = self.earliness[0]
            tardiness = self.tardiness[0]
            self.ID = self.ID[1:]
            self.earliness = self.earliness[1:]
            self.tardiness = self.tardiness[1:]
        else:
            ID = self.ID
            self.time_window_controller.add_source_and_TWNode(self.ID, target_node, self.earliness, self.tardiness)
        R = set()
        new_edges = set()
        # Duyệt các dòng của file TSG.txt
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts[0] == 'a' and len(parts) >= 6:
                        ID2 =int(parts[2])
                        for i in range(1, self.H + 1):
                            j = i * self.M + ID
                            if j == ID2:
                                C = int(int(self.beta) * max(earliness - i, 0, i - tardiness) / int(self.alpha))
                                new_edges.add((j, max_val, 0, 1, C))
                                self.find_node(j).create_edge(target_node, self.M, self.d, [j, max_val, 0, 1, C])
                                break
                        t = ID2 // self.M - (1 if ID2 % self.M == 0 else 0)
                        if(t > self.H):
                            #pdb.set_trace()
                            C = self.H*self.H
                            new_edges.add((j, max_val, 0, 1, C))
                            self.find_node(j).create_edge(target_node, self.M, self.d, [j, max_val, 0, 1, C])
                            
        
        except FileNotFoundError:
            pass
        
        #pdb.set_trace()
        count = 0
        #self.ts_edges.update(e for e in new_edges if e not in self.ts_edges)
        self.ts_edges.extend(e for e in new_edges if e not in self.ts_edges)
        self.create_set_of_edges(new_edges)
        # Ghi các cung mới vào file TSG.txt
        with open('TSG.txt', 'a') as file:
          for edge in new_edges:
              count += 1
              file.write(f"a {edge[0]} {edge[1]} {edge[2]} {edge[3]} {edge[4]}\n")
        if(self.print_out):
            print(f"Đã cập nhật {count} cung mới vào file TSG.txt.")

    def update_tsg_with_t(self):
        T = int(input("Nhập giá trị T: "))
        # Đảm bảo T là một giá trị nguyên dương
        if not isinstance(T, int) or T <= 0:
            print("Giá trị của T phải là một số nguyên dương.")
            return

        new_lines = []

        # Đọc và kiểm tra từng dòng trong file TSG.txt cũ
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) == 6 and parts[0] == 'a':
                        ID1, ID2 = int(parts[1]), int(parts[2])

                        # Kiểm tra điều kiện ID1 và ID2
                        if ID1 >= T * self.M and ID2 >= T * self.M:
                            new_lines.append(line)
        except FileNotFoundError:
            print("Không tìm thấy file TSG.txt.")
            return

        # Ghi các dòng thỏa điều kiện vào file TSG.txt mới
        with open('TSG_new.txt', 'w') as file:
            for line in new_lines:
                file.write(line)
        print("Đã tạo file TSG_new.txt mới với các dòng thỏa điều kiện.")

    def add_problem_info(self):
      json_filepath = input("Nhap ten file dau vao: ")
      try:

          with open(json_filepath, 'r') as json_file:
              data = json.load(json_file)
              agv_number = data["AGV"]["number"]
              itinerary_start = data["itinerary"]["start"]
              itinerary_end = data["itinerary"]["end"]

              # Tính toán max_id và số lượng cung (A) từ file TSG.txt
              max_id = 0
              A = 0
              with open('TSG.txt', 'r') as tsg_file:
                  for line in tsg_file:
                      if line.startswith('a'):
                          A += 1
                          _, id1, id2, _, _, _ = line.split()
                          max_id = max(max_id, int(id1), int(id2))

              # Tạo dòng thông tin về bài toán cần giải
              problem_info_line = f"p min {max_id} {A}\n"

              # Tạo dòng thông tin về lịch trình
              itinerary_lines = []
              for item in itinerary_start:
                  time_values = item["time"]
                  for time_value in time_values:
                      point_id = item["point"] + self.M * time_value
                      itinerary_lines.append(f"n {point_id} 1\n")
              for item in itinerary_end:
                  point_id = item["point"][0]
                  time_values = item["time"]
                  itinerary_lines.append(f"n {point_id} -1\n")
                  self.ID = point_id
                  self.earliness = time_values[0]
                  self.tardiness = time_values[1]
                  self.alpha = 1
                  self.beta =  1
                  self.add_time_windows_constraints()


              # Ghi dòng thông tin về bài toán và lịch trình vào đầu file TSG.txt
              with open('TSG.txt', 'r+') as tsg_file:
                  content = tsg_file.read()
                  tsg_file.seek(0, 0)
                  tsg_file.write(problem_info_line + ''.join(itinerary_lines) + content)

              print("Đã thêm thông tin về bài toán vào file TSG.txt.")
      except FileNotFoundError:
          print("Không tìm thấy file JSON hoặc TSG.txt.")

    def remove_duplicate_lines(self):
            try:
                # Read lines from TSG.txt
                with open('TSG.txt', 'r') as file:
                    lines = file.readlines()

                seen_lines = set()
                unique_lines = []
                for line in lines:
                    if re.match(r'^a\s+\d+\s+\d+', line):
                        if line.strip() not in seen_lines:
                            unique_lines.append(line)
                            seen_lines.add(line.strip())
                    else:
                        unique_lines.append(line)

                # Write unique lines back to TSG.txt
                with open('TSG.txt', 'w') as file:
                    file.writelines(unique_lines)

                print("Removed duplicate lines from TSG.txt.")
            except FileNotFoundError:
                print("File TSG.txt not found.")

    def remove_redundant_edges(self):
            # Tập R: ID của nút nguồn
            R = set()
            # Tập E: ID của nút đích
            E = set()

            try:
                # Đọc dòng p min Max A
                with open('TSG.txt', 'r') as file:
                    lines = file.readlines()
                    if lines:
                        first_line = lines[0].strip()
                        if first_line.startswith('p min'):
                            # Tìm tất cả các dòng bắt đầu bằng 'n' và lưu vào tập S
                            S = set()
                            for line in lines[1:]:
                                if line.startswith('n'):
                                    _, node_id, _ = line.split()
                                    S.add(int(node_id))

                            # Lưu ID của nút nguồn vào tập R
                            for line in lines[1:]:
                                if line.startswith('a'):
                                    _, source_id, _, _, _, _ = line.split()
                                    source_id = int(source_id)
                                    if source_id not in S:
                                        R.add(source_id)

                            # Lưu ID của nút đích vào tập E
                            for line in lines[1:]:
                                if line.startswith('a'):
                                    _, _, target_id, _, _, _ = line.split()
                                    E.add(int(target_id))

                        else:
                            print("File không đúng định dạng.")
                            return
                    else:
                        print("File rỗng.")
                        return
            except FileNotFoundError:
                print("File không tồn tại.")
                return

            try:
                # Đọc từng dòng của file và loại bỏ các cạnh dư thừa
                with open('TSG.txt', 'r') as file:
                    lines = file.readlines()

                    # Dòng mới sau khi loại bỏ các cạnh dư thừa
                    new_lines = []

                    for line in lines:
                        if line.startswith('a'):
                            _, source_id, target_id, _, _, _ = line.split()
                            source_id = int(source_id)
                            target_id = int(target_id)

                            # Nếu source_id không thuộc S và không thuộc E, loại bỏ cạnh
                            if source_id not in S and source_id not in E:
                                continue

                        # Thêm dòng vào danh sách mới
                        new_lines.append(line)

                # Ghi các dòng mới vào file TSG.txt
                with open('TSG.txt', 'w') as file:
                    file.writelines(new_lines)

                print("Đã loại bỏ các cạnh dư thừa từ file TSG.txt.")
            except FileNotFoundError:
                print("File không tồn tại.")

    def remove_descendant_edges(self):
        source_id = int(input("Nhập ID của điểm gốc: "))
        try:
          with open('TSG.txt', 'r') as file:
              lines = file.readlines()
        except FileNotFoundError:
          print("File TSG.txt không tồn tại.")
          return

        # Tạo một hàng đợi để duyệt qua các cung
        queue = deque([source_id])

        # Dùng set để lưu trữ ID của các cung cần loại bỏ
        to_remove = set()

        while queue:
          current_id = queue.popleft()
          for line in lines:
              parts = line.strip().split()
              if len(parts) == 6 and parts[0] == 'a' and int(parts[1]) == current_id:
                  destination_id = int(parts[2])
                  to_remove.add(line.strip())
                  queue.append(destination_id)

        new_lines = [line for line in lines if line.strip() not in to_remove]
        # Ghi lại các cung còn lại vào file TSG.txt
        with open('TSG.txt', 'w') as file:
          file.writelines(new_lines)

        print("Đã gỡ bỏ các cung con cháu xuất phát từ điểm gốc trong đồ thị TSG.")
    
    def process_tsg(self):
        AGV = set()
        TASKS = set()
        objective_coeffs = {}
        solver = pywraplp.Solver.CreateSolver('SCIP')
        try:
          with open('TSG.txt', 'r') as file:
              for line in file:
                  parts = line.strip().split()
                  if len(parts) == 3 and parts[0] == 'n':
                      node_id, val = int(parts[1]), int(parts[2])
                      if val == 1:
                          AGV.add(node_id)
                      elif val == -1:
                          TASKS.add(node_id)
                  elif len(parts) == 6 and parts[0] == 'a':
                      i, j, c = int(parts[1]), int(parts[2]), int(parts[5])
                      if (i, j) not in objective_coeffs:
                          objective_coeffs[(i, j)] = c

        except FileNotFoundError:
            print("File TSG.txt không tồn tại.")

        objective = solver.Objective()

        # Thêm các biến quyết định vào mục tiêu
        added_keys = set()  # Sử dụng set để lưu trữ các khóa đã được thêm
        for m in AGV:
            for i, j in objective_coeffs.keys():
                key = f'x_{m}_{i}_{j}'
                if key not in added_keys:  # Chỉ tạo biến nếu chưa được tạo trước đó
                    x = solver.BoolVar(key)
                    objective.SetCoefficient(x, objective_coeffs[(i, j)])  # Đặt hệ số cho mỗi biến
                    added_keys.add(key)  # Thêm khóa vào set đã được thêm

        objective.SetMinimization()
        print(added_keys)
        # Thêm ràng buộc x_m_i_j nhận giá trị 0 hoặc 1
        for m in AGV:
            for i, j in objective_coeffs.keys():
                x = solver.LookupVariable(f'x_{m}_{i}_{j}')
                constraint = solver.Constraint(0, 1)
                constraint.SetCoefficient(x, 1)

        status = solver.Solve()
        if status == pywraplp.Solver.OPTIMAL:
            print('Solution:')
            print('Objective value =', solver.Objective().Value())
            for m in AGV:
                for i, j in objective_coeffs.keys():
                    x = solver.LookupVariable(f'x_{m}_{i}_{j}')
                    if x.solution_value() == 1:
                        print(f'x_{m}_{i}_{j} = 1')
        else:
            print('The problem does not have an optimal solution.')
            
    def generate_poisson_random(self, M = None):
        if M is None:
            M = self.M
        if M <= 2 and M >= 1:
            return M
        while True:
            # Sinh số ngẫu nhiên theo phân phối Poisson
            number = np.random.poisson(lam=M)        
            # Kiểm tra điều kiện số ngẫu nhiên lớn hơn 1 và nhỏ hơn hoặc bằng M
            if 1 < number < M:
                return number



    def use_in_main(self, use_config_data = False, print_output = False):
        self.print_out = print_output
        if(use_config_data):
            filepath = config.filepath
        else:
            filepath = input("Nhap ten file can thuc hien (hint: Redundant3x3Wards.txt): ")
            if filepath == '':
                filepath = 'Redundant3x3Wards.txt'
            config.filepath = filepath
        self.started_nodes = [] #[1, 10]

        self.process_input_file(filepath)
        if(use_config_data):
            self.H = config.H
        else:
            self.H = input("Nhap thoi gian can gia lap (default: 10): ")
            if(self.H == ''):
                self.H = 10
            else:
                self.H = int(self.H)
            config.H = self.H

        self.generate_hm_matrix()
        if(use_config_data):
            self.d = config.d
        else:
            self.d = input("Nhap time unit (default: 1): ")
            if(self.d == ''):
                self.d = 1
            else:
                self.d = int(self.d)
            config.d = self.d
        
        self.generate_adj_matrix()
        
        num_of_agvs = 0
        if(use_config_data):
            self.num_max_agvs = config.num_max_agvs
            self.ID = config.ID
            self.earliness = config.earliness
            self.tardiness = config.tardiness
            self.started_nodes = config.started_nodes
            num_of_agvs = config.numOfAGVs
        else:
            self.num_max_agvs = input("Nhap so luong AGV toi da di chuyen trong toan moi truong (default: 4):")
            if(self.num_max_agvs == ''):
                self.num_max_agvs = 2
            else:
                self.num_max_agvs = int(self.num_max_agvs)
            num_of_agvs = self.num_max_agvs
            config.num_max_agvs = self.num_max_agvs
            config.numOfAGVs = num_of_agvs
            if len(self.started_nodes) == 0:
                self.ID = []
                self.earliness = []
                self.tardiness = []
                #pdb.set_trace()
                for i in range(num_of_agvs):
                    [s, d, e, t] = self.generate_numbers_student(self.M, self.H, 12, 100)
                    self.started_nodes.append(s)
                    self.ID.append(d)
                    self.earliness.append(e)
                    self.tardiness.append(t)
                print(f'Start: {self.started_nodes} \n End: {self.ID} \n Earliness: {self.earliness} \n Tardiness: {self.tardiness}')
                config.started_nodes = self.started_nodes.copy()
                config.ID = self.ID.copy()
                config.earliness = self.earliness.copy()
                config.tardiness = self.tardiness.copy()
            """self.num_max_agvs = 8
            numOfAGVs = 8
            self.started_nodes = [23, 4, 29, 30, 31, 32, 33, 35] 
            self.ID = [2, 25, 8, 9, 10, 11, 12, 14] 
            self.earliness = [2, 4, 8, 9, 10, 11, 12, 14] 
            self.tardiness = [302, 304, 308, 309, 310, 311, 312, 314]
            print(f'Start: {self.started_nodes} \n End: {self.ID} \n Earliness: {self.earliness} \n Tardiness: {self.tardiness}')"""
        
        self.create_tsg_file()
        count = 0
        
        while(count <= num_of_agvs - 1):
            #pdb.set_trace()
            if(isinstance(self.ID, int)):
                self.ID = 3
                self.earliness = 4 if count == 0 else 7
                self.tardiness = 6 if count == 0 else 9
                self.alpha = 1
                self.beta = 1
            else:
                pass
            self.add_time_windows_constraints()
            assert len(self.ts_edges) == len(self.tsedges), f"Thiếu cạnh ở đâu đó rồi {len(self.ts_edges)} != {len(self.tsedges)}"
            count += 1
        #self.add_restrictions()
        self.gamma = 1
        self.restriction_count = 1
        self.start_ban = 0
        self.end_ban = 2*self.d
        self.restrictions = []
        self.ur = 3
        #pdb.set_trace()
        self.process_restrictions()
        #pdb.set_trace()

    def test_menu(self):
        while True:
            print("======================================")
            print("Nhan (a) de chon file dau vao")
            print("Nhan (b) de in ra ma tran HM")
            print("Nhan (c) de in ra ma tran lien ke Adj")
            print("Nhan (d) de tao ra file TSG.txt")
            print("Nhan (h) de yeu cau nhap ID, earliness, tardiness")
            print("Nhan (j) de cap nhat cac rang buoc ve su xuat hien cua xe")
            print("Nhan cac phim ngoai (a-o) de ket thuc")

            self.use_in_main()
                
    def main_menu(self):
        while True:
            print("======================================")
            print("Nhan (a) de chon file dau vao")
            print("Nhan (b) de in ra ma tran HM")
            print("Nhan (c) de in ra ma tran lien ke Adj")
            print("Nhan (d) de tao ra file TSG.txt")
            print("Nhan (e) de nhap vao ID nguon")
            print("Nhan (f) de kiem tra file")
            print("Nhan (g) de cap nhat file TSG.txt")
            print("Nhan (h) de yeu cau nhap ID, earliness, tardiness")
            print("Nhan (i) de loc ra cac cung cho do thi")
            print("Nhan (j) de cap nhat cac rang buoc ve su xuat hien cua xe")
            print("Nhan (k) de cap nhat cac dong dau cua TSG")
            print("Nhan (l) de loai bo cac dong du thua")
            print("Nhan (m) de loai bo cac dong bi trung lap")
            print("Nhan (o) de giai tim loi giai minimum cho completion time")

            print("Nhan cac phim ngoai (a-o) de ket thuc")

            choice = input("Nhap lua chon cua ban: ").strip().lower()

            if choice == 'a':
                self.getStartedPoints()
                filepath = input("Nhap ten file dau vao: ")
                self.process_input_file(filepath)
            elif choice == 'b':
                self.H = int(input("Nhap vao gia tri H: "))
                self.generate_hm_matrix()
            elif choice == 'c':
                self.d = int(input("Nhap vao gia tri d: "))
                self.generate_adj_matrix()
            elif choice == 'd':
                self.create_tsg_file()
            elif choice == 'e':
                self.query_edges_by_source_id()
            elif choice == 'f':
                self.check_file_conditions()
            elif choice == 'g':
                self.update_file()
            elif choice == 'h':
                self.ID = int(input("Nhập ID của điểm trong không gian: "))
                self.earliness = int(input("Nhập giá trị earliness: "))
                self.tardiness = int(input("Nhập giá trị tardiness: "))
                alpha = input("Nhập alpha (nhấn Enter để lấy giá trị mặc định là 1): ")
                beta = input("Nhập beta (nhấn Enter để lấy giá trị mặc định là 1): ")
                self.alpha = int(alpha) if alpha else 1
                self.beta = int(beta) if beta else 1
                self.add_time_windows_constraints()
            elif choice == 'i':
                self.update_tsg_with_t()
            elif choice == 'j':
                self.add_restrictions()
                self.process_restrictions()
            elif choice == 'k':
                self.add_problem_info()
            elif choice == 'm':
                self.remove_duplicate_lines()
            elif choice == 'l':
                self.remove_redundant_edges()
            elif choice == 'n':
                self.remove_descendant_edges()
            elif choice == 'o':
                self.process_tsg()
            else:
                print("Ket thuc chuong trinh.")
                break

if __name__ == "__main__":
    gp = GraphProcessor()
    #gp.main_menu()
    gp.use_in_main()

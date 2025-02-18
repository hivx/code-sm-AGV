from model.Graph import Graph, bcolors#, graph
from model.AGV import AGV
from model.Event import Event, debug
from controller.EventGenerator import StartEvent
from model.Logger import Logger
import config
from discrevpy import simulator
from controller.GraphProcessor import GraphProcessor
import subprocess
import sys
import pdb
import time

from model.hallway_simulator_module.HallwaySimulator import DirectoryManager
dm = DirectoryManager()
dm.full_cleanup()

def choose_solver():
    print("Choose the method for solving:")
    print("1 - Use LINK II solver")
    print("2 - Use parallel network-simplex")
    print("3 - Use NetworkX")
    choice = 3
    if(config.count == 2):
        choice = 1
        config.solver_choice = 'solver'
    else:
        choice = input("Enter your choice (1 or 2 or 3): ")
        if choice == '1':
            config.solver_choice = 'solver'
        elif choice == '2':
            config.solver_choice = 'network-simplex'
        elif choice == '3':
            config.solver_choice = 'networkx'
        else:
            print("Invalid choice. Defaulting to Network X.")
            config.solver_choice = 'networkx'

def choose_time_measurement():
    # choose to run sfm or not
    if(config.count == 1):
        print("Choose to run sfm or not:")
        print("1 - Run sfm")
        print("0 - Not run sfm")
        choice = input("Enter your choice (1 or 0): ")
        if choice == '1':
            config.sfm = True
        elif choice == '0':
            config.sfm = False
        else:
            print("Invalid choice. Defaulting to run sfm.")
            config.sfm = True

allAGVs = set()
TASKS = set()

x = {}
y = {}

config.count = 0
logger = Logger()
while(config.count < 2):
    #pdb.set_trace()
    config.count = config.count + 1
    if config.count > 1:
        print(f"{bcolors.WARNING}Start half cleanup{bcolors.ENDC}")
        dm.half_cleanup()
    choose_solver()
    choose_time_measurement()
    graph_processor = GraphProcessor()
    start_time = time.time()
    graph_processor.use_in_main(config.count != 1)
    end_time = time.time()
    graph_processor.print_out = False
    # Tính thời gian thực thi
    execution_time = end_time - start_time
    if(execution_time >= 5 and graph_processor.print_out):
        print(f"Thời gian thực thi: {execution_time} giây")
    
    graph = Graph(graph_processor)  # Assuming a Graph class has appropriate methods to handle updates
    
    events = []
    Event.setValue("number_of_nodes_in_space_graph", graph_processor.M) #sẽ phải đọc file Edges.txt để biết giá trị cụ thể
    Event.setValue("debug", 0)
    # Kiểm tra xem có tham số nào được truyền qua dòng lệnh không
    if len(sys.argv) > 1:
        Event.setValue("debug", 1 if sys.argv[1] == '-g' else 0)
    
    number_of_nodes_in_space_graph = Event.getValue("number_of_nodes_in_space_graph")
    # Mở file để đọc
    #pdb.set_trace()
    graph_processor.init_agvs_n_events(allAGVs, events, graph, graph_processor)
    graph_processor.init_tasks(TASKS)
    graph_processor.init_nodes_n_edges() 
    events = sorted(events, key=lambda x: x.start_time)
    Event.setValue("allAGVs", allAGVs)
    
    
    def schedule_events(events):
        for event in events:
            #pdb.set_trace()
            simulator.schedule(event.start_time, event.process)
    
    def reset(simulator):
        config.totalCost = 0
        config.reachingTargetAGVs = 0
        config.haltingAGVs = 0
        config.totalSolving = 0
        config.timeSolving = 0
        AGV.reset()
        simulator.reset()
    
    if __name__ == "__main__":
        import time
        start_time = time.time()
        simulator.ready()
        schedule_events(events)
        simulator.run()
        end_time = time.time()
        # Tính toán thời gian chạy
        elapsed_time = end_time - start_time
        # Chuyển đổi thời gian chạy sang định dạng hh-mm-ss
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        config.timeSolving = config.timeSolving / config.totalSolving
        #runTime = f'{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)
        print("Thời gian chạy: {:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)))
        logger.log("Log.csv", config.filepath, config.numOfAGVs, config.H, \
            config.d, config.solver_choice, config.reachingTargetAGVs, config.haltingAGVs, \
                config.totalCost, elapsed_time, config.timeSolving)
        reset(simulator)

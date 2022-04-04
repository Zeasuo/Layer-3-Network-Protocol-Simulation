import socket
import threading
import time
import select
import netifaces as ni
import json


"""
    In this class, forwarding table referrs to the table that routers send to the monitor node 
    routing table refers to the table that the monitor node sends to the router
"""

router_count = 1 # number of routers
router_to_forwarding_table = {} # e.g {"r1": {10.104.0.1: 10.104.0.2}}
source_address_to_router = {} # e.g. {"11.1.11.1": "r1"}

# format: {node: [neighbors]}, e.g. {'r1': ['r2', 'r3'], 'r2': ['r1'], 'r3': ['r1']}
routing_table = {}
# format: {node: {target: neighbour}}, e.g. {'r2': {'r1': 'r1', 'r3': 'r1'}}
computed_routing_table = {}
# format: {receiving_ip: {destination_ip: {source_interface_ip: next_interface_ip}}}, more details in process_routing_table
routing_table_to_send = {}
# connection is a dictionary represents the connection between routers, in both directions
# format: {source_router: {destination_router: (source_ip, destination_ip)}} e.g. {'r1': {'r2': ('10.104.0.1', '10.104.0.2')}}
connection = {}

input_sockets = []
output_sockets = []
router_connections = []

"""
    This function listens for incoming forwarding table from other routers
    and sends routing table to other routers
"""
def send_and_receive_table():
    global input_sockets
    global output_sockets
    global router_connections
    tIntfs = ni.interfaces()
    broadcasts = []
    receive_from = []
    socket_b_ip = {}
    all_routers = {}
    bip_to_inet = {}
    broadcasts_s_to_inet_s ={}
    for intf in tIntfs:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
            broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast.bind((ip, 8001))
            broadcasts.append(broadcast)
            socket_b_ip[broadcast] = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']

            ip_b = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                    socket.IPPROTO_UDP)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                               str(intf).encode('utf-8'))
            receive.bind((ip_b, 8002))
            receive_from.append(receive)

            bip_to_inet[ip_b] = ip

            broadcasts_s_to_inet_s[receive] = broadcast

    while True:
        readable, writable, exceptional = select.select(receive_from, broadcasts, [])
        if readable:
            for s in readable:
                print(s)
                sourcedata, sourceAddress = s.recvfrom(1024)
                print(sourcedata)
                if sourceAddress[0] != bip_to_inet[s.getsockname()[0]]:
                    all_routers[sourceAddress[:-1] + "2"] = broadcasts_s_to_inet_s[s]
                    receivedData = json.loads(sourcedata.decode())
                    print("Received: from "+sourceAddress[0])
                    print(receivedData)
                    # pass the received data into the function
                    set_routing_table(receivedData, sourceAddress[0])

            for router_address in all_routers:
                print(all_routers)
                if router_address in routing_table_to_send:
                    print(router_address)
                    all_routers[router_address].sendto(str.encode(json.dumps(routing_table_to_send[router_address])), (router_address[:-1] + "1", 8005))


"""
    This function calls related functions to process the forwarding table,
    calculates the routing table, prepares the routing table in a format that 
    can be sent to other routers.
"""
def set_routing_table(forwarding_table, source_address):
    current_router = process_forwarding_table(forwarding_table, source_address)
    dijkstra(routing_table)
    process_routing_table(current_router)
    print_routing_table()


"""
    forwarding_table follows the format: {sourceIP: destIP}
    process forwarding_table and updates routing table
    return the node that represents the source address
"""
def process_forwarding_table(forwarding_table, source_address):
    global router_count
    global router_to_forwarding_table
    global source_address_to_router
    global routing_table
    global connection
    # if it's the first time we've seen this source address
    if source_address not in source_address_to_router:
        router = "r" + str(router_count)
        router_count += 1
        router_to_forwarding_table[router] = forwarding_table
        source_address_to_router[source_address] = router
        # add router to routing table
        routing_table[router] = []
    # if we've seen this source address before
    else:
        # if the forwarding table is different from the previous one
        if router_to_forwarding_table[source_address_to_router[source_address]] != forwarding_table:
            # update the forwarding table, and destination IP to source IP mapping
            router_to_forwarding_table[source_address_to_router[source_address]] = forwarding_table

    currect_router = source_address_to_router[source_address]
    print("Processing current router: " + currect_router)
    # update routing table
    for source_ip, dest_ip in forwarding_table.items():
        for router in router_to_forwarding_table.keys():
            # if source_ip, dest_ip matches dest_ip, source_ip in forwarding table of another router
            # and store this connection in connection dictionary
             if router != currect_router \
                and dest_ip in router_to_forwarding_table[router] \
                and router_to_forwarding_table[router][dest_ip] == source_ip \
                and router not in routing_table[currect_router] and currect_router not in routing_table[router]:
                routing_table[currect_router].append(router)
                routing_table[router].append(currect_router)
                # add connection to connection dictionary
                if currect_router not in connection:
                    connection[currect_router] = {}
                connection[currect_router][router] = (source_ip, dest_ip)
                if router not in connection:
                    connection[router] = {}
                connection[router][currect_router] = (dest_ip, source_ip)
                break
    return currect_router


"""
    implement directed, unweighted dijkstra's algorithm to find shortest path to 
    all nodes in the network given routing_table, and a target_node. default distance to neighbors is 1.
    updates calculated_routing_table of the following format:
    {node: {target: neighbor}} where node is the current node, target is the node want to reach. 
    and neighbor is the node that is the next hop in order to reach target_node
"""
def dijkstra(routing_table):
    for target_node in routing_table:
        # initialize distance to all nodes to infinity
        distance = {}
        for node in routing_table:
            distance[node] = float("inf")
        # initialize previous node to None
        previous = {}
        for node in routing_table:
            previous[node] = None
        # initialize visited nodes to empty set
        visited = set()
        # initialize queue to hold nodes in order of distance
        queue = []
        # initialize distance to start node to 0
        distance[target_node] = 0
        # initialize queue to hold nodes in order of distance
        queue.append(target_node)
        # while queue is not empty
        while queue:
            # pop node with smallest distance
            current = queue.pop(0)
            # if node has not been visited
            if current not in visited:
                # mark node as visited
                visited.add(current)
                # for each neighbor of current node
                for neighbor in routing_table[current]:
                    # if neighbor is not visited
                    if neighbor not in visited:
                        # if distance to neighbor is greater than distance to current node + 1
                        if distance[neighbor] > distance[current] + 1:
                            # update distance to neighbor
                            distance[neighbor] = distance[current] + 1
                            # update previous node to current node
                            previous[neighbor] = current
                            # add neighbor to queue
                            queue.append(neighbor)
        # return dictionary of previous node to reach each node
        previous.pop(target_node)
        for node in previous:
            if previous[node] == target_node:
                previous[node] = node
        # update computed_routing_table
        computed_routing_table[target_node] = previous
    return


"""
    prepare the routing table to be sent to routers 
    the package format is:
    {receiving_ip: {destination_ip: {source_interface_ip: next_interface_ip}}}
    where receiving_ip is the IP address of the receiving router
    destination_ip is the IP address of the destination router
    source_interface_ip is the IP address of the source interface of the receiving router
    next_interface_ip is the IP address of the router that will forward the packet to the destination router
"""
def process_routing_table(currect_router):
    global routing_table_to_send
    # get receiving router IP, which is source ip but with last digit changed to 2 (e.g. 11.1.11.1 -> 11.1.11.2)
    for currect_router in routing_table.keys():
        current_routing_table = computed_routing_table[currect_router]
        for source_address, router in source_address_to_router.items():
            if router == currect_router:
                receiving_ip = source_address[:-1] + "2"
                routing_table_to_send[receiving_ip] = {}
                for target_node in current_routing_table:
                    # get destination router IP
                    temp_router = currect_router
                    temp_table = computed_routing_table[temp_router]
                    while temp_table[target_node] != target_node:
                        temp_router = temp_table[target_node]
                        temp_table = computed_routing_table[temp_router]
                    destination_ip = connection[temp_router][target_node][1]

                    next_node = current_routing_table[target_node]
                    # get source interface IP
                    source_interface_ip = connection[currect_router][next_node][0]
                    # get next interface IP
                    next_interface_ip = connection[currect_router][next_node][1]
                    routing_table_to_send[receiving_ip][destination_ip] = {source_interface_ip: next_interface_ip}


"""
    A function that prints the routing table, and calculated_routing_table to the console
"""
def print_routing_table():
    print("Routing table: " + str(routing_table))
    print("Calculated routing table: " + str(computed_routing_table))
    print("Routing table to send: " + str(routing_table_to_send))

if __name__ == "__main__":
    # set_routing_table({'10.104.0.1': "10.104.0.2", '10.105.0.1': "10.105.0.2"},"11.1.11.1")
    # set_routing_table({'10.104.0.2': "10.104.0.1"},"11.2.11.1")
    # set_routing_table({'10.105.0.2': "10.105.0.1"},"11.3.11.1")

    send_and_receive_table()

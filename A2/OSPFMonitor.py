from concurrent.futures import process
import socket
from sqlite3 import connect
import threading
import time

import netifaces as ni
import select
import json

router_count = 1 
raw_forwarding_table = {"10.104.0.1": "10.104.0.2", "10.105.0.1": "10.105.0.2"}
destIP_to_sourceIP = {} # e.g. {10.104.0.1: 10.104.0.2}
router_to_forwarding_table = {} # e.g {"r1": {10.104.0.1: 10.104.0.2}}
source_address_to_router = {} # e.g. {"11.1.11.1": "r1"}

# format: {node: [neighbors]} 
routing_table = {"r1": ["r2", "r3", "r4", "r5"], "r2": ["r1", "r4", "r5"], "r3": ["r1", "r4"], "r4": ["r3","r2", "r1"], "r5": ["r1", "r2"]}

"""
    forwarding_table follows the format: {souceIP: destIP}
    process raw_forwarding_table and return a dictionary of {node: [neighbour ip]}
"""
def process_forwarding_table(forwarding_table, source_address):
    connects_to = [] # the ip address of the node that this router connects to
    if source_address not in router_to_forwarding_table:
        router = "r" + str(router_count)
        router_count += 1
        router_to_forwarding_table[router] = forwarding_table
    for key, value in forwarding_table.items():
        destIP_to_sourceIP[value] = key
        connects_to.append(value)
    


"""
implement directed, unweighted dijkstra's algorithm to find shortest path to 
all nodes in the network given routing_table, and a target_node. default distance to neighbors is 1.
return a dictionary of the following format:
{start_node: neighbor_node} where neighbor_node is in routing_table[start_node]
and is the node that is the next hop to reach target_node
Example output:
dijkstra({"r1": ["r2", "r3"], "r2": ["r1"], "r3": ["r1"]}, "r2")
{'r1': 'r1', 'r3': 'r1'}
"""
def dijkstra(routing_table, target_node):
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
    return previous

if __name__ == "__main__":
    print(dijkstra(routing_table, "r4"))

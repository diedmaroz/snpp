#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Adaptation of Louvain community detection to signed network.

Main change: definition of modularity
"""

from __future__ import print_function
from collections import defaultdict
__all__ = ["partition_at_level", "modularity", "best_partition", "generate_dendrogram", "generate_dendogram", "induced_graph"]
__author__ = """Thomas Aynaud (thomas.aynaud@lip6.fr)"""
#    Copyright (C) 2009 by
#    Thomas Aynaud <thomas.aynaud@lip6.fr>
#    All rights reserved.
#    BSD license.

__PASS_MAX = -1
__MIN = 0.0000001

import networkx as nx
import sys
import types
import array


def partition_at_level(dendrogram, level) :
    """Return the partition of the nodes at the given level

    A dendrogram is a tree and each level is a partition of the graph nodes.
    Level 0 is the first partition, which contains the smallest communities, and the best is len(dendrogram) - 1.
    The higher the level is, the bigger are the communities

    Parameters
    ----------
    dendrogram : list of dict
       a list of partitions, ie dictionnaries where keys of the i+1 are the values of the i.
    level : int
       the level which belongs to [0..len(dendrogram)-1]

    Returns
    -------
    partition : dictionnary
       A dictionary where keys are the nodes and the values are the set it belongs to

    Raises
    ------
    KeyError
       If the dendrogram is not well formed or the level is too high

    See Also
    --------
    best_partition which directly combines partition_at_level and generate_dendrogram to obtain the partition of highest modularity

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> dendo = generate_dendrogram(G)
    >>> for level in range(len(dendo) - 1) :
    >>>     print "partition at level", level, "is", partition_at_level(dendo, level)
    """
    partition = dendrogram[0].copy()
    for index in range(1, level + 1) :
        for node, community in partition.items() :
            partition[node] = dendrogram[index][community]
    return partition


def modularity(partition, graph) :
    """    
    Compute the modularity of a partition of a graph
    
    Parameters
    ----------
    partition : dict
       the partition of the nodes, i.e a dictionary where keys are their nodes and values the communities
    graph : networkx.Graph
       the networkx graph which is decomposed

    Returns
    -------
    modularity : float
       The modularity

    Raises
    ------
    KeyError
       If the partition is not a partition of all graph nodes
    ValueError
        If the graph has no link
    TypeError
        If graph is not a networkx.Graph

    References
    ----------
    .. 1. Newman, M.E.J. & Girvan, M. Finding and evaluating community structure in networks. Physical Review E 69, 26113(2004).

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> part = best_partition(G)
    >>> modularity(part, G)
    """
    if type(graph) != nx.MultiGraph:
        raise TypeError("Bad graph type, use only non directed graph")

    graph_p, graph_n = split_graph_by_sign(graph)

    inc_p = defaultdict(float)
    deg_p = defaultdict(float)
    inc_n = defaultdict(float)
    deg_n = defaultdict(float)

    links_p = graph_p.size(weight='weight')
    links_n = graph_n.size(weight='weight')    

    if links_p == 0  or links_n == 0:
        raise ValueError("A graph without link has an undefined modularity")

    for node in graph:
        com = partition[node]
        deg_p[com] += graph_p.degree(node, weight = 'weight')
        deg_n[com] += graph_n.degree(node, weight = 'weight')
        for neighbor, keyed_datas in graph[node].items():
            print('edge', node, neighbor)
            if partition[neighbor] == com:  # same partition
                for key, datas in keyed_datas.items():
                    weight = datas.get("weight", 1)
                    if neighbor == node:
                        if datas['sign'] == 1:
                            inc_p[com] += weight
                        else:
                            inc_n[com] += weight
                    else:
                        if datas['sign'] == 1:
                            inc_p[com] += weight / 2
                        else:
                            inc_n[com] += weight / 2
    res = 0.
    for com in set(partition.values()):
        res += ((inc_p[com] / (2*links_p)) - (deg_p[com] / (2.*links_p))**2)
        res -= ((inc_n[com] / (2*links_n)) - (deg_n[com] / (2.*links_n))**2)
    return res


def best_partition(graph, partition = None) :
    """Compute the partition of the graph nodes which maximises the modularity
    (or try..) using the Louvain heuristices

    This is the partition of highest modularity, i.e. the highest partition of the dendrogram
    generated by the Louvain algorithm.

    Parameters
    ----------
    graph : networkx.Graph
       the networkx graph which is decomposed
    partition : dict, optionnal
       the algorithm will start using this partition of the nodes. It's a dictionary where keys are their nodes and values the communities

    Returns
    -------
    partition : dictionnary
       The partition, with communities numbered from 0 to number of communities

    Raises
    ------
    NetworkXError
       If the graph is not Eulerian.

    See Also
    --------
    generate_dendrogram to obtain all the decompositions levels

    Notes
    -----
    Uses Louvain algorithm

    References
    ----------
    .. 1. Blondel, V.D. et al. Fast unfolding of communities in large networks. J. Stat. Mech 10008, 1-12(2008).

    Examples
    --------
    >>>  #Basic usage
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> part = best_partition(G)

    >>> #other example to display a graph with its community :
    >>> #better with karate_graph() as defined in networkx examples
    >>> #erdos renyi don't have true community structure
    >>> G = nx.erdos_renyi_graph(30, 0.05)
    >>> #first compute the best partition
    >>> partition = community.best_partition(G)
    >>>  #drawing
    >>> size = float(len(set(partition.values())))
    >>> pos = nx.spring_layout(G)
    >>> count = 0.
    >>> for com in set(partition.values()) :
    >>>     count = count + 1.
    >>>     list_nodes = [nodes for nodes in partition.keys()
    >>>                                 if partition[nodes] == com]
    >>>     nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20,
                                    node_color = str(count / size))
    >>> nx.draw_networkx_edges(G,pos, alpha=0.5)
    >>> plt.show()
    """
    dendo = generate_dendrogram(graph, partition)
    return partition_at_level(dendo, len(dendo) - 1 )
    
    
def generate_dendrogram(graph, part_init = None) :
    """Find communities in the graph and return the associated dendrogram

    A dendrogram is a tree and each level is a partition of the graph nodes.  Level 0 is the first partition, which contains the smallest communities, and the best is len(dendrogram) - 1. The higher the level is, the bigger are the communities


    Parameters
    ----------
    graph : networkx.Graph
        the networkx graph which will be decomposed
    part_init : dict, optionnal
        the algorithm will start using this partition of the nodes. It's a dictionary where keys are their nodes and values the communities

    Returns
    -------
    dendrogram : list of dictionaries
        a list of partitions, ie dictionnaries where keys of the i+1 are the values of the i. and where keys of the first are the nodes of graph

    Raises
    ------
    TypeError
        If the graph is not a networkx.Graph

    See Also
    --------
    best_partition

    Notes
    -----
    Uses Louvain algorithm

    References
    ----------
    .. 1. Blondel, V.D. et al. Fast unfolding of communities in large networks. J. Stat. Mech 10008, 1-12(2008).

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> dendo = generate_dendrogram(G)
    >>> for level in range(len(dendo) - 1) :
    >>>     print "partition at level", level, "is", partition_at_level(dendo, level)
    """
    if type(graph) != nx.MultiGraph :
        raise TypeError("Bad graph type, use only non directed graph")

    #special case, when there is no link
    #the best partition is everyone in its community
    if graph.number_of_edges() == 0 :
        part = dict([])
        for node in graph.nodes() :
            part[node] = node
        return part

    current_graph = graph.copy()
    status = Status()
    status.init(current_graph, part_init)
    mod = __modularity(status)
    status_list = list()
    __one_level(current_graph, status)
    new_mod = __modularity(status)
    partition = __renumber(status.node2com)
    status_list.append(partition)
    mod = new_mod
    current_graph = induced_graph(partition, current_graph)
    status.init(current_graph)

    while True :
        __one_level(current_graph, status)
        new_mod = __modularity(status)
        if new_mod - mod < __MIN :
            break
        partition = __renumber(status.node2com)
        status_list.append(partition)
        mod = new_mod
        current_graph = induced_graph(partition, current_graph)
        status.init(current_graph)
    return status_list[:]


def induced_graph(partition, graph) :
    """Produce the graph where nodes are the communities

    there is a link of weight w between communities if the sum of the weights of the links between their elements is w

    Parameters
    ----------
    partition : dict
       a dictionary where keys are graph nodes and  values the part the node belongs to
    graph : networkx.Graph
        the initial graph

    Returns
    -------
    g : networkx.Graph
       a networkx graph where nodes are the parts

    Examples
    --------
    >>> n = 5
    >>> g = nx.complete_graph(2*n)
    >>> part = dict([])
    >>> for node in g.nodes() :
    >>>     part[node] = node % 2
    >>> ind = induced_graph(part, g)
    >>> goal = nx.MultiGraph()
    >>> goal.add_weighted_edges_from([(0,1,n*n),(0,0,n*(n-1)/2), (1, 1, n*(n-1)/2)])
    >>> nx.is_isomorphic(int, goal)
    True
    """
    ret = nx.MultiGraph()
    ret.add_nodes_from(partition.values())

    for node1, node2, datas in graph.edges_iter(data = True) :
        weight = datas.get("weight", 1)
        sign = datas['sign']
        com1 = partition[node1]
        com2 = partition[node2]
        if not ret.has_edge(com1, com2, key=sign):
            ret.add_edge(com1, com2, key=sign, weight=weight, sign=sign)
        else:
            ret[com1][com2][sign]['weight'] += weight

    return ret


def __renumber(dictionary) :
    """Renumber the values of the dictionary from 0 to n
    """
    count = 0
    ret = dictionary.copy()
    new_values = dict([])

    for key in dictionary.keys():
        value = dictionary[key]
        new_value = new_values.get(value, -1)
        if new_value == -1 :
            new_values[value] = count
            new_value = count
            count = count + 1
        ret[key] = new_value

    return ret


def __load_binary(data) :
    """Load binary graph as used by the cpp implementation of this algorithm
    """
    data = open(data, "rb")

    reader = array.array("I")
    reader.fromfile(data, 1)
    num_nodes = reader.pop()
    reader = array.array("I")
    reader.fromfile(data, num_nodes)
    cum_deg = reader.tolist()
    num_links = reader.pop()
    reader = array.array("I")
    reader.fromfile(data, num_links)
    links = reader.tolist()
    graph = nx.MultiGraph()
    graph.add_nodes_from(range(num_nodes))
    prec_deg = 0

    for index in range(num_nodes) :
        last_deg = cum_deg[index]
        neighbors = links[prec_deg:last_deg]
        graph.add_edges_from([(index, int(neigh)) for neigh in neighbors])
        prec_deg = last_deg

    return graph

def __one_level(graph, status) :
    """
    TODO
    Compute one level of communities
    """
    modif = True
    nb_pass_done = 0
    cur_mod = __modularity(status)
    new_mod = cur_mod

    while modif  and nb_pass_done != __PASS_MAX :
        cur_mod = new_mod
        modif = False
        nb_pass_done += 1

        for node in graph.nodes() :
            com_node = status.node2com[node]
            # k_i / 2m
            # should be m?
            degc_totw_p = status.gdegrees_p.get(node, 0.) / (status.total_weight_p*2.)
            degc_totw_n = status.gdegrees_n.get(node, 0.) / (status.total_weight_n*2.)
            
            neigh_communities = __neighcom(node, graph, status)

            # change...
            __remove(node, com_node,
                     neigh_communities[com_node][0], neigh_communities[com_node][1],
                     status)
            best_com = com_node
            best_increase = 0
            for com, (dnc_p, dnc_n) in neigh_communities.items() :
                # dnc: k_{i, in}
                # status.degrees.get(com, 0.): \sum_{tot} of com
                incr = (dnc_p  - status.degrees_p.get(com, 0.) * degc_totw_p)
                incr -= (dnc_n  - status.degrees_n.get(com, 0.) * degc_totw_n)

                if incr > best_increase :
                    best_increase = incr
                    best_com = com
            # change
            __insert(node, best_com,
                    neigh_communities[best_com][0], neigh_communities[best_com][1],
                    status)
            if best_com != com_node :
                modif = True
        new_mod = __modularity(status)
        if new_mod - cur_mod < __MIN :
            break

        
def split_graph_by_sign(graph):
    graph_p, graph_n = nx.Graph(), nx.Graph()

    def filter_edges_by_sign(g, s):
        for i, j in g.edges_iter():
            for key, d in g[i][j].items():
                if key == s:
                    yield (i, j, {'weight': d['weight']})

    graph_p.add_nodes_from(graph.nodes_iter())
    graph_n.add_nodes_from(graph.nodes_iter())

    graph_p.add_edges_from(filter_edges_by_sign(graph, 1))
    graph_n.add_edges_from(filter_edges_by_sign(graph, -1))
    return graph_p, graph_n


class Status(object):
    """
    add pos and neg matrix
    
    
    To handle several data in one struct.

    Could be replaced by named tuple, but don't want to depend on python 2.6
    """
    node2com = {}
    total_weight = 0
    internals = {}
    degrees = {}
    gdegrees = {}

    def __init__(self) :
        self.node2com = dict([])

        self.degrees_p = defaultdict(float)  # $\sum_{tot}$
        self.degrees_n = defaultdict(float)
        self.gdegrees_p = defaultdict(float)  # k_i
        self.gdegrees_n = defaultdict(float)         
        self.internals_p = defaultdict(float)  # $\sum_{in}$
        self.internals_n = defaultdict(float)
        
        self.total_weight_p = 0
        self.total_weight_n = 0
        
        self.loops_p = dict([])
        self.loops_n = dict([])

    def __str__(self) :
        return ("node2com : " + str(self.node2com) + " degrees : "
            + str(self.degrees) + " internals : " + str(self.internals)
            + " total_weight : " + str(self.total_weight))

    def copy(self) :
        """Perform a deep copy of status"""
        new_status = Status()
        new_status.node2com = self.node2com.copy()
        
        new_status.internals_p = self.internals_p.copy()
        new_status.degrees_p = self.degrees_p.copy()
        new_status.gdegrees_p = self.gdegrees_p.copy()
        new_status.total_weight_p = self.total_weight_p

        new_status.internals_n = self.internals_n.copy()
        new_status.degrees_n = self.degrees_n.copy()
        new_status.gdegrees_n = self.gdegrees_n.copy()
        new_status.total_weight_n = self.total_weight_n        

        
    def init(self, graph, part = None) :
        """Initialize the status of a graph with every node in one community"""
        graph_p, graph_n = split_graph_by_sign(graph)

        assert graph.number_of_edges() == (graph_p.number_of_edges() + graph_n.number_of_edges())

        count = 0  

        self.total_weight_p = graph_p.size(weight='weight')  # $m$
        self.total_weight_n = graph_n.size(weight='weight')
        if part == None :
            for node in graph.nodes() :
                self.node2com[node] = count
                deg_p = float(graph_p.degree(node, weight = 'weight'))
                deg_n = float(graph_n.degree(node, weight = 'weight'))
                if deg_p < 0 or deg_n < 0:
                    raise ValueError("Bad graph type, use positive weights")
                self.degrees_p[count] = deg_p
                self.gdegrees_p[node] = deg_p
                self.degrees_n[count] = deg_n
                self.gdegrees_n[node] = deg_n
                
                self.loops_p[node] = float(
                    graph_p.get_edge_data(node, node, {"weight":0}).get("weight", 1))
                self.loops_n[node] = float(
                    graph_n.get_edge_data(node, node, {"weight":0}).get("weight", 1))

                self.internals_p[count] = self.loops_p[node]
                self.internals_n[count] = self.loops_n[node]
                count += 1
        else :
            for node in graph.nodes() :
                com = part[node]
                self.node2com[node] = com  # BAD: why not just copy?
                deg_p = float(graph_p.degree(node, weight = 'weight'))
                deg_n = float(graph_n.degree(node, weight = 'weight'))
                
                self.degrees_p[com] += deg_p
                self.gdegrees_p[node] = deg_p
                self.degrees_n[com] += deg_n
                self.gdegrees_n[node] = deg_n

                self.loops_p[node] = float(
                    graph_p.get_edge_data(node, node, {"weight":0}).get("weight", 1))
                self.loops_n[node] = float(
                    graph_n.get_edge_data(node, node, {"weight":0}).get("weight", 1))
                
                inc_p, inc_n = (0., 0.)

                for neighbor, keyed_datas in graph[node].items() :
                    for key, datas in keyed_datas.items():
                        weight = datas.get("weight", 1)
                        if weight <= 0 :
                            raise ValueError("Bad graph type, use positive weights")
                        if part[neighbor] == com:
                            if neighbor == node:
                                if datas['sign'] == 1:
                                    inc_p += weight
                                else:
                                    inc_n += weight
                            else:
                                if datas['sign'] == 1:
                                    inc_p += weight / 2
                                else:
                                    inc_n += weight / 2
                print(self.internals_p)
                self.internals_p[com] += inc_p
                self.internals_n[com] += inc_n
               

def __neighcom(node, graph, status):
    """
    ADAPT
    Compute the communities in the neighborood of node in the graph given
    with the decomposition node2com

    Return:
    dict of neighboring community -> weight sum between 'node' and that community
    """
    weights = defaultdict(lambda : [0, 0])  # position 0 for pos weight, 1 for neg weight
    for neighbor, keyed_datas in graph[node].items():
        for key, datas in keyed_datas.items():
            if neighbor != node:
                weight = datas.get("weight", 1)
                neighborcom = status.node2com[neighbor]            
                if datas['sign'] == 1:
                    weights[neighborcom][0] += weight
                else:
                    weights[neighborcom][1] += weight
    return weights


def __remove(node, com, weight_p, weight_n, status) :
    """
    ADAPT
    Remove node from community com and modify status"""
    status.degrees_p[com] = (status.degrees_p.get(com, 0.)
                            - status.gdegrees_p.get(node, 0.))
    status.degrees_n[com] = (status.degrees_n.get(com, 0.)
                            - status.gdegrees_n.get(node, 0.))
        
    status.internals_p[com] = float(status.internals_p.get(com, 0.) -
                                    weight_p - status.loops_p.get(node, 0.))
    status.internals_n[com] = float(status.internals_n.get(com, 0.) -
                                    weight_n - status.loops_n.get(node, 0.))
    status.node2com[node] = -1


def __insert(node, com, weight_p, weight_n, status) :
    """ Insert node into community and modify status"""
    status.node2com[node] = com
    status.degrees_p[com] = (status.degrees_p.get(com, 0.) +
                             status.gdegrees_p.get(node, 0.))
    status.degrees_n[com] = (status.degrees_n.get(com, 0.) +
                             status.gdegrees_n.get(node, 0.))
    status.internals_p[com] = float(status.internals_p.get(com, 0.) +
                                    weight_p + status.loops_p.get(node, 0.))
    status.internals_n[com] = float(status.internals_n.get(com, 0.) +
                                    weight_n + status.loops_n.get(node, 0.))


def __modularity(status) :
    """
    ADAPT
    
    Compute the modularity of the partition of the graph faslty using status precomputed
    """
    # links = float(status.total_weight)
    # result = 0.
    # for community in set(status.node2com.values()) :
    #     in_degree = status.internals.get(community, 0.)
    #     degree = status.degrees.get(community, 0.)
    #     if links > 0 :
    #         result = result + in_degree / links - ((degree / (2.*links))**2)

    links_p = float(status.total_weight_p)
    links_n = float(status.total_weight_n)
    result = 0.
    for community in set(status.node2com.values()) :
        in_degree_p = status.internals_p.get(community, 0.)
        in_degree_n = status.internals_n.get(community, 0.)
        degree_p = status.degrees_p.get(community, 0.)
        degree_n = status.degrees_n.get(community, 0.)
        if links_p > 0 :
            result += in_degree_p / (2.*links_p) - ((degree_p / (2.*links_p))**2)  ## BUG FIX
        if links_n > 0:
            result -= in_degree_n / (2.*links_n) - ((degree_n / (2.*links_n))**2)
    return result


def main() :
    """Main function to mimic C++ version behavior"""
    try :
        filename = sys.argv[1]
        graphfile = __load_binary(filename)
        partition = best_partition(graphfile)
        print(str(modularity(partition, graphfile)), file=sys.stderr)
        for elem, part in partition.items() :
            print(str(elem) + " " + str(part))
    except (IndexError, IOError):
        print("Usage : ./community filename")
        print("find the communities in graph filename and display the dendrogram")
        print("Parameters:")
        print("filename is a binary file as generated by the ")
        print("convert utility distributed with the C implementation")
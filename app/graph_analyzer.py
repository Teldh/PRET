import networkx as nx
import igraph
import pandas as pd
import numpy as np
from networkx.readwrite import json_graph
import json
import codecs
import csv
import ast



def get_annotations(annotator, dataset):
    '''
    Returns a comma separated list of prerequisite relations inserted by a given annotator
    The output has the format:
        prereq1,subsid1
        prereq1,subsid2
        prereq2,subsid1
        ...
    '''
    
    with open('output_files//annotations_'+annotator+'.csv', 'w', encoding='utf-8', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        for concept in dataset["name"]:
            subsids = ast.literal_eval(dataset.loc[dataset['name'].tolist().index(concept)]["subsidiaries "+annotator])
            for s in subsids:
                csv_writer.writerow([concept] + [s])
			
			
				
def create_graphs(filename, dataset, annotator):
    '''
    Creates both networkx and igraph native graphs.
    
    INPUT:
    filename: a csv file in the form:
        annotator's name
        prereq1,subsid1
        prereq1,subsid2
        prereq2,subsid1
    
    dataset: a pandas dataframe
    '''

    G_nx = nx.DiGraph()
    G_ig = igraph.Graph(directed=True)
    annotator = annotator
    G_nx.add_nodes_from(dataset['name'].tolist())
    G_ig.add_vertices(dataset['name'].tolist())
    for index, row in filename.iterrows():
        prereq = row[0]
        subsid = row[1]



        G_nx.add_edge(prereq, subsid)
        try:
            weight = row[2]
        except:
            weight = None

        if weight:
            if annotator=="3" or annotator=="5" or annotator=="6":
                G_nx[prereq][subsid]['threshold'] = weight
            else:
                if type(annotator) is not list and annotator.startswith("uid"):
                    G_nx[prereq][subsid]['weight'] = weight
                else:
                    if type(annotator) is str and annotator.startswith("gold"):
                        G_nx[prereq][subsid]['weight'] = weight

        G_ig.add_edge(dataset['name'].tolist().index(prereq),
                      dataset['name'].tolist().index(subsid))
    return G_nx, G_ig, annotator
	
	
	
def compute_metrics(networkx_graph, igraph_graph):
    '''
    Computes basic metrics of a given graph.
    
    INPUT:
    a graph passed in two forms (networkx_graph and igraph_graph must represent the same graph!)
    
    RETURNS:
    a dict containing basic metrics:
        number of edges,
        number of nodes, 
        a list of disconnected nodes,
        diameter of the graph,
        node with max in-degree (and its in-degree value),
        node with max out-degree (and its out-degree value)
    '''
    
    # size
    num_nodes = len(nx.nodes(networkx_graph))
    num_edges = len(nx.edges(networkx_graph))

    # disconnected nodes
    disconnected = [node for node in nx.isolates(networkx_graph)]

    # degrees
    max_out_degree = igraph.GraphBase.maxdegree(igraph_graph, mode="OUT")
    max_in_degree = igraph.GraphBase.maxdegree(igraph_graph, mode="IN")
    id_out = igraph_graph.degree(mode="OUT").index(max_out_degree)
    id_in = igraph_graph.degree(mode="IN").index(max_in_degree)
    node_max_out = igraph_graph.vs[id_out]['name']
    node_max_in = igraph_graph.vs[id_in]['name']

    # diameter of the graph
    diameter = igraph.GraphBase.diameter(igraph_graph, directed=True, unconn=True)
    
    return {'num_nodes': num_nodes,
            'num_edges': num_edges,
            'disconnected': disconnected, 
            'diameter': diameter,
            "max out degree": (node_max_out, max_out_degree),
            "max in degree": (node_max_in, max_in_degree)}
			
			
def detect_loops(networkx_graph, igraph_graph, dataset, remove=False):
    '''
    Finds (and possibly removes) mutual edges and loops from a graph.
    If remove is True, the edges will be removed INPLACE.
    
    RETURNS:
    a dict with lists of mutual edges and loops that have been detected.
    
    '''

    detected_cycles = {'mutuals': [],
                       'loops': []}

    if not (nx.is_directed_acyclic_graph(networkx_graph)):

        mutuals = [i for i, e in enumerate(igraph.GraphBase.is_mutual(igraph_graph)) if e]
        iter_mut = iter(mutuals)

        for edge in zip(iter_mut, iter_mut):
            source = igraph_graph.vs[igraph_graph.es[edge[0]].source]['name']
            target = igraph_graph.vs[igraph_graph.es[edge[0]].target]['name']
            detected_cycles['mutuals'].append((source, target))
            detected_cycles['mutuals'].append((target, source))
            detected_cycles['loops'].append((source, target))
            
            if remove:
                # keep only the relation that has as prerequisite the term appearing first in the text
                if dataset.index[dataset['name']==source][0] < dataset.index[dataset['name']==target][0]:   
                    if networkx_graph.has_edge(target, source):
                        networkx_graph.remove_edge(target, source)
                        igraph_graph.delete_edges([(target, source)])
                        

                elif dataset.index[dataset['name']==target][0] < dataset.index[dataset['name']==source][0]:
                    if networkx_graph.has_edge(source, target):
                        networkx_graph.remove_edge(source, target)
                        igraph_graph.delete_edges([(source, target)])

                        
        loops = [i for i, e in enumerate(igraph.GraphBase.is_loop(igraph_graph)) if e]
        iter_loop = iter(loops)
      
        for edge in zip(iter_loop, iter_loop):
            source = igraph_graph.vs[igraph_graph.es[edge[0]].source]['name']
            target = igraph_graph.vs[igraph_graph.es[edge[0]].target]['name']
            detected_cycles['loops'].append((source, target))
            
            # TODO: add code for removing loops (not needed now)
                                           
        
        return detected_cycles
		
		
		
def detect_transitive_edges(graph, cutoff, find_also_not_inserted=False):
    '''
    Detect transitive relations manually inserted by the annotator.
    If "find_also_not_inserted", the algorithm searches also all the
    potential transitives in the graph (before a cutoff).
    
    INPUT:
    graph
    cutoff: an int number of edges, after which the searching algorithm stops.
    
    OUTPUT
    A dict with transitives,
    indexed whether they have been manually inserted by the annotator
    or automatically detected in the graph by the search algorithm.
    '''
    
    transitives = {'manually inserted': [],
                   'automatically detected': []}
    
    if cutoff > 10:
        cutoff = 10
    
    for source_node in graph.nodes():
        other_nodes = list(graph.nodes())
        other_nodes.remove(source_node)

        for target_node in other_nodes:
            paths = nx.all_simple_paths(graph, source_node, target_node, cutoff)

            for path in paths:
                if len(path)>2 and graph.has_edge(source_node, target_node): 
                    if (source_node, target_node) not in transitives['manually inserted']:
                        transitives['manually inserted'].append((source_node, target_node))
                    
                    else:
                        if find_also_not_inserted:
                            if (source_node, target_node) not in transitives['automatically detected']:
                                transitives['automatically detected'].append((source_node, target_node))
    return transitives
	
	
	
def detect_clusters(igraph_graph):
    '''
    Detects clusters in a graph created with igraph.
    Clusters are detected using infomap clusterization algorithm.
    
    INPUT
    igraph graph
    
    RETURNS
    a list of the same length of nodes in the graph
    
    '''

    infomap_clusters = igraph_graph.community_infomap()
    membership = infomap_clusters.membership
        
    return membership


def plot_clusters(igraph_graph):
    '''
    graph: a graph created with igraph
    clusters: detected with a community detection algorithm of igraph
    '''
    
    membership = detect_clusters(igraph_graph)
    pal = igraph.drawing.colors.ClusterColoringPalette(max(membership)+1)
    igraph_graph.vs['color'] = pal.get_many(membership)

    return igraph.plot(igraph_graph, bbox=(0, 0, 2000, 2000), layout=igraph_graph.layout("fr"),
                             vertex_label=range(igraph_graph.vcount()), vertex_label_size=10,
                             edge_width=0.7, edge_arrow_size=0.7, edge_arrow_width=0.7)
							 
							 
							 
def create_graph_dict(dataset, gold_matrix, annotator, metrics, detected_cycles, transitives, membership, G_nx):
    '''
    Collects all the info about the graph in a python dict
    (to be then passed to save_to_json in order to obtain the final json)

    info to encode:
    nodes: id, name, sections, freq (from section we can derive first occurrance)
    links: source, target, cluster, annotators (from annotators we can derive agreement)
    '''

    if type(annotator) is str and annotator.startswith("uid"):
        ref = annotator.strip('][').split(', ')
        annotator = ref
    '''UP: Controllo per il bezier graph che passava una stringa anzichè una lista'''
    graph_dict = {"annotator": annotator,
                  "directed": True,
                  "nodes": [],
                  "links": [],
                  "num nodes": metrics['num_nodes'],
                  "num links": metrics['num_edges'],
                  "diameter": metrics['diameter'],
                  "max out degree": metrics['max out degree'],
                  "max in degree": metrics['max in degree'],
                  "detected cycles": detected_cycles,
                  "disconnected nodes": metrics['disconnected']}
    indexes = gold_matrix.index
    for concept in dataset["name"]:
        if concept in indexes:
            ID = dataset[dataset['name']==concept].index.tolist()[0]

            try:
                sections_list = ast.literal_eval(dataset.loc[ID]["sections"])
                sentence_list = ast.literal_eval(dataset.loc[ID]["sentence"])
                # convert the section_list to string to make it serializable with json
                sentence_list = list(map(str, sentence_list))
                sections_list = list(map(int, sections_list))
            except:
                sections_list = (dataset.loc[ID]["sections"])
                sentence_list = (dataset.loc[ID]["sentence"])
                temp = []
                temp2 = []
                for item1 in sentence_list:
                    temp2.append(int(item1))
                sentence_list = temp2
                for item in sections_list:
                    temp.append(str(item))
                sections_list = temp


            # add info to "nodes"
            graph_dict["nodes"].append({"id": ID,
                                        "name": concept,
                                        "sections": sections_list,
                                        "sentence": sentence_list,
                                        "frequence": int(dataset.loc[ID]["frequence"]),
                                        "cluster": membership[ID]})

            for other_concept in dataset["name"]:
                if other_concept in indexes:
                    ID_source = gold_matrix.index.tolist().index(concept)
                    ID_target = gold_matrix.index.tolist().index(other_concept)
                    if G_nx.has_edge(concept, other_concept):
                        annotators_list = []
                        if not pd.isna(gold_matrix.loc[concept][other_concept]):
                            try:
                                annotators_list = ast.literal_eval(gold_matrix.loc[concept][other_concept])
                            except:
                                annotators_list = (gold_matrix.loc[concept][other_concept])

                        if type(annotator) is not list and annotator.startswith("uid"):
                        # add info to "links"

                            graph_dict["links"].append({"source": ID_source,
                                                    "target": ID_target,
                                                    "annotators": annotators_list,
                                                    "weight": G_nx[concept][other_concept]['weight']})
                        else:
                            if type(annotator) is list:

                                x = annotators_list.split()
                                graph_dict["links"].append({"source": ID_source,
                                                            "target": ID_target,
                                                            "annotators": x,
                                                            "weight": G_nx[concept][other_concept]['weight']})

                            else:
                                if annotator == "3" or annotator == "5" or annotator == "6":
                                    graph_dict["links"].append({"source": ID_source,
                                                    "target": ID_target,
                                                    "annotators": annotators_list,
                                                    "threshold":G_nx[concept][other_concept]['threshold']})
                                else:

                                    graph_dict["links"].append({"source": ID_source,
                                                            "target": ID_target,
                                                            "annotators": annotators_list,})
        #                                            "is_transitive": (concept, other_concept) in transitives['manually inserted'],
        #                                            "has_mutual": (concept, other_concept) in detected_cycles['mutuals']})
#                try:
 #                   graph_dict["links"].append({
  #                  "is_transitive": (concept, other_concept) in transitives['manually inserted'],
   #                 "has_mutual": (concept, other_concept) in detected_cycles['mutuals']})
    #            except:
     #               pass
        
    return graph_dict
	
	
	
	
def export_to_json(filename, graph_dict):
    '''
    save to external json
    '''
    with open(filename, 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(graph_dict, indent=4,
                                 sort_keys=True,
                                 separators=(',', ': '),
                                 ensure_ascii=False))
								 
								 
								 
								 
#G_nx, G_ig, annotator = create_graphs('datasets//prova_relazioni_tool.csv', dataset)
#metrics = compute_metrics(G_nx, G_ig)
#detected_cycles = detect_loops(G_nx, G_ig)
#trans_dict = detect_transitive_edges(G_nx, cutoff=metrics['diameter'])
#membership = detect_clusters(G_ig)
#graph_dict = create_graph_dict(dataset, gold_with_annotators, annotator, metrics, detected_cycles, trans_dict, membership)
#output_json = export_to_json("output_files//prova.json", graph_dict)




def get_roots(graph):
    roots = []

    for node in graph:
        if len(list(graph.predecessors(node)))==0: #è root
            roots.append(node)

    return roots

def longest_path(graph):
    return nx.dag_longest_path(graph)
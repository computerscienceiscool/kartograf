import math
from typing import Iterable, Callable, List
import itertools

import networkx as nx


from gufe import AtomMapper, AtomMapping
from gufe import SmallMoleculeComponent

from openfe.setup import Network

class minimal_spanning_graph_networker():
    
    def build_network(self, ligands: Iterable[SmallMoleculeComponent],
                           mappers: Iterable[AtomMapper],
                           scorer: Callable[[AtomMapping], float]):
        """Plan a Network which connects all ligands with minimal cost

        Parameters
        ----------
        ligands : Iterable[SmallMoleculeComponent]
        the ligands to include in the Network
        mappers : Iterable[AtomMapper]
        the AtomMappers to use to propose mappings.  At least 1 required,
        but many can be given, in which case all will be tried to find the
        lowest score edges
        scorer : Scoring function
        any callable which takes a AtomMapping and returns a float
        """
        nodes = list(ligands)

        # First create a network with all the proposed mappings (scored)
        mapping_generator = itertools.chain.from_iterable(
            mapper.suggest_mappings(molA, molB)
            for molA, molB in itertools.combinations(nodes, 2)
            for mapper in mappers
        )
        mappings = [mapping.with_annotations({'score': scorer(mapping)})
                    for mapping in mapping_generator]
        network = Network(mappings, nodes=nodes)

        # Next analyze that network to create minimal spanning network. Because
        # we carry the original (directed) AtomMapping, we don't lose
        # direction information when converting to an undirected graph.
        min_edges = nx.minimum_spanning_edges(nx.MultiGraph(network.graph),
                                            weight='score')
        min_mappings = [edge_data['object'] for _, _, _, edge_data in min_edges]
        min_network = Network(min_mappings)
        missing_nodes = set(nodes) - set(min_network.nodes)
        if missing_nodes:
            raise RuntimeError("Unable to create edges to some nodes: "
                            + str(list(missing_nodes)))

        return min_network

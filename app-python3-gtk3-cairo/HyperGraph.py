# -*- coding: utf-8 -*-

## @file HyperGraph.py
## @package HyperGraph

import random as rnd

import numpy as np
import math
import cairo
import time
# import numba
# from numba import double
# from numba.decorators import jit
# import locale
# locale.setlocale(locale.LC_NUMERIC, 'C')

import pickle

from Vert import Node, HBNode, Vert
from VertArranger import VertArranger
from Utils import Utils
from OCL import OCL

## Klasa HyperGraph.
#  Główna klasa projektu. Tu znajdują się wszystkie najważniejsze elementy.
#  Zawiera zmienne słownikowe X, U, P oraz zmienną zbioru activated_id_set. Są to główne elementy modelu hipergrafu. 
#  Definiują one postać hipergrafu.
#  Dodatkowo zawiera zmienne projektu project_properties, selected_id_list.
#  Model hipergrafu może ewoluować, na przykłąd na podstawie jakiegoś algorytmu.
class HyperGraph(object):

    # CREATE

    ## Konstruktor obiektu hipergrafu.
    def __init__(self):

        ## Zmienna słownikowa przechowująca wierzchołki hipergrafu.
        # Przykładowa zawartość:
        # {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}.
        
        self.X = dict()

        ## Zmienna słownikowa przechowująca hipergałęzie hipergrafu.
        # Przykładowa zawartość:
        # {16: 16:ha1, 17: 17:ha2, 18: 18:ha3, 19: 19:ha4, 10: 10:ha5, 11: 11:ha6, 12: 12:ha7, 13: 13:ha8, 14: 14:ha9, 15: 15:ha10}
        self.U = dict()

        ## Zmienna słownikowa przechowująca relacje wierzchołków do hipergałęzi w hipergrafie.
        # Przykładowa zawartość:
        # {16: (6, 7), 17: (7, 8), 18: (8, 9), 19: (3, 8), 10: (0, 1), 11: (1, 2), 12: (2, 3), 13: (3, 4), 14: (4, 5), 15: (5, 6)}
        self.P = dict()
        
        ## Zmienna zbioru nieuporządkowanego przechowująca identyfikatory wyróżnionych elementów hipergrafu.
        self.activated_id_set = set()

        ## Zmienna przechowująca historię kroków ewolucji hipergrafu.
        self.evolution_history = list()

        ## Zmienna typu lista przechowująca w odpowiedniej kolejności id klikniętych wierzchołków.
        # Przykładowa zawartość:
        # [0, 9]
        self.selected_id_list = []

        ## Zmienna zawierająca ustawienia aktualnego projektu.
        self.project_properties = {
            'additional_xnode_properties': {},
            'additional_node_properties': {},
            'additional_hbnode_properties': {}
        }

        ## Zmienna informująca o numerze aktualnie przeglądanego kroku ewolucji hipergrafu.
        self.evolution_view_current_frame = -1

        self.save_evolutionary_state(incrementcounter=True)

    ## Metoda tworząca nowy obiekt reprezentujący wizualnie wierzchołek.
    # @param name Nazwa wierzchołka.
    # @param position Współrzędne utworzenia obiektu.
    # @param prop_dict Słownik właściwości do przypisania wierzchołkowi.
    # @return Id nowoutworzonego obiektu.
    def add_node(self, name, position, prop_dict, normalize_pos=True):

        pd = dict(self.project_properties['additional_xnode_properties'])
        pd.update(self.project_properties['additional_node_properties'])
        pd.update(prop_dict)

        ve = Node(name=name, pos=position, prop_dict=pd)

        if normalize_pos:
            self.normalize_xnode_position(ve)

        self.X[ve.get_id()] = ve

        # print(self)

        return ve.get_id()

    ## Metoda tworząca nowy obiekt reprezentujący wizualnie hipergałąź.
    # @param name Nazwa hipergałęzi.
    # @param type Typ hipergałęzi (hiperkrawędź, hiperłuk, hiperpętla).
    # @param position Współrzędne utworzenia obiektu.
    # @param prop_dict Słownik właściwości do przypisania hipergałęzi.
    # @return Id nowoutworzonego obiektu.
    def add_hbnode(self, name, hbtype, position, prop_dict, normalize_pos=True):
        pd = dict(self.project_properties['additional_xnode_properties'])
        pd.update(self.project_properties['additional_hbnode_properties'])
        pd.update(prop_dict)

        hbnode = HBNode(name=name, hbtype=hbtype, pos=position, prop_dict=pd)

        if normalize_pos:
            self.normalize_xnode_position(hbnode)

        self.U[hbnode.get_id()] = hbnode

        return hbnode.get_id()

    ## Metoda tworząca nową hipergałąź.
    # Obejmuje to stworzenie nowej relacji wierzchołek-hipergałąź oraz stworzenie nowego obiektu reprezentującego wizualnie hipergałąź.
    # @param name Nazwa hipergałęzi.
    # @param type Typ hipergałęzi (hiperkrawędź, hiperłuk, hiperpętla).
    # @param nodes_id_list Lista id wierzchołków do przypisania hiperkrawędzi.
    # @param prop_dict Słownik właściwości do przypisania hipergałęzi.
    def add_hyperbranch(self, name, hbtype, nodes_id_list, prop_dict, normalize_pos=True):
        pos_com = self.get_xnodes_center_of_mass_by_xnodes_id_list(nodes_id_list)

        hbid = self.add_hbnode(name=name, hbtype=hbtype, position=pos_com, prop_dict=prop_dict, normalize_pos=normalize_pos)

        # hyperedge: P[hid] = [set(elems)]
        if hbtype == HBNode.HB_HYPEREDGE:
            self.P[hbid] = set(nodes_id_list)
        # hyperloop: P[hid] = [tuple(elems)]
        elif hbtype == HBNode.HB_HYPERLOOP:
            self.P[hbid] = tuple(nodes_id_list)
        # hyperarc:  P[hid].append(tuple(elems)) # TODO: do or do not?
        elif hbtype == HBNode.HB_HYPERARC:
            self.P[hbid] = tuple(nodes_id_list)
        else:
            self.P[hbid] = list(nodes_id_list)

        hbnode = self.get_hbnode_by_id(hbid)
        hbnode.set_radius_from_degree(self.get_xnode_degree_by_xnode_id(hbid))
        hbnode.set_mass_from_degree(self.get_xnode_degree_by_xnode_id(hbid))
        hbnode.set_property_value('elements', str(self.get_hyperbranch_by_id(hbid)))

        for nid in nodes_id_list:
            node = self.get_node_by_id(nid)
            node.set_radius_from_degree(self.get_xnode_degree_by_xnode_id(nid))
            node.set_mass_from_degree(self.get_xnode_degree_by_xnode_id(nid))

        # print(self)

        return hbnode.get_id()

    # READ

    ## Metoda zwracająca obiekt wizualnie reprezentujący element hipergrafu po jego id.
    # Może być to wierzchołek lub hipergałąź.
    # @param xid Id elementu.
    # @return Obiekt wizualnie reprezentujący element.
    def get_xnode_by_id(self, xid):
        if xid in self.X:
            return self.get_node_by_id(xid)

        if xid in self.U:
            return self.get_hbnode_by_id(xid)

        return None

    ## Metoda zwracająca maksymalny id elementu hipergrafu.
    # @return Wartość liczbowa maksymalnego id elementu w hipergrafie.
    def get_max_xnode_index(self):
        index_list = list(self.X.keys()) + list(self.U.keys())

        try:
            return max(index_list)
        except ValueError as ve:
            return -1

    ## Metoda zwracająca stopień elementu jako liczbę elementów z nim połączonych.
    # W przypadku wierzchołka jest to liczba hiperkrawędzi, które go zawierają.
    # W przypadku hiperkrawędzi jest to liczba wierzchołków do niej należących.
    # @param xid Id elementu.
    # @param hbtype Opcjonalny typ hipergałęzi.
    # @return Wartość liczbowa stopnia elementu.
    def get_xnode_degree_by_xnode_id(self, xid, hbtype=None):
        if xid in self.X:  # if xnode is node
            return len(set(self.get_all_hyperbranches_id_by_node_id(xid, hbtype)))

        if xid in self.U:  # if xnode is hbnode
            return len(self.get_hyperbranch_by_id(xid))

        return None

    ## Metoda zwracająca obiekt wizualnie reprezentujący wierzchołek po jego id.
    # @param nid Id wierzchołka.
    # @return Obiekt wizualnie reprezentujący wierzchołek.
    def get_node_by_id(self, nid):
        return self.X[nid]

    ## Metoda zwracająca wszystkie id wierzchołków do których da się przejść z danego wierzchołka.
    # @param nid Id wierzchołka.
    # @return Zbiór id wierzchołków do których da się przejść z danego wierzchołka.
    def get_all_reachable_nodes_id_from_node_id(self, nid):
        hbid_list = list(self.get_all_hyperbranches_id_by_node_id(nid))
        reachable_nid_list = []

        for hbid in hbid_list:
            hbranch_list = self.get_hyperbranch_by_id(hbid)  # [hbel1, hbel2...]
            hbnode = self.get_hbnode_by_id(hbid)

            if hbnode.get_hyperbranch_type() == HBNode.HB_HYPEREDGE:
                hbelems = list(hbranch_list)
                hbelems.remove(nid)
                reachable_nid_list += hbelems

            elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERARC:
                hbelems = list(hbranch_list)
                hbelems = hbelems[hbelems.index(nid) + 1:]
                reachable_nid_list += hbelems

            elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERLOOP:  # TODO: zastanowic sie nad stopniem wierzcholka i jego hiperpetlami
                hbelems = list(hbranch_list)
                reachable_nid_list += hbelems

            else:
                assert False

        return set(reachable_nid_list)

    ## Metoda zwracająca wszystkie id wierzchołków z których da się przejść do danego wierzchołka.
    # @param nid Id wierzchołka.
    # @return Zbiór id wierzchołków z których da się przejść do danego wierzchołka.
    def get_all_nodes_id_where_node_id_is_reachable(self, nid):
        hbid_list = list(self.get_all_hyperbranches_id_by_node_id(nid))
        reachable_nid_list = []

        for hbid in hbid_list:
            hbranch_list = self.get_hyperbranch_by_id(hbid)  # [hbel1, hbel2...]
            hbnode = self.get_hbnode_by_id(hbid)

            if hbnode.get_hyperbranch_type() == HBNode.HB_HYPEREDGE:
                hbelems = list(hbranch_list)
                hbelems.remove(nid)
                reachable_nid_list += hbelems

            elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERARC:
                hbelems = list(hbranch_list)
                hbelems = hbelems[:hbelems.index(nid)]
                reachable_nid_list += hbelems

            elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERLOOP:  # TODO: zastanowic sie nad stopniem wierzcholka i jego hiperpetlami
                hbelems = list(hbranch_list)
                reachable_nid_list += hbelems

            else:
                assert False

        return set(reachable_nid_list)

    ## Metoda zwracająca stopień wierzchołka (liczbę hiperkrawędzi do niego połączonych).
    # @param nid Id wierzchołka.
    # @return Wartość liczbowa stopnia wierzchołka.
    def get_node_degree_by_node_id(self, nid):
        return len(set(self.get_all_hyperbranches_id_by_node_id(nid)))

    ## Metoda zwracająca zbiór id hipergałęzi łączących daną parę wierzchołków.
    # @param nid1 Id wierzchołka początkowego.
    # @param nid2 Id wierzchołka końcowego.
    # @param directed Opcjonalny argument sterujący, czy kierunek ma być wzięty pod uwagę czy zignorowany.
    # @return Zbiór id hipergałęzi łączących daną parę wierzchołków.
    def get_connections_between_nodes_by_nodes_id(self, nid1, nid2, directed=True):
        hbid_list_for_nid1 = list(self.get_all_hyperbranches_id_by_node_id(nid1))

        conn_hbid = []

        for hbid in hbid_list_for_nid1:
            hbranch_list_copy = list(self.get_hyperbranch_by_id(hbid))  # [hbel1, hbel2...]
            # print("connections from {} to {} on hyperbranches {}".format(nid1, nid2, hbranch_list_copy))

            hbnode = self.get_hbnode_by_id(hbid)

            if hbnode.get_hyperbranch_type() == HBNode.HB_HYPEREDGE:
                if nid2 in hbranch_list_copy and nid2 != nid1:  # jesli nid2 jest w tej samej hiperkrawedzi co nid1 i nid2 != nid1
                    conn_hbid.append(hbid)
                    # print("conection from {} to {} on he {}".format(nid1, nid2, hbid))

            elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERARC:
                if nid2 in hbranch_list_copy and nid2 != nid1:
                    if directed:
                        nid1_index = hbranch_list_copy.index(nid1)
                        nid2_index = hbranch_list_copy.index(nid2)

                        if nid1_index < nid2_index:  # jesli nid2 jest na dalszym miejscu w tym samym hiperłuku co nid1
                            conn_hbid.append(hbid)
                            # print("conection (directed) from {} to {} on ha {}".format(nid1, nid2, hbid))
                    else:
                        conn_hbid.append(hbid)
                        # print("conection (undirected) from {} to {} on ha {}".format(nid1, nid2, hbid))

            elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERLOOP:
                if nid1 == nid2:  # jesli nid2 jest tym samym co nid1; TODO: jesli len(hbranch_list_copy) > 1?
                    conn_hbid.append(hbid)
                    # print("conection from {} to {} on hl {}".format(nid1, nid2, hbid))

            else:
                assert False

        return set(conn_hbid)

    ## Metoda zwracająca obiekt reprezentujący wizualnie hipergałąź po id hipergałęzi.
    # @param hid Id hipergałęzi.
    # @return Obiekt reprezentujący wizualnie hipergałąź.
    def get_hbnode_by_id(self, hid):
        return self.U[hid]

    ## Metoda zwracająca zestaw (listę, krotkę, zbiór) id wierzchołków w danej hipergałęzi.
    # @param hid Id hipergałęzi.
    # @return Zestaw id wierzchołków w formie listy, zbioru lub krotki.
    def get_hyperbranch_by_id(self, hid):
        return self.P[hid]  # e.g. (4,5,6) or {1,2,3}

    ## Metoda zwracająca id wszystkich elementów hipergrafu.
    # Nie jest istotny typ elementu, może to być wierzchołek lub hipergałąź.
    # @return Lista id wszystkich elementów w hipergrafie.
    def get_all_xnodes_id(self):
        return self.get_all_nodes_id() + self.get_all_hyperbranches_id()

    ## Metoda zwracająca id wszystkich wierzchołków hipergrafu.
    # @return Lista id wszystkich wierzchołków w hipergrafie.
    def get_all_nodes_id(self):
        return [nid for nid in self.X.keys()]

    ## Metoda zwracająca id wszystkich hipergałęzi hipergrafu.
    # @return Lista id wszystkich hipergałęzi w hipergrafie.
    def get_all_hyperbranches_id(self):
        return [hbid for hbid in self.U.keys()]

    ## Metoda zwracająca wszystkie id elementów połączonych do danego elementu.
    # Nie jest istotny typ elementu, może to być wierzchołek lub hipergałąź.
    # Nie jest tutaj ważny kierunek połączenia, liczy się po prostu dowolne połączenie.
    # @param xid Id elementu.
    # @return Zbiór id elementów, które są połączone z danym elementem w dowolny sposób
    def get_all_connected_xnodes_id_by_xnode_id(self, xid):
        # if xnode is node then return all byperbranches containing this node
        if xid in self.X.keys():
            return list(self.get_all_hyperbranches_id_by_node_id(xid))

        # if xnode is hyperbranch then return all nodes it connects
        if xid in self.U.keys():
            return self.get_all_nodes_id_by_hyperbranch_id(xid)

    ## Metoda zwracająca wszystkie id wierzchołków połączonych do danego wierzchołka.
    # Nie jest tutaj ważny kierunek działania hipergałęzi wspólnych między danymi wierzchołkami, liczy się po prostu dowolne połączenie.
    # @param nid Id wierzchołka.
    # @return Zbiór id wierzchołków, które są połączone z danym wierzchołkiem.
    def get_all_connected_nodes_id_by_node_id(self, nid):
        nid_by_nid_set = set()

        # get all byperbranches by node id
        hbid_list = list(self.get_all_hyperbranches_id_by_node_id(nid))

        # return set of all nodes in these hyperbranches
        for hbid in hbid_list:
            nid_by_nid_set.update(self.get_all_nodes_id_by_hyperbranch_id(hbid))

        return nid_by_nid_set

    ## Metoda zwracająca wszystkie id wierzchołków należących do danej hipergałęzi.
    # @param hid Id hipergałęzi.
    # @return Lista id wierzchołków, które należą do danej hipergałęzi..
    def get_all_nodes_id_by_hyperbranch_id(self, hid):
        return set(self.get_hyperbranch_by_id(hid))

    ## Metoda zwracająca wszystkie id hipergałęzi do których należy dany wierzchołek.
    # @param nid Id wierzchołka.
    # @param hbtype Opcjonalny typ hipergałęzi, do filtrowania.
    # @return Lista id hipergałęzi, do których wierzchołek należy.
    def get_all_hyperbranches_id_by_node_id(self, nid, hbtype=None):
        hbid_list = self.get_all_hyperbranches_id()
        hbid_by_id_list = []

        for hbid in hbid_list:
            if nid in self.get_hyperbranch_by_id(hbid) and (hbtype is None or self.get_hbnode_by_id(hbid).get_hyperbranch_type() == hbtype):
                hbid_by_id_list.append(hbid)
                # yield hbid # metoda zwraca generator

        return hbid_by_id_list  # metoda zwraca liste

    ## Metoda zwracająca zbiór wierzchołków wspólny dla danych hipergałęzi.
    # @param hbid_list Lista id hipergałęzi do sprawdzenia.
    # @return Zbiór id wierzchołków należących jednocześnie do wszystkich hipergałęzi z listy.
    def get_all_shared_nodes_id_in_hyperbranches_list(self, hbid_list):
        hb_shared_nodes_id = None

        for hbid in hbid_list:
            if hb_shared_nodes_id is None:
                hb_shared_nodes_id = list(self.get_all_nodes_id_by_hyperbranch_id(hbid))
                continue

            nodes_id_for_hb = self.get_all_nodes_id_by_hyperbranch_id(hbid)

            for nid in list(hb_shared_nodes_id):
                if nid not in nodes_id_for_hb:
                    if nid in hb_shared_nodes_id:
                        hb_shared_nodes_id.remove(nid)

        return set(hb_shared_nodes_id)

    ## Metoda zwracająca Id elementu który jest na danej pozycji.
    # @param pos Pozycja, która ma zostać sprawdzona w poszukiwaniu elementów.
    # @param rmul Mnożnik promienia, w którym należy szukać.
    # @return Id elementu znajdującego się na danej pozycji.
    def get_colliding_xnode_id_by_position(self, pos, rmul=4.0):

        all_xid = self.get_all_xnodes_id()

        if len(all_xid) > 0:

            node_id_list = all_xid
            node_id_list.reverse()

            node_pos_array = np.zeros((len(node_id_list), 2))
            node_radius_array = np.zeros(len(node_id_list))

            for i, xnode in enumerate([self.get_xnode_by_id(vid) for vid in node_id_list]):
                node_pos_array[i] = xnode.get_position()
                node_radius_array[i] = xnode.get_radius()

            node_dist_vecs = node_pos_array - [pos]
            # norms = np.linalg.norm(node_dist_vecs, axis=1)
            # tests = norms < (node_radius_array*rmul)
            # selected = tests.nonzero()[0]

            sqrdists = node_dist_vecs[...,0]**2 + node_dist_vecs[...,1]**2

            closest = sqrdists.argmin()
            closestdistsqr = sqrdists[closest]

            selected = list()

            if closestdistsqr < (node_radius_array[closest]*rmul)**2:
                selected.append(closest)


            if len(selected) > 0:
                return node_id_list[selected[0]]

        return None

        # # for ve in sorted([self.get_xnode_by_id(vid) for vid in self.get_all_xnodes_id()], key=lambda x: x.get_radius()):
        # for ve in reversed([self.get_xnode_by_id(vid) for vid in self.get_all_xnodes_id()]):
        #     if ve.is_colliding(pos, rmul):
        #         print("colliding node: {}".format(ve.get_id()))
        #         return ve.get_id()
        # return None

    ## Metoda zwracająca id najbliższego elementu hipergrafu do id danego elementu.
    # @param xid Id elementu, do którego należy wyszukać najbliższy element.
    # @param xid_list Opcjonalna lista id elementów, z których należy korzystać. Jeśli nie jest ustawiona, przeszukiwane są wszystkie wierzchołki.
    # @return Id najbliższego elemetu.
    def get_closest_xnode_id_by_xnode_id(self, xid, xid_list=None):
        # nodes = [self.get_node_by_id(nid) for nid in self.get_all_nodes_id()]

        if xid_list is None:
            node_id_list = self.get_all_xnodes_id()
        else:
            node_id_list = list(xid_list)

        closest_xnode = None

        xnode = self.get_xnode_by_id(xid)
        for nid in node_id_list:
            if nid != xid:
                if closest_xnode is None:
                    closest_xnode = self.get_xnode_by_id(nid)
                else:
                    if xnode.distance_norm_from(self.get_xnode_by_id(nid)) < xnode.distance_norm_from(closest_xnode):
                        closest_xnode = self.get_xnode_by_id(nid)

        # print("closest to {} is {}".format(xid, closest_xnode.get_id()))

        return closest_xnode.get_id() if closest_xnode is not None else None

    ## Metoda zwracająca listę zaznaczonych elementów hipergrafu.
    # @return Lista elementów zaznaczonych w kolejności zaznaczania (ostatni element zaznaczony jako ostatni).
    def get_selected_xnodes_id(self):
        return list(self.selected_id_list)

    ## Metoda zwracająca zbiór wyróżnionych elementów hipergrafu.
    # @return Zbiór elementów wyróżnionych .
    def get_activated_xnodes_id(self):
        return set(self.activated_id_set)

    ## Metoda zwracająca listę zaznaczonych wierzchołków hipergrafu.
    # @return Lista wierzchołków zaznaczonych w kolejności zaznaczania (ostatni element zaznaczony jako ostatni).
    def get_selected_nodes_id(self):
        return [xid for xid in self.get_selected_xnodes_id() if self.get_xnode_by_id(xid).is_of_vert_type(Vert.T_NODE)]

    ## Metoda zwracająca listę zaznaczonych hipergałęzi hipergrafu.
    # @return Lista hipergałęzi zaznaczonych w kolejności zaznaczania (ostatni element zaznaczony jako ostatni).
    def get_selected_hbnodes_id(self):
        return [xid for xid in self.get_selected_xnodes_id() if self.get_xnode_by_id(xid).is_of_vert_type(Vert.T_HBRANCH)]

    ## Metoda obliczająca środek masy danych elementów.
    # @param xid_list Lista id elementów, z której należy wyznaczyć środek masy.
    # @return Punkt środka masy jako tablica biblioteki NumPy.
    def get_xnodes_center_of_mass_by_xnodes_id_list(self, xid_list):
        mass = 0.0
        c_o_m = np.array((0.0, 0.0))

        for xid in xid_list:
            xnode = self.get_xnode_by_id(xid)
            # c_o_m += xnode.get_position() * xnode.get_mass()
            # mass += xnode.get_mass()
            c_o_m += xnode.get_position()
            mass += 1.0

        c_o_m /= mass

        return c_o_m

    ## Metoda generująca zbiór elementów elementów, które nie należą do żadnej hipergałęzi.
    # @return Zbiór elementów elementów, które nie należą do żadnej hipergałęzi.
    def get_all_unconnected_nodes_id(self):
        all_nodes_id = self.get_all_nodes_id()
        uncnodes_id = set()

        for nid in all_nodes_id:
            if len(set(self.get_all_hyperbranches_id_by_node_id(nid))) == 0:
                uncnodes_id.add(nid)

        return uncnodes_id

    ## Metoda generująca zbiór elementów elementów, które należą do przynajmniej jednej hipergałęzi.
    # @return Zbiór elementów elementów, które należą do przynajmniej jednej hipergałęzi.
    def get_all_connected_nodes_id(self):
        all_nodes_id = self.get_all_nodes_id()
        connodes_id = set()

        for nid in all_nodes_id:
            if len(set(self.get_all_hyperbranches_id_by_node_id(nid))) > 0:
                connodes_id.add(nid)

        return connodes_id

    ## Metoda rysująca połączenie pomiędzy wierzchołkiem a hiperkrawędzią.
    # Zajmuje ok 5% czasu CPU.
    # @param pos1 Współrzędna punktu początku połączenia w bazie współrzędnych płaszczyzny rysowania elementów.
    # @param pos2 Współrzędna punktu końca połączenia w bazie współrzędnych płaszczyzny rysowania elementów.
    # @param cro Kontekst rysowania biblioteki Cairo.
    # @param pan_vec Wektor przesunięcia punktu środka płaszczyzny rysowania elementów w stosunku do lewego górnego rogu ekranu.
    # @param center Punkt środka ekranu w bazie współrzędnych ekranu.
    # @param zoom Współczynnik powiększenia płaszczyzny rysowania elementów w stosunku do bazy współrzędnych ekranu.
    # Im większy tym większe rysowane są elementy na ekranie.
    # @param color Kolor połączenia.
    @staticmethod
    def draw_edge(v1pos_zoomed, v2pos_zoomed, cro, zoom, color=None):
        if color is None:
            color = (0.7, 0.7, 0.7)

        cro.set_source_rgb(*color)
        cro.set_line_width(1.0)

        cro.move_to(v1pos_zoomed[0], v1pos_zoomed[1])
        cro.line_to(v2pos_zoomed[0], v2pos_zoomed[1])

        cro.stroke()

    ## Metoda rysująca hipergraf na płótnie rysowania.
    # Zajmuje ok 15% czasu CPU.
    # Rysuje wszystkie połączenia, wierzchołki i hipergałęzie a także dodatkowe informacje,
    # na przykład osiągalność z ostatnio zaznaczonego wierzchołka
    # lub pogrubienie połączenia, jeśli zaznaczony element do niego należy.
    # @param cro Kontekst rysowania biblioteki Cairo.
    # @param dt Stałą czasowa, odstęp pomiędzy rysowaniem.
    # @param pan_vec Wektor przesunięcia punktu środka płaszczyzny rysowania elementów w stosunku do lewego górnego rogu ekranu.
    # Wyrażony w bazie płaszczyzny rysowania elementów (nie ekranu!)
    # @param center Punkt środka ekranu w bazie współrzędnych ekranu.
    # @param zoom Współczynnik powiększenia płaszczyzny rysowania elementów w stosunku do bazy współrzędnych ekranu.
    # Im większy tym większe rysowane są elementy na ekranie.
    def draw(self, cro, pan_vec, center, zoom):
        tstart = time.time()

        all_xnodes_id = self.get_all_xnodes_id()

        if len(all_xnodes_id) > 0:
            all_xnodes = [self.get_xnode_by_id(xid) for xid in all_xnodes_id]
            all_xnodes_pos = [x.get_position() for x in all_xnodes]

            all_xnodes_mapped_pos = Utils.map_pos_list_canvas_to_screen(all_xnodes_pos, center, zoom, pan_vec)
            all_xnodes_mapped_pos_dict = dict()

            # is_node_visible_list = [(pos_mapped < center * 2).all() and (pos_mapped > 0).all() for pos_mapped in all_xnodes_mapped_pos]
            is_node_visible_list = np.logical_and(
                np.less( all_xnodes_mapped_pos, (center * 2) ),
                np.greater( all_xnodes_mapped_pos, 0 )
            )
            is_node_visible_list = np.logical_and(is_node_visible_list[:,0], is_node_visible_list[:,1])
            is_node_visible_dict = dict()

            for i, xid in enumerate(all_xnodes_id):
                all_xnodes_mapped_pos_dict[xid] = all_xnodes_mapped_pos[i]
                is_node_visible_dict[xid]       = is_node_visible_list[i]

            all_hyperbranches_id = self.get_all_hyperbranches_id()
            # all_hbnodes = [self.get_hbnode_by_id(xid) for xid in all_hyperbranches_id]

            all_edges_nodes_id_pairs = list()
            all_edges_nodes_pos_pairs = list()
            is_edge_visible_list = list()
            is_edge_visible_dict = dict()

            for hid in all_hyperbranches_id:
                all_nodes_id_for_hbnode = self.get_all_nodes_id_by_hyperbranch_id(hid)

                for nid in all_nodes_id_for_hbnode:
                    all_edges_nodes_id_pairs.append((hid, nid))

            if len(all_edges_nodes_id_pairs) > 0:
                all_edges_nodes_pos_pairs = np.array([[all_xnodes_mapped_pos_dict[h], all_xnodes_mapped_pos_dict[n]] for h, n in all_edges_nodes_id_pairs], dtype=np.float)

                p0 = center
                p1 = all_edges_nodes_pos_pairs[:,0,:]
                p2 = all_edges_nodes_pos_pairs[:,1,:]

                # test na widocznosc linii z rownania na odleglosc punktu p0 od prostej danej parą punktów (p1, p2)
                ddl = np.abs((p2[:,1] - p1[:,1]) * p0[0] - (p2[:,0] - p1[:,0]) * p0[1] + p2[:,0] * p1[:,1] - p1[:,0] * p2[:,1])
                ddm = np.sqrt( (p2[:,1] - p1[:,1]) ** 2 + (p2[:,0] - p1[:,0]) ** 2)

                dd = ddl/ddm

                in_the_same_quarter = np.logical_and(np.equal(np.less(p1[:,0], p0[0]), np.less(p2[:,0], p0[0])), np.equal(np.less(p1[:,1], p0[1]), np.less(p2[:,1], p0[1])))

                is_edge_visible_list = np.logical_and(np.less(dd, max(*center)*1.5), np.logical_not(in_the_same_quarter))
                # print(dd)
                # print(is_edge_visible_list)

            for i, pair in enumerate(all_edges_nodes_id_pairs):
                is_edge_visible_list[i] = is_node_visible_dict[pair[0]] or is_node_visible_dict[pair[1]] or is_edge_visible_list[i]
                is_edge_visible_dict[pair] = is_edge_visible_list[i]

            num_nodes_visible = np.count_nonzero(is_node_visible_list)
            num_edges_visible = np.count_nonzero(is_edge_visible_list)
            num_drawables_visible = num_nodes_visible + num_edges_visible

            if num_drawables_visible >= 5000:
                cro.set_tolerance(1.5)
                cro.set_antialias(cairo.ANTIALIAS_GRAY) # ANTIALIAS_NONE
            elif num_drawables_visible >= 500:
                cro.set_tolerance(1.0)
                cro.set_antialias(cairo.ANTIALIAS_GRAY) # ANTIALIAS_NONE
            else:
                cro.set_tolerance(0.5)
                cro.set_antialias(cairo.ANTIALIAS_GRAY)  # ANTIALIAS_NONE

            for hid, nid in all_edges_nodes_id_pairs:
                hbpos_zoomed = all_xnodes_mapped_pos_dict[hid]
                npos_zoomed = all_xnodes_mapped_pos_dict[nid]

                # if len(all_xnodes_id) < 1536 or is_node_visible_dict[hid] or is_node_visible_dict[nid]:
                if is_edge_visible_dict[(hid, nid)]:
                # if is_edge_visible_dict[(hid, nid)]:
                    ecolor = None

                    if nid in self.activated_id_set and hid in self.activated_id_set:
                        ecolor = (0.8, 0.2, 0.0)
                    else:
                        if hid in self.selected_id_list or nid in self.selected_id_list:
                            ecolor = (0.2, 0.2, 0.2)

                    self.draw_edge(hbpos_zoomed, npos_zoomed, cro, zoom, color=ecolor)

            for ve in all_xnodes:
                pos_mapped = all_xnodes_mapped_pos_dict[ve.get_id()]

                if is_node_visible_dict[ve.get_id()]:  # if on screen
                    ve.draw(cro, pos_mapped, zoom)

            tend = time.time()
            #print("drawn   \t{0} xnodes, \t{1} edges,   \tin {2:.5f}s, \t{3:.1f} 1/s".format(num_nodes_visible, num_edges_visible, tend-tstart, 1.0/(tend-tstart)))

    # UPDATE

    ## Metoda pozwalająca na zaznaczenie elementu hipergrafu po jego id.
    # @param xid Id elementu do zaznaczenia.
    def select_xnode_by_id(self, xid):
        self.get_xnode_by_id(xid).select()  # TODOTUTAJ

        if xid not in self.selected_id_list:
            self.selected_id_list.append(xid)

    ## Metoda pozwalająca na odznaczenie elementu hipergrafu po jego id.
    # @param xid Id elementu do odznaczenia.
    def deselect_xnode_by_id(self, xid):
        # try:
        self.deactivate_all()
        self.get_xnode_by_id(xid).deselect() # TODOTUTAJ
        # except AttributeError:
        #     print("error : deselect_xnode : node {} does not exist!".format(xid), sys.stderr)

        if xid in self.selected_id_list:
            self.selected_id_list.remove(xid)

    ## Metoda pozwalająca na wyróżnienie elementu hipergrafu po jego id.
    # @param xid Id elementu do wyróżnienia.
    def activate_xnode_by_id(self, xid):
        self.get_xnode_by_id(xid).activate()
        self.activated_id_set.add(xid)

    ## Metoda pozwalająca na usunięcia wyróżnienia z elementu hipergrafu po jego id.
    # @param xid Id elementu do usunięcia wyróżnienia.
    def deactivate_xnode_by_id(self, xid):
        self.get_xnode_by_id(xid).deactivate()
        self.activated_id_set.remove(xid)

    ## Metoda usuwająca wyróżnienie ze wszystkich elementów.
    def deactivate_all(self):
        print('Deactivating set {}'.format(self.activated_id_set))
        for xid in set(self.activated_id_set):
            self.deactivate_xnode_by_id(xid)

    ## Metoda pozwalająca na zaznaczenie lub odznaczenie elementu hipergrafu po jego id.
    # @param xid Id elementu do zaznaczenia lub odznaczenia.
    def select_toggle_xnode_by_id(self, xid):
        xnode = self.get_xnode_by_id(xid)

        if xnode.is_selected():
            self.deselect_xnode_by_id(xid)
        else:
            self.select_xnode_by_id(xid)

    ## Metoda, która generuje nową pozycję elementu hipergrafu jeśli aktualna pozycja jest zajęta przez inny element.
    # Element jest przesuwany w pętli o losowy wektor. Jeśli nowowygenerowana pozycja także jest zajęta, generowane są następne, aż do skutku.
    # @param xnode Element hipergrafu, którego pozycja ma być znormalizowana.
    def normalize_xnode_position(self, xnode, rmul=1.5):
        radius = 100
        while self.get_colliding_xnode_id_by_position(xnode.get_position(), rmul=rmul) is not None:
            # print("can't place here, colliding node")
            xnode.translate_by_vec((rnd.randrange(int(radius)) - radius/2, rnd.randrange(int(radius)) - radius/2))
            radius *= 1.5

    ## Metoda odświeżająca dany wierzchołek lub hipergałąź hipergrafu.
    # @param xid Id danego wierzchołka lub hipergrafu.
    def update_xnode_by_id(self, xid):
        self.get_xnode_by_id(xid).update()

    ## Metoda odświeżająca wszystkie wierzchołki i hipergałęzie hipergrafu.
    # @param dt Czas pomiędzy kolejnymi odświeżeniami.
    def update_all_xnodes(self, dt):
        verts_id_list = self.get_all_xnodes_id()
        
        if len(verts_id_list) > 0:
            verts_list = [self.get_xnode_by_id(xid) for xid in verts_id_list]
            
            verts_f = np.array([v.force_vec for v in verts_list])
            verts_m = [v.get_mass() for v in verts_list]
            verts_v = np.array([v.get_velocity() for v in verts_list])
            verts_p = np.array([v.get_position() for v in verts_list])
            
            newa = (verts_f / np.array((verts_m, verts_m)).transpose())
            newv = verts_v + newa * dt
            newp = verts_p + newv * dt

            for i, ve in enumerate(verts_list):
                if not ve.is_selected():
                    ve.set_acceleration(newa[i])
                    ve.set_velocity(newv[i])
                    ve.set_position(newp[i])
                    ve.force_vec *= 0

            # wersja wolniejsza, niezwektoryzowana
            # for ve in verts_list:
            #    ve.update(dt)

    ## Metoda odświeżająca hipergraf.
    # @param dt Czas pomiędzy kolejnymi odświeżeniami.
    def update(self, dt):
        tstart = time.time()

        hbid_list = self.get_all_hyperbranches_id()
        xid_list = self.get_all_xnodes_id()

        # HB --- HB - złożoność liniowa w stosunku do ilości hipergałęzi.
        ## Układanie hipergałęzi w pewnej odległości od siebie.
        VertArranger.arrange_all(hgobj=self,
                                 xid_list=hbid_list,
                                 k=0,
                                 grav=-1*10**7 )

        # HB --- V
        for hbid in hbid_list:
            nids_for_hbid = list(self.get_all_nodes_id_by_hyperbranch_id(hbid))
            # hid_list = []
            nid_list = []
            for nid in nids_for_hbid:
                # hid_list.append(hbid)
                nid_list.append(nid)

                # nid_pairs_for_hbid.append((hbid, nid))

            ## Układanie par wierzchołek-hipergałąź - złożoność liniowa w stosunku do ilości wierzchołków niewolnych.
            VertArranger.arrange_pairs_list(hgobj=self,
                                            list1=[hbid]*len(nid_list),
                                            list2=nid_list,
                                            u_mul=3,
                                            k=2*10**6,
                                            grav=-2*10**6 )

            # V --- V in HB
            ## Układanie wierzchołków w pewnej odległości od siebie w danej hipergałęzi
            # Powoduje duży narzut obliczeniowy (duża złożoność).
            VertArranger.arrange_all(hgobj=self,
                                    xid_list=nids_for_hbid,
                                    u_mul=7,
                                    k=0 * 10 ** 1,
                                    grav=-1*10**6 )


        VertArranger.apply_drag_force(self, xid_list, drag=2 * 10 ** 3)
        self.update_all_xnodes(dt=dt)

        tend = time.time()
        print("updated \t{0} xnodes, \t{1} hbnodes,  \tin {2:.5f}s, \t{3:.1f} 1/s, \tOCL: {4}".format(len(xid_list), len(hbid_list),
                                                                             tend - tstart, 1.0 / (tend - tstart), OCL.ENABLE_OPENCL and OCL.is_initialized()))

    # DELETE

    ## Metoda usuwająca wierzchołek lub hipergałąź po id.
    # @param xid Id wierzchołka lub hipergałęzi.
    def delete_xnode_by_id(self, xid):
        if xid in self.X.keys():
            self.delete_node_by_id(xid)

        if xid in self.U.keys():
            self.delete_hyperbranch_by_id(xid)

    ## Metoda usuwająca wierzchołek po id.
    # @param nid Id wierzchołka.
    def delete_node_by_id(self, nid):
        self.deselect_xnode_by_id(nid)
        self.deactivate_all()
        hbids_for_nid = set(self.get_all_hyperbranches_id_by_node_id(nid))

        for hbid in hbids_for_nid:
            self.delete_hyperbranch_by_id(hbid)

        self.X.pop(nid)

    ## Metoda usuwająca hipergałąź po id.
    # @param hid Id hipergałęzi.
    def delete_hyperbranch_by_id(self, hid):
        self.deselect_xnode_by_id(hid)
        self.deactivate_all()

        nodes_id_list = self.get_all_nodes_id_by_hyperbranch_id(hid)

        self.U.pop(hid)
        self.P.pop(hid)

        for nid in nodes_id_list:
            node = self.get_node_by_id(nid)
            node.set_radius_from_degree(self.get_xnode_degree_by_xnode_id(nid))
            node.set_mass_from_degree(self.get_xnode_degree_by_xnode_id(nid))

    ## Metoda zwracająca wartość tekstową hipergrafu.
    # @return Wartość tekstowa hipergrafu zawierająca słowniki X, U, P oraz listę zaznaczonych elementów.
    def __repr__(self):
        return "\nX: {}\nU:{}\nP:{}\nsel:{}\n".format(self.X, self.U, self.P, self.selected_id_list)

    ## Metoda zwracająca hipergraf jako krotkę jego elementów.
    # @return Krotka zawierająca elementy hipergrafu.
    def dump_hg_as_tuple(self):
        return (self.X, self.U, self.P, self.selected_id_list, self.activated_id_set, self.project_properties, self.evolution_history)

    ## Metoda wypełniająca hipergraf za pomocą krotki jego elementów.
    # @param hgtuple Krotka zawierająca elementy hipergrafu.
    def load_hg_from_tuple(self, hgtuple):
        self.X = hgtuple[0]
        self.U = hgtuple[1]
        self.P = hgtuple[2]

        if len(hgtuple) > 3:
            self.selected_id_list = hgtuple[3]
            self.activated_id_set = hgtuple[4]
            self.project_properties = hgtuple[5]

        if len(hgtuple) > 6:
            self.evolution_history = hgtuple[6]

    ## Metoda zwracająca hipergraf jako słownik wybranych elementów.
    # @param elems_to_dump Lista symboli elementów, które mają być zawarte w słowniku.
    # @return Słownik zawierający elementy hipergrafu.
    def dump_hg_as_dict(self, elems_to_dump=None) -> dict:

        hgdict = dict()

        if elems_to_dump is None:
            elems_to_dump = ['X', 'U', 'P', 'S', 'A', 'T', 'H']

        if 'X' in elems_to_dump:
            hgdict['X'] = dict(self.X)

        if 'U' in elems_to_dump:
            hgdict['U'] = dict(self.U)

        if 'P' in elems_to_dump:
            hgdict['P'] = dict(self.P)

        if 'S' in elems_to_dump:
            hgdict['S'] = list(self.selected_id_list)

        if 'A' in elems_to_dump:
            hgdict['A'] = set(self.activated_id_set)

        if 'T' in elems_to_dump:
            hgdict['T'] = dict(self.project_properties)

        if 'H' in elems_to_dump:
            hgdict['H'] = list(self.evolution_history)

        return hgdict

    ## Metoda wypełniająca hipergraf za pomocą słownika wybranych elementów.
    # @param hgdict Słownik zawierający elementy hipergrafu
    def load_hg_from_dict(self, hgdict):
        if 'X' in hgdict:
            self.X = hgdict['X']

        if 'U' in hgdict:
            self.U = hgdict['U']

        if 'P' in hgdict:
            self.P = hgdict['P']

        if 'S' in hgdict:
            self.selected_id_list = hgdict['S']

        if 'A' in hgdict:
            self.activated_id_set = hgdict['A']

        if 'T' in hgdict:
            self.project_properties = hgdict['T']

        if 'H' in hgdict:
            self.evolution_history = hgdict['H']

    ## Zapisuje aktualny stan hipergrafu jako stan jego ewolucji.
    # Jeśli licznik aktualnie aktywnego stanu nie wskazuje na ostatni stan, to wszystkie
    # stany następujące po wskazywanym zostają usunięte, a następnie do powstałej w ten sposób listy
    # dopisywany jest aktualny stan.
    # @param incrementcounter Zmienna informująca, czy zwiększyć licznik zapisanych stanów ewolucji.
    def save_evolutionary_state(self, incrementcounter=True):
        frame = self.evolution_view_current_frame

        # hgstate = (self.X, self.U, self.P, self.activated_id_set)
        hgstatestr = pickle.dumps(self.dump_hg_as_dict(elems_to_dump=['A', 'X', 'U', 'P', 'S']))

        if incrementcounter:
            self.evolution_history = self.evolution_history[:frame + 1]
            self.evolution_history.append(hgstatestr)
            self.evolution_view_current_frame += 1
        else:
            self.evolution_history = self.evolution_history[:frame]
            self.evolution_history.append(hgstatestr)

        print('k: {}'.format(frame))

    ## Ładuje dany stan ewolucji hipergrafu do podglądu.
    # @param frame Zmienna informująca, który stan załadować.
    def load_evolutionary_state(self, frame):
        endframe = len(self.evolution_history) - 1

        # assert(frame >= 0 and frame <= endframe)

        if 0 <= frame <= endframe:
            hgstate = pickle.loads(self.evolution_history[frame])
            self.load_hg_from_dict(hgstate)

        print('l: {}'.format(frame))

    ## Ładuje poprzedni stan ewolucji hipergrafu do podglądu.
    def load_previous_evolutionary_state(self):
        if self.evolution_view_current_frame > 0:
            self.evolution_view_current_frame -= 1

        self.load_evolutionary_state(self.evolution_view_current_frame)

        print('p: {}'.format(self.evolution_view_current_frame))

    ## Ładuje następny stan ewolucji hipergrafu do podglądu.
    def load_next_evolutionary_state(self):
        if self.evolution_view_current_frame < len(self.evolution_history) - 1:
            self.evolution_view_current_frame += 1
            self.load_evolutionary_state(self.evolution_view_current_frame)

        else:
            print('Current evolutionary state at frame {}'.format(self.evolution_view_current_frame))

        print('n: {}'.format(self.evolution_view_current_frame))

    ## Metoda zwracająca macierz incydencji A w formie stringa.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_incydencji_u21(self, xid_list=None):

        nodes_id = None
        hbid_list = None

        if xid_list is not None:
            nodes_id = [nid for nid in xid_list if self.get_xnode_by_id(nid).is_of_vert_type(Vert.T_NODE)]
            hbid_list = [hbid for hbid in xid_list if self.get_xnode_by_id(hbid).is_of_vert_type(Vert.T_HBRANCH)]

        if nodes_id is None or len(nodes_id) == 0:
            nodes_id = self.get_all_nodes_id()

        if hbid_list is None or len(hbid_list) == 0:
            hbid_list = self.get_all_hyperbranches_id()

        # nodes_id = self.get_all_nodes_id()
        # hbid_list = self.get_all_hyperbranches_id()

        A = np.zeros([len(nodes_id), len(hbid_list)], dtype='U21')

        for x, xw in enumerate(nodes_id):
            for y, yk in enumerate(hbid_list):
                if xw in self.get_hyperbranch_by_id(yk):
                    hbnode = self.get_hbnode_by_id(yk)

                    # print('hbnode type: ' + str(hbnode.get_hyperbranch_type()))

                    if hbnode.get_hyperbranch_type() == HBNode.HB_HYPEREDGE:
                        A[x, y] = 'θ'  # kiedyś było A
                    elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERARC:
                        A[x, y] = str(self.get_hyperbranch_by_id(yk).index(xw) + 1)
                    elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERLOOP:
                        A[x, y] = 'φ'+str(len(self.get_hyperbranch_by_id(yk)))  # kiedys bylo L
                    else:
                        A[x, y] = str(self.get_hyperbranch_by_id(yk).index(xw) + 1)
                else:
                    A[x, y] = '0'

        return {
            "matrix": A,
            "lines": nodes_id,
            "columns": hbid_list
        }

    ## Metoda zwracająca macierz incydencji A w formie numerycznej.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_incydencji(self, xid_list=None):

        nodes_id = None
        hbid_list = None

        if xid_list is not None:
            nodes_id = [nid for nid in xid_list if self.get_xnode_by_id(nid).is_of_vert_type(Vert.T_NODE)]
            hbid_list = [hbid for hbid in xid_list if self.get_xnode_by_id(hbid).is_of_vert_type(Vert.T_HBRANCH)]

        if nodes_id is None or len(nodes_id) == 0:
            nodes_id = self.get_all_nodes_id()

        if hbid_list is None or len(hbid_list) == 0:
            hbid_list = self.get_all_hyperbranches_id()


        # nodes_id = self.get_all_nodes_id()
        # hbid_list = self.get_all_hyperbranches_id()

        A = np.zeros([len(nodes_id), len(hbid_list)], dtype=int)

        for x, xw in enumerate(nodes_id):
            for y, yk in enumerate(hbid_list):
                if xw in self.get_hyperbranch_by_id(yk):
                    hbnode = self.get_hbnode_by_id(yk)

                    # print('hbnode type: ' + str(hbnode.get_hyperbranch_type()))

                    if hbnode.get_hyperbranch_type() == HBNode.HB_HYPEREDGE:
                        A[x, y] = 1 # wstawiana jest 1
                    elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERARC:
                        A[x, y] = self.get_hyperbranch_by_id(yk).index(xw) + 1  # wstawiany jest indeks +1
                    elif hbnode.get_hyperbranch_type() == HBNode.HB_HYPERLOOP:
                        A[x, y] = len(self.get_hyperbranch_by_id(yk))  # wstawiana jest krotność hiperpętli
                    else:
                        A[x, y] = self.get_hyperbranch_by_id(yk).index(xw) + 1  # wstawiany jest indeks +1
                else:
                    A[x, y] = 0
                
            if len(nodes_id) > 64:
                print("matr. A: {}% done...".format(100*x/len(nodes_id)))

        return {
            "matrix": A,
            "lines": nodes_id,
            "columns": hbid_list
        }
    
    ## Metoda zwracająca binarną macierz incydencji Ab.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def bin_macierz_incydencji(self, xid_list=None):
        A_dict = self.macierz_incydencji_u21(xid_list=xid_list)
        Ab = Utils.binarize_nparray(A_dict['matrix'])

        return {
            "matrix" : Ab,
            "lines"  : A_dict["lines"],
            "columns": A_dict["columns"]
        }

    ## Metoda zwracająca macierz przyległości wierzchołków R.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_przyleglosci_wierzcholkow(self, nodes_id=None):

        if nodes_id is not None:
            nodes_id = [nid for nid in nodes_id if self.get_xnode_by_id(nid).is_of_vert_type(Vert.T_NODE)]

        if nodes_id is None or len(nodes_id) == 0:
            nodes_id = self.get_all_nodes_id()

        # nodes_id = self.get_all_nodes_id()

        R = np.zeros([len(nodes_id), len(nodes_id)], dtype=np.int)

        # jesli jest droga z x do y to +=1
        for x, xw in enumerate(nodes_id):
            for y, yw in enumerate(nodes_id):
                R[x, y] = len(self.get_connections_between_nodes_by_nodes_id(xw, yw, directed=False))
                
            if len(nodes_id) > 64:
                print("matr. R: {}% done...".format(100*x/len(nodes_id)))

        return {
            "matrix": R,
            "lines": nodes_id,
            "columns": nodes_id
        }

    ## Metoda zwracająca binarną macierz przyległości wierzchołków Rb.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def bin_macierz_przyleglosci_wierzcholkow(self, nodes_id=None):
        R_dict = self.macierz_przyleglosci_wierzcholkow(nodes_id=nodes_id)
        Rb = Utils.binarize_nparray(R_dict['matrix'])

        return {
            "matrix": Rb,
            "lines": R_dict["lines"],
            "columns": R_dict["columns"]
        }

    ## Metoda zwracająca macierz przyległości gałęzi B.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_przyleglosci_galezi(self, hyperbranches_id=None):

        if hyperbranches_id is not None:
            hyperbranches_id = [hbid for hbid in hyperbranches_id if self.get_xnode_by_id(hbid).is_of_vert_type(Vert.T_HBRANCH)]

        if hyperbranches_id is None or len(hyperbranches_id) == 0:
            hyperbranches_id = self.get_all_hyperbranches_id()


        # hyperbranches_id = self.get_all_hyperbranches_id()

        B = np.zeros([len(hyperbranches_id), len(hyperbranches_id)], dtype=np.int)

        for x, xk in enumerate(hyperbranches_id):
            for y, yk in enumerate(hyperbranches_id):
                B[x, y] = len(self.get_all_shared_nodes_id_in_hyperbranches_list((xk, yk)))
                
            if len(hyperbranches_id) > 64:
                print("matr. B: {}% done...".format(100*x/len(hyperbranches_id)))

        return {
            "matrix": B,
            "lines": hyperbranches_id,
            "columns": hyperbranches_id
        }

    ## Metoda zwracająca binarną macierz przyległości gałęzi Bb.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def bin_macierz_przyleglosci_galezi(self, hyperbranches_id=None):
        B_dict = self.macierz_przyleglosci_galezi(hyperbranches_id=hyperbranches_id)
        B = B_dict["matrix"]

        return {
            "matrix": Utils.binarize_nparray(B),
            "lines": B_dict["lines"],
            "columns": B_dict["columns"]
        }

    ## Metoda zwracająca macierz przejść P.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_przejsc(self, nodes_id=None):
        if not OCL.is_initialized():
            OCL.init_kernel()

        if nodes_id is not None:
            nodes_id = [nid for nid in nodes_id if self.get_xnode_by_id(nid).is_of_vert_type(Vert.T_NODE)]

        if nodes_id is None or len(nodes_id) == 0:
            nodes_id = self.get_all_nodes_id()
                
        

        if OCL.ENABLE_OPENCL:
            A = self.macierz_incydencji(nodes_id)
            Anp = A['matrix'].astype(np.int32)
            hbtypenp = np.array([self.get_hbnode_by_id(hid).get_hyperbranch_type() for hid in A['columns']], dtype=np.int32)
            
            kmax = np.array([Anp.shape[1]], dtype=np.int32)

            P = np.zeros((len(nodes_id), len(nodes_id))).astype(np.int32)

            OCL.run_with_ocl(
                np_in_list=[Anp, hbtypenp, kmax],  # A_nm, hbtype_m, kmax 1x1
                np_out_list=[P],  # P_nn
                shape=(len(nodes_id), len(nodes_id)),
                oclfun=OCL.prog['opencl_kernel_a_to_p']
            )
            
            # TEST NA POPRAWNOSC, TODO: ZAKOMENTOWAC POZNIEJ
            #P1 = np.zeros([len(nodes_id), len(nodes_id)], dtype=np.int)
            #for x in range(len(nodes_id)):
            #    #for y, yw in enumerate(nodes_id):
            #    y = int(x*3/4)
            #    assert(P[x, y] == len(self.get_connections_between_nodes_by_nodes_id(nodes_id[x], nodes_id[y], directed=True)))
            #    y = int(x*2/3)
            #    assert(P[x, y] == len(self.get_connections_between_nodes_by_nodes_id(nodes_id[x], nodes_id[y], directed=True)))
            #    y = int(x/2)
            #    assert(P[x, y] == len(self.get_connections_between_nodes_by_nodes_id(nodes_id[x], nodes_id[y], directed=True)))
            #    y = int(x/3)
            #    assert(P[x, y] == len(self.get_connections_between_nodes_by_nodes_id(nodes_id[x], nodes_id[y], directed=True)))
            #    y = int(x/4)
            #    assert(P[x, y] == len(self.get_connections_between_nodes_by_nodes_id(nodes_id[x], nodes_id[y], directed=True)))
            #    
            #    if len(nodes_id) > 64:
            #        print("matr. P_CL testing: {}% done...".format(100*x/len(nodes_id)))
            
        else:
            P = np.zeros([len(nodes_id), len(nodes_id)], dtype=np.int)

            for x, xw in enumerate(nodes_id):
                for y, yw in enumerate(nodes_id):
                    P[x, y] = len(self.get_connections_between_nodes_by_nodes_id(xw, yw, directed=True))  # duzy narzut obliczeniowy
                    
                if len(nodes_id) > 64:
                    print("matr. P: {}% done...".format(100*x/len(nodes_id)))
                
                


        return {
            "matrix": P,
            "lines": nodes_id,
            "columns": nodes_id
        }

    ## Metoda zwracająca binarną macierz przejść Pb.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def bin_macierz_przejsc(self, nodes_id=None):
        P_dict = self.macierz_przejsc(nodes_id=nodes_id)
        P = P_dict["matrix"]

        return {
            "matrix": Utils.binarize_nparray(P),
            "lines": P_dict["lines"],
            "columns": P_dict["columns"]
        }

    ## Metoda zwracająca macierz osiągalności D.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_osiagalnosci(self, nodes_id=None):
        Pb_dict = self.bin_macierz_przejsc(nodes_id=self.get_all_nodes_id())
        Pb = Pb_dict['matrix']

        D = Utils.suma_szeregu_geometrycznego_nparray(Pb, Pb.shape[0] * Pb.shape[1])

        Db = Utils.binarize_nparray(D)

        if nodes_id is not None:
            nodes_id = [nid for nid in nodes_id if self.get_xnode_by_id(nid).is_of_vert_type(Vert.T_NODE)]
        else:
            nodes_id = []

        if len(nodes_id) > 0:
            Db_ = np.zeros((len(nodes_id), len(nodes_id)), dtype=np.float)

            for i, x in enumerate(nodes_id):
                for j, y in enumerate(nodes_id):
                    Db_[i,j] = Db[Pb_dict['lines'].index(x), Pb_dict['columns'].index(y)]
                    
                if len(nodes_id) > 64:
                    print("matr. D: {}% done...".format(100*i/len(nodes_id)))

            Db = Db_
        else:
            nodes_id = Pb_dict['lines']

        return {
            "matrix": Utils.binarize_nparray(Db),
            "lines": nodes_id,
            "columns": nodes_id
        }

    ## Metoda zwracająca macierz spójności S.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_spojnosci(self, nodes_id=None):
        Rb_dict = self.bin_macierz_przyleglosci_wierzcholkow(nodes_id=self.get_all_nodes_id())
        Rb = Rb_dict['matrix']

        S = Utils.suma_szeregu_geometrycznego_nparray(Rb, Rb.shape[0] * Rb.shape[1])

        Sb = Utils.binarize_nparray(S)

        if nodes_id is not None:
            nodes_id = [nid for nid in nodes_id if self.get_xnode_by_id(nid).is_of_vert_type(Vert.T_NODE)]
        else:
            nodes_id = []

        if len(nodes_id) > 0:
            Sb_ = np.zeros((len(nodes_id), len(nodes_id)), dtype=np.float)

            for i, x in enumerate(nodes_id):
                for j, y in enumerate(nodes_id):
                    Sb_[i, j] = Sb[Rb_dict['lines'].index(x), Rb_dict['columns'].index(y)]
                    
                if len(nodes_id) > 64:
                    print("matr. S: {}% done...".format(100*i/len(nodes_id)))

            Sb = Sb_
        else:
            nodes_id = Rb_dict['lines']

        return {
            "matrix": Utils.binarize_nparray(Sb),
            "lines": nodes_id,
            "columns": nodes_id
        }

    ## Metoda zwracająca macierz skalarów odległości pomiędzy elementami hipergrafu.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_skalarow_odleglosci(self, xid_list=None, cl=False):
        # program glowny
        if not OCL.is_initialized():
            OCL.init_kernel()

        if xid_list is None or len(xid_list) == 0:
            xid_list = self.get_all_xnodes_id()

        if len(xid_list) > 0:
            xnodes_pos_list = [self.get_xnode_by_id(xid).get_position().tolist() for xid in xid_list]

            # zmienne numpy
            a_np = np.array(xnodes_pos_list).astype(np.float32)


            if OCL.ENABLE_OPENCL and cl:
                res_np = np.zeros((len(xnodes_pos_list), len(xnodes_pos_list))).astype(np.float32)

                OCL.run_with_ocl(
                    np_in_list=[a_np],
                    np_out_list=[res_np],
                    shape=(len(xnodes_pos_list), len(xnodes_pos_list)),
                    oclfun=OCL.prog['opencl_kernel_scalar_dist']
                )
            else:
                a = np.array([a_np])
                avec = a - a.transpose((1, 0, 2))

                sqrdists = avec[..., 0] ** 2 + avec[..., 1] ** 2
                dists = np.sqrt(sqrdists)

                # res_np = np.linalg.norm(avec, axis=2)
                res_np = dists

            return {
                "matrix": res_np,
                "lines": xid_list,
                "columns": xid_list
            }
        else:
            return {
                "matrix": [],
                "lines": [],
                "columns": []
            }

    ## Metoda zwracająca macierz wektorów odległości pomiędzy elementami hipergrafu.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_wekt_odleglosci(self, xid_list=None, cl=False):
        if not OCL.is_initialized():
            OCL.init_kernel()

        if xid_list is None or len(xid_list) == 0:
            xid_list = self.get_all_xnodes_id()

        if len(xid_list) > 0:
            xnodes_pos_list = [self.get_xnode_by_id(xid).get_position().tolist() for xid in xid_list]

            # zmienne numpy
            a_np = np.array(xnodes_pos_list).astype(np.float32)


            if OCL.ENABLE_OPENCL and cl:
                res_np = np.zeros((len(xnodes_pos_list), len(xnodes_pos_list), len(xnodes_pos_list[0]))).astype(np.float32)

                OCL.run_with_ocl(
                    np_in_list=[a_np],
                    np_out_list=[res_np],
                    shape=(len(xnodes_pos_list), len(xnodes_pos_list)),
                    oclfun=OCL.prog['opencl_kernel_vector_dist']
                )
            else:
                a = np.array([a_np])
                res_np = a - a.transpose((1, 0, 2))

            return {
                "matrix": res_np,
                "lines": xid_list,
                "columns": xid_list
            }
        else:
            return {
                "matrix": [],
                "lines": [],
                "columns": []
            }

    ## Metoda zwracająca macierz wektorów kierunku pomiędzy elementami hipergrafu.
    # @return Słownik z macierzą wraz z opisem wierszy i kolumn.
    # @jit
    def macierz_wekt_kierunkowych(self, xid_list=None, cl=False):
        if not OCL.is_initialized():
            OCL.init_kernel()

        if xid_list is None or len(xid_list) == 0:
            xid_list = self.get_all_xnodes_id()

        if len(xid_list) > 0:
            xnodes_pos_list = [self.get_xnode_by_id(xid).get_position().tolist() for xid in xid_list]

            # zmienne numpy
            xnodes_pos_array_np = np.array(xnodes_pos_list).astype(np.float32)

            if OCL.ENABLE_OPENCL and cl:
                res_np = np.zeros((len(xnodes_pos_list), len(xnodes_pos_list), len(xnodes_pos_list[0]))).astype(np.float32)

                OCL.run_with_ocl(
                    np_in_list=[xnodes_pos_array_np],
                    np_out_list=[res_np],
                    shape=(len(xnodes_pos_list), len(xnodes_pos_list)),
                    oclfun=OCL.prog['opencl_kernel_vector_dir']
                )
            else:
                a = np.array([xnodes_pos_array_np])

                av = a - a.transpose((1, 0, 2))

                sqrdists = av[..., 0] ** 2 + av[..., 1] ** 2

                # ad = np.linalg.norm(av, axis=2)
                ad = np.sqrt(sqrdists)

                adad = np.array((ad, ad)).transpose((1, 2, 0))

                adad[adad == 0] = math.sqrt(2.0)/2

                res_np = av / adad


            return {
                "matrix": res_np,
                "lines": xid_list,
                "columns": xid_list
            }
        else:
            return {
                "matrix": [],
                "lines": [],
                "columns": []
            }
            
    def documenting_dummy_fun(self):
       
        self.X = Node("", np.array((0.0,0.0)), {})
        self.U = HBNode("", HBNode.HB_DUMMY, np.array((0.0,0.0)), {})

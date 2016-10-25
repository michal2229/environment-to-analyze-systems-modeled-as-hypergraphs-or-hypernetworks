# -*- coding: utf-8 -*-

## @file HgMatrixAnalyzer.py
## @package HgMatrixAnalyzer

import numpy as np
from Utils import Utils as u

# import locale
# locale.setlocale(locale.LC_NUMERIC, 'C')

from HyperGraph import HyperGraph

import random

## Klasa HgMatrixAnalyzer.
# Klasa odpowiadająca za analizę danego hipergrafu. Jej metodami są m.in. algorytmy.
class HgMatrixAnalyzer:
    def __init__(self):
        pass

    ## Metoda generująca przykładowy wynik.
    # @param hg_obj Obiekt hipergrafu na którym wykonywany jest algorytm.
    @staticmethod
    def example_result_generator(hg_obj):

        elems_id = hg_obj.get_selected_xnodes_id()

        if not len(elems_id) > 0:
            elems_id = hg_obj.get_all_xnodes_id()

        res_as_str = ""
        #res_as_str += "(xnodes, ilość osiągalnych, z ilu osiągalny, stopien)"
        #n_out_nodes = dict()
        #n_in_nodes = dict()
        #for xid in elems_id:
        #    n_out_nodes[xid] = len(hg_obj.get_all_reachable_nodes_id_from_node_id(xid))
        #    n_in_nodes[xid] = len(hg_obj.get_all_nodes_id_where_node_id_is_reachable(xid))
        #res_as_str += "\nid\tor\tir\n"
        #res_as_str += "\n".join(["{}\t{}\t{}".format(xid, n_out_nodes[xid], n_in_nodes[xid]) for xid in sorted(hg_obj.get_all_nodes_id())])
        #res_as_str += "\n"

        res_as_str += "\nMacierz incydencji A\n" + u.matrix_result_dict_as_string(hg_obj.macierz_incydencji_u21(elems_id))

        res_as_str += "\nBinarna macierz incydencji Ab\n" + u.matrix_result_dict_as_string(hg_obj.bin_macierz_incydencji(elems_id))

        res_as_str += "\nMacierz przyleglosci wierzcholkow R\n" + u.matrix_result_dict_as_string(hg_obj.macierz_przyleglosci_wierzcholkow(elems_id))

        res_as_str += "\nBinarna macierz przyleglosci wierzcholkow Rb\n" + u.matrix_result_dict_as_string(hg_obj.bin_macierz_przyleglosci_wierzcholkow(elems_id))

        res_as_str += "\nMacierz przyleglosci galezi B\n" + u.matrix_result_dict_as_string(hg_obj.macierz_przyleglosci_galezi(elems_id))

        res_as_str += "\nBinarna macierz przyleglosci galezi Bb\n" + u.matrix_result_dict_as_string(hg_obj.bin_macierz_przyleglosci_galezi(elems_id))

        res_as_str += "\nMacierz przejsc P\n" + u.matrix_result_dict_as_string(hg_obj.macierz_przejsc(elems_id))

        res_as_str += "\nBinarna macierz przejsc Pb\n" + u.matrix_result_dict_as_string(hg_obj.bin_macierz_przejsc(elems_id))

        res_as_str += "\nMacierz osiągalności (silnej spójności) D\n" + u.matrix_result_dict_as_string(hg_obj.macierz_osiagalnosci(elems_id))

        res_as_str += "\nMacierz spójności S\n" + u.matrix_result_dict_as_string(hg_obj.macierz_spojnosci(elems_id))

        return res_as_str


    ## Metoda wykonująca algorytm Dijkstry wyszukiwania najkrótszej drogi między dwoma punktami.
    # @param hgobj Obiekt hipergrafu na którym wykonywany jest algorytm.
    # @param nid_a Id wierzchołka początkowego.
    # @param nid_b Id wierzchołka końcowego.
    @staticmethod
    def return_dijkstra_path_from_a_to_b(hgobj: HyperGraph, nid_a, nid_b=None, evo=False):
        propname = 'value'

        def opisznp(M):
            print('Macierz\n{}\ntypu {} o rozmiarze {}.'.format(M, M.dtype, M.shape))

        # Macierz incydencji A hipergrafu (linie - wierzcholki, kolumny - hipergałęzie). Ta macierz jest w formacie NUMERYCZNYM!

        A_dict = hgobj.macierz_incydencji(xid_list=None)
        A = A_dict['matrix']
        opisznp(A)

        # Macierz przejść hipergrafu.

        P_dict = hgobj.macierz_przejsc(nodes_id=None)
        P = P_dict['matrix']
        opisznp(P)

        # Wektor wag hipergałęzi (wartości parametru, np 'value').

        hbid_list = hgobj.get_all_hyperbranches_id()
        w_l = [hgobj.get_hbnode_by_id(hbid).get_property_value(propname) for hbid in hbid_list]
        W = np.array(w_l)
        opisznp(W)

        # Zmienna ilości wierzchołków.

        ilosc_wierzcholkow = P.shape[0]
        lista_id_wierzcholkow = A_dict['lines']
        lista_id_hipergalezi = A_dict['columns']

        # Tablica stanu wyszukiwania. Będzie to tablica numpy z możliwością zamaskowania elementów, aby nie wracać do odwiedzonych wierzchołków.

        s1 = np.ones(ilosc_wierzcholkow, dtype=np.float) * np.inf
        s = np.ma.array(s1, mask=False)
        np.ma.set_fill_value(s, np.inf)
        opisznp(s)

        # **Punktem startu będzie wierzchołek o indeksie 0** w macierzy. Indeks wierzchołka w macierzy nie jest jednoznaczny z id wierzchołka w hipergrafie. Da się uzyskać id wierzchołka lub hipergałęzi ze słownika wyniku metod hipergrafu. Tutaj pominięte zostały te elementy, ponieważ nie jest istotny prawdziwy id wierzchołka na poziomie obliczeń.
        # Ustawianie indeksu wierzchołka startowego. Ustawianie odległości do tego wierzchołka jako zero.

        start = lista_id_wierzcholkow.index(nid_a)
        s[start] = 0

        # Ustawianie indeksu wierzchołka końcowego (opcjonalnie, może być None). Ustawianie zmiennej wynikowej sciezki. Jeśli znaleziono ścieżkę, przyjmie wartość inną niż None.

        koniec = lista_id_wierzcholkow.index(nid_b) if nid_a != nid_b else None
        sciezka = list()

        # Ustawianie zmiennej poprzedników. Jest to słownik, którego kluczami są indeksy elementów, a w wartości pod danym kluczem można znaleźć indeksy poprzedników tych elementów.

        poprzednicy = dict()

        # Ustawianie zmiennej zawierającej indeksy nieodwiedzonych wierzchołków.

        nieodwiedzone = set(range(ilosc_wierzcholkow))

        if evo:
            hgobj.deactivate_all()

        # Algorytm Dijkstry dostosowany do hipergrafu.

        while len(nieodwiedzone) > 0:  # dla każdego wierzchołka
            aktualny_wierzcholek = s.argmin()

            if evo:
                id_akt_w = lista_id_wierzcholkow[aktualny_wierzcholek]
                hgobj.activate_xnode_by_id(id_akt_w)
                hgobj.save_evolutionary_state(True)

            if aktualny_wierzcholek == koniec:
                print('\n\tDotarcie do wierzchołka końcowego!')

                print('\tPoprzednicy: \n\t\t{}'.format(poprzednicy))

                sciezka = list()
                w = aktualny_wierzcholek
                while w in poprzednicy:
                    fr = lista_id_wierzcholkow[poprzednicy[w]['b']]
                    hb = lista_id_hipergalezi[poprzednicy[w]['h']]
                    to = lista_id_wierzcholkow[w]
                    w = poprzednicy[w]['b']

                    step = {
                        'a': fr,
                        'b': to,
                        'h': hb
                    }

                    sciezka.append(step)

                    print('\n\t Added step {}.'.format(step))

                sciezka.reverse()
                print('\tŚcieżka:\n\t\t{}'.format(sciezka))
                
                if evo:
                    hgobj.deactivate_all()
                
                break

            if s.mask[aktualny_wierzcholek]:
                break

            # print('\nRozpatrywanie wierzchołka {}.'.format(aktualny_wierzcholek))

            lista_dostepnosci = P[aktualny_wierzcholek]
            # print('\tLista dostepnosci wierzchołków z tego wierzchołka:\n\t\t{}.'.format(lista_dostepnosci))

            indeksy_dostepnych = P[aktualny_wierzcholek].nonzero()[0]
            # print('\tIndeksy dostępnych wierzchołków:\n\t\t{}.'.format(indeksy_dostepnych))


            for ind_dost in indeksy_dostepnych if koniec not in indeksy_dostepnych else [koniec]:
                # print('\n\tRozpatrywanie drogi do wierzchołka {}.'.format(ind_dost))
                # print('\t\tIlość dostępnych dróg: {}.'.format(lista_dostepnosci[ind_dost]))

                hd = np.logical_and(A[ind_dost] >= A[aktualny_wierzcholek], A[aktualny_wierzcholek] != 0)

                # print('{} >= {}\nand\n{} != 0 \n-> {}'.format(A[ind_dost], A[aktualny_wierzcholek], A[aktualny_wierzcholek], hd))
                hipergalezie_dostepne = hd.nonzero()[0]
                # print('\t\tDostępności na hipergałęziach: {}'.format(hipergalezie_dostepne))

                for ind_hg in hipergalezie_dostepne:
                    waga_hg = W[ind_hg]
                    # print('\n\t\t\tHipergałąź {} ma wagę {}.'.format(ind_hg, waga_hg))
                    if s[ind_dost] > waga_hg + s[aktualny_wierzcholek]:
                        s[ind_dost] = waga_hg + s[aktualny_wierzcholek]
                        poprzednicy[ind_dost] = {
                            'b': aktualny_wierzcholek,
                            'h': ind_hg
                        }

            # print('\n\tStan po wyjściu z wierzchołka {} to \n\t\t{}.'.format(aktualny_wierzcholek, s.data))

            s.mask[aktualny_wierzcholek] = True
            nieodwiedzone.remove(aktualny_wierzcholek)

        s.mask = np.ma.nomask

        # Pole *s.data* jest tablicą odległości obliczoną przez algorytm.
        dists = [{'nid': lista_id_wierzcholkow[ind], 'mindist': s.data[ind]} for ind in range(s.data.shape[0])]

        return sciezka, dists

    ## Metoda generująca hipergraf z danych wprowadzonych przez użytkownika.
    # @param hgobj Obiekt hipergrafu na którym wykonywany jest algorytm.
    # @param nn Ilość wierzchołków do wygenerowania.
    # @param nh Ilość hipergałęzi do wygenerowania.
    # @param evo Zmienna sterująca, czy kolejne dodania elementów do hipergrafu mają być traktowane jako kolejny krok jego ewolucji.
    @staticmethod
    def generuj_hipergraf(hgobj: HyperGraph, nn=25, nh=10, evo=False):

        generated_nodes_id_list = list()

        for i in range(nn):
            r = max(500 + 48*(i//100), 500)
            z = np.exp(-2j*np.pi*((i%100)/(100) + (i//100)/1000  + 0.25))
            rot = (z.real, z.imag)
            pos = np.array((1.0,1.0))
            coords = (pos*rot)*r
            nid = hgobj.add_node(name='', position=coords, prop_dict={}, normalize_pos=False)

            generated_nodes_id_list.append(nid)

            if evo:
                hgobj.save_evolutionary_state()

        for j in range(nh):

            if nn < 2:
                t = 2
            else:
                t = random.randint(0, 1)

            v = random.randint(1, 100)

            k = (nh/nn)

            fromj = int((1-k)*j*nn/nh)
            toj =  int((1-k)*(1+j)*nn/nh + k*nn + 0.1)

            available_list = generated_nodes_id_list[fromj:toj]

            random.shuffle(available_list)

            nodes_id_for_hbid = available_list

            hbid = hgobj.add_hyperbranch(name='', hbtype=t, nodes_id_list=nodes_id_for_hbid, prop_dict={'value' : v}, normalize_pos=True)

            if evo:
                hgobj.save_evolutionary_state(True)

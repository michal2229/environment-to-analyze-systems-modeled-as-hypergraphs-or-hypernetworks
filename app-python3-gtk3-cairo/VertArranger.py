# -*- coding: utf-8 -*-

## @file VertArranger.py
## @package VertArranger

import numpy as np
import math
import time
# import locale
# locale.setlocale(locale.LC_NUMERIC, 'C')

# import hashlib

from OCL import OCL

## Klasa VertArranger.
# Klasa wspomagająca obliczanie nowych współrzędnych wierzchołków 
# na płaszczyźnie płótna, na podstawie zależności 
# fizycznych (grawitacja, sprężystość, opór).
# Jest dość wymagająca obliczeniowo. Należy ją zoptymalizować.
class VertArranger:

    ## Zwraca siłę sprężynową.
    # @param d Rzeczywista skalarna odległość między dwoma elementami.
    # @param dir_vec Wektor jednostkowy kierunku.
    # @param u Długość sprężyny (wartość zadana).
    # @param k Stała sprężystości sprężyny.
    # @return Siła obliczona zgodna z kierunkiem.
    @staticmethod
    def get_spring_force(d, dir_vec, u, k):

        if k > 0:
            x = d - u
            F = k * x * dir_vec

            return F
        else:
            return np.array((0.0, 0.0), dtype=np.float)

    ## Zwraca siłę grawitacyjną.
    # @param m1 Masa elementu.
    # @param m2 Masa drugiego elementu.
    # @param r1 Promień elementu.
    # @param r2 Promień drugiego elementu.
    # @param d Odległość pomiędzy elementami.
    # @param dir_vec Wektor kierunku.
    # @param grav_const Stała grawitacyjna.
    # @return Siła grawitacyjna.
    @staticmethod
    def get_gravity_force(m1, m2, d, dir_vec, grav_const):
        if d < 32:
            d = 32
        return (dir_vec * grav_const * m1 * m2) / (d**2)

    ## Zwraca siłę oporu.
    # @param o Obiekt elementu, który jest rozpatrywany.
    # @param drag_coef Współczynnik oporu.
    # @return Siła oporu wprost proporcjonalna do prędkości elementu i jwspółczynnika oporu.
    @staticmethod
    def get_drag_force(o, drag_coef):
        F = o.get_velocity()*drag_coef
        return F

    ## Metoda licząca siły występujące pomiędzy parami elementów na danej liście par, oraz przypisująca je do nich.
    # @param hgobj Obiekt hipergrafu.
    # @param xnodes_id_pairs_list Lista par id elementów.
    # @param u_mul Mnożnik wartości zadanej odległości (opcjonalny).
    # @param k Stała sprężystości (opcjonalna).
    # @param grav Stała grawitacyjna (opcjonalna).
    @staticmethod
    def arrange_pairs_list(hgobj, list1, list2, u_mul=1.0, k=0.0, grav=0.0):
        tstart = time.time()

        l1_xnodes = [hgobj.get_xnode_by_id(xid) for xid in list1]
        l2_xnodes = [hgobj.get_xnode_by_id(xid) for xid in list2]

        l1_pos = [x.get_position() for x in l1_xnodes]
        l2_pos = [x.get_position() for x in l2_xnodes]

        l1_mass = [x.get_mass() for x in l1_xnodes]
        l2_mass = [x.get_mass() for x in l2_xnodes]

        l1_radius = [x.get_radius() for x in l1_xnodes]
        l2_radius = [x.get_radius() for x in l2_xnodes]

        wekt_wekt_odl_np = np.array(l2_pos) - np.array(l1_pos)
        wekt_skal_odl_np = np.sqrt(wekt_wekt_odl_np[..., 0] ** 2 + wekt_wekt_odl_np[..., 1] ** 2).transpose()

        wektor_mas1_np = np.array(l1_mass)
        wektor_mas2_np = np.array(l2_mass)

        wektor_promieni1_np = np.array(l1_radius)
        wektor_promieni2_np = np.array(l2_radius)

        dd = np.array((wekt_skal_odl_np, wekt_skal_odl_np)).transpose()
        wekt_wekt_kier_np = wekt_wekt_odl_np/dd

        wekt_masa1_razy_masa2_np = wektor_mas1_np * wektor_mas2_np

        wekt_promien1_plus_promien2_np = wektor_promieni1_np + wektor_promieni2_np

        wekt_wartosci_zadanych_odleglosci_np = (wekt_promien1_plus_promien2_np + 100) * u_mul

        macierz_skalarow_sil_sprezystosci_np = k * ( wekt_skal_odl_np -wekt_wartosci_zadanych_odleglosci_np)

        macierz_skalarow_sil_grawitacji_np = ((grav * wekt_masa1_razy_masa2_np) / ( np.maximum(wekt_skal_odl_np, 32 * np.ones(wekt_skal_odl_np.shape)) ** 2))

        Fs3d = np.array((macierz_skalarow_sil_sprezystosci_np, macierz_skalarow_sil_sprezystosci_np)).transpose()
        Fg3d = np.array((macierz_skalarow_sil_grawitacji_np, macierz_skalarow_sil_grawitacji_np)).transpose()

        Fsv = np.multiply(wekt_wekt_kier_np, Fs3d)
        Fgv = np.multiply(wekt_wekt_kier_np, Fg3d)

        Fv = Fsv + Fgv

        for i, id_pair in enumerate(zip(list1, list2)):
            o1 = hgobj.get_xnode_by_id(id_pair[0])
            o2 = hgobj.get_xnode_by_id(id_pair[1])

            if not o1.is_selected():
                o1.add_force(Fv[i])

            if not o2.is_selected():
                o2.add_force(-Fv[i])

        # for i, id_pair in enumerate(zip(list1, list2)):
        #
        #     o1 = hgobj.get_xnode_by_id(id_pair[0])
        #     o2 = hgobj.get_xnode_by_id(id_pair[1])
        #
        #     ## Wektor odległości pomiędzy dwoma elementami.
        #     D = o1.distance_vect_from(o2)
        #
        #     ## Skalar odległości pomiędzy dwoma elementami.
        #     # d = np.linalg.norm(D)
        #     d = math.sqrt(D[0] ** 2 + D[1] ** 2)
        #
        #     m1 = o1.get_mass()
        #     r1 = o1.get_radius()
        #
        #     m2 = o2.get_mass()
        #     r2 = o2.get_radius()
        #
        #     if d != 0:
        #         ## Wektor kierunku.
        #         dir_vec = D / d
        #
        #         ## Przeliczona wartość zadana odległości pomiędzy dwoma elementami.
        #         u = (r1 + r2 + 100) * u_mul
        #
        #         ## Siła sprężystości.
        #         Fs = VertArranger.get_spring_force(d, dir_vec, u, k)
        #
        #         ## Siła grawitacji.
        #         Fg = VertArranger.get_gravity_force(m1, m2, d, dir_vec, grav_const=grav)
        #
        #         if not o1.is_selected():
        #             o1.add_force(Fg)
        #             o1.add_force(Fs)
        #
        #         if not o2.is_selected():
        #             o2.add_force(-Fg)
        #             o2.add_force(-Fs)
        #     else:
        #         pass


        tend = time.time()

        # print("\t\tarranged {0} xnode pairs in {1:.5f}s, {2:.1f} 1/s".format(len(list1), tend-tstart, 1.0/(tend-tstart)))
    ## Metoda licząca siły występujące pomiędzy podzbiorami elementów na danej liście id, oraz przypisująca je do nich.
    # @param hgobj Obiekt hipergrafu.
    # @param xid_list Lista id elementów.
    # @param u_mul Mnożnik wartości zadanej odległości (opcjonalny).
    # @param k Stała sprężystości oddziaływań sprężystych pomiędzy elementami (opcjonalna).
    # @param grav Stała grawitacyjna (opcjonalna).
    # @param nclosest Ilość innych elementów do obliczenia na każdy element (pomniejszona o jeden liczność podzbioru).
    @staticmethod
    def arrange_all(hgobj, xid_list, u_mul=1.0, k=0.0, grav=0.0):
        tstart = time.time()

        if not OCL.is_initialized():
            OCL.init_kernel()

        xid_list = list(xid_list)

        if len(xid_list) >= 1:
            opencl_from_size = 24
            #opencl_computing = True
            # opencl_computing = False
            opencl_computing = len(xid_list) >= opencl_from_size

            if opencl_computing and OCL.ENABLE_OPENCL:
                # POBIERANIE DANYCH WIERZCHOLKOW DO WEKTOROW
                wektor_mas_np       = np.array([hgobj.get_xnode_by_id(xid).get_mass()              for xid in xid_list], dtype=np.float32)
                wektor_promieni_np  = np.array([hgobj.get_xnode_by_id(xid).get_radius()            for xid in xid_list], dtype=np.float32)
                xnodes_pos_array_np = np.array([hgobj.get_xnode_by_id(xid).get_position().tolist() for xid in xid_list], dtype=np.float32)
                coeffs_vec_3_x_1    = np.array([u_mul,k,grav]).astype(np.float32)

                # Fv = np.zeros((len(xid_list),len(xid_list),2), dtype=np.float32)
                # OCL.run_with_ocl(
                #     np_in_list=[xnodes_pos_array_np, wektor_mas_np, wektor_promieni_np, coeffs_vec_3_x_1],
                #     # np_out_list=[Fv, Fv_sum_for_rows],
                #     np_out_list=[Fv],
                #     shape=(Fv.shape[0], Fv.shape[1]),
                #     oclfun=OCL.prog['opencl_kernel_vector_force'],
                #     preset_outbuf=False,
                #     rw_outbuf=False
                # )
                # # OCL.run_with_ocl(
                # #     np_in_list=[Fv],
                # #     np_out_list=[Fv_sum_for_rows],
                # #     shape=Fv_sum_for_rows.shape,
                # #     oclfun=OCL.prog['opencl_kernel_mat_line_sum_to_vec']
                # # )
                # Fv_sum_for_rows = np.sum(Fv, axis=1)

                Fv_sum_for_rows = np.zeros((len(xid_list), 2), dtype=np.float32)
                OCL.run_with_ocl(
                    np_in_list=[xnodes_pos_array_np, wektor_mas_np, wektor_promieni_np, coeffs_vec_3_x_1],
                    np_out_list=[Fv_sum_for_rows],
                    # np_out_list=[Fv],
                    shape=(len(xid_list),),
                    oclfun=OCL.prog['opencl_kernel_vector_vector_force'],
                    preset_outbuf=False,
                    rw_outbuf=False
                )

                # print(Fv)
                # print(Fv_sum_for_rows)
            else:
                mac_skal_odl_dict = hgobj.macierz_skalarow_odleglosci(xid_list)
                mac_wekt_kier_dict = hgobj.macierz_wekt_kierunkowych(xid_list)
                # mac_wekt_odl_dict = hgobj.macierz_wekt_odleglosci(xid_list)

                # mac_wekt_odl_np = mac_wekt_odl_dict['matrix']
                mac_skal_odl_np  = mac_skal_odl_dict['matrix']
                mac_wekt_kier_np = mac_wekt_kier_dict['matrix']
                # mac_wekt_odl_np = mac_wekt_odl_dict['matrix']

                # POBIERANIE DANYCH WIERZCHOLKOW DO WEKTOROW
                wektor_mas_np = np.matrix([hgobj.get_xnode_by_id(xid).get_mass() for xid in xid_list])
                wektor_promieni_np = np.matrix([hgobj.get_xnode_by_id(xid).get_radius() for xid in xid_list])

                # # DEKLAROWANIE WEKTORA WYNIKOWEGO
                # wektor_sil_wynik_np = np.zeros((len(xid_list),2), dtype=np.float)

                # LICZENIE MACIERZY POMOCNICZYCH
                macierz_masa1_razy_masa2_np = wektor_mas_np.transpose() * wektor_mas_np  # | * -- -> []

                macierz_promien1_plus_promien2_np = wektor_promieni_np.transpose() + wektor_promieni_np  # | + -- -> []

                macierz_wartosci_zadanych_odleglosci_np = (macierz_promien1_plus_promien2_np + 100) * u_mul

                macierz_skalarow_sil_sprezystosci_np = k * (
                mac_skal_odl_np - macierz_wartosci_zadanych_odleglosci_np)  # * dir_vecs

                macierz_skalarow_sil_grawitacji_np = ((grav * macierz_masa1_razy_masa2_np) / (
                np.maximum(mac_skal_odl_np, 32 * np.ones(mac_skal_odl_np.shape)) ** 2))  # dir_vecs

                np.fill_diagonal(macierz_skalarow_sil_sprezystosci_np, 0.0)
                np.fill_diagonal(macierz_skalarow_sil_grawitacji_np, 0.0)

                Fs3d = np.array((macierz_skalarow_sil_sprezystosci_np, macierz_skalarow_sil_sprezystosci_np)).transpose(
                    (1, 2, 0))
                Fg3d = np.array((macierz_skalarow_sil_grawitacji_np, macierz_skalarow_sil_grawitacji_np)).transpose(
                    (1, 2, 0))

                Fsv = np.multiply(mac_wekt_kier_np, Fs3d)
                Fgv = np.multiply(mac_wekt_kier_np, Fg3d)

                Fv = Fsv + Fgv

                Fv_sum_for_rows = np.sum(Fv,axis=1)

            # print(Fv)
            # print(Fv_sum_for_rows)

            for i in range(len(xid_list)):
                o = hgobj.get_xnode_by_id(xid_list[i])
                o.add_force(Fv_sum_for_rows[i])

        tend = time.time()

        # print("\t\tarranged all {0} xnodes ({1} relations) in {2:.5f}s, {3:.1f} 1/s, OCL: {4}".format(len(xid_list), len(xid_list)*(len(xid_list)-1), tend - tstart, 1.0/(tend-tstart), OCL.ENABLE_OPENCL and OCL.is_initialized()))


    ## Metoda działająca siłą oporu zależną od prędkości na każdy element danej listy.
    # @param hgobj Obiekt hipergrafu, którego elementy są rozpatrywane.
    # @param xid_list Lista elementów do zastosowania oporu.
    # @param drag Współczynnik oporu do zastosowania.
    @staticmethod
    def apply_drag_force(hgobj, xid_list, drag):

        maxvel = 500.0

        if len(xid_list) > 0:
            node_list = [hgobj.get_xnode_by_id(xid) for xid in xid_list]
            node_vel_vec_list = np.array([n.get_velocity() for n in node_list])
            node_f_vec_list_to_add = node_vel_vec_list * (drag * -1)
            node_vel_vec_list[(node_vel_vec_list[:,0]**2 + node_vel_vec_list[:,1]**2) > maxvel**2] *= 0.5

        for i, xid in enumerate(xid_list):
            o = node_list[i]
            o.add_force(node_f_vec_list_to_add[i])

            # pozwala utrzymac stabilnosc, elementy nie rozjezdzaja sie
            # gdy jest za duza sila, ktora powoduje duza predkosc,
            # co powoduje nieprawidłowości przy zbyt dużym czasie odświeżania
            o.velocity_vec = node_vel_vec_list[i]

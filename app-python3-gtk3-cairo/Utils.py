# -*- coding: utf-8 -*-

## @file Utils.py
## @package Utils

import numpy as np

# import numba
# from numba import double
# from numba.decorators import jit
# import locale
# locale.setlocale(locale.LC_NUMERIC, 'C')


## Klasa Utils.
# Klasa zawierająca przydatne narzędzia, wspomagające pracę aplikacji.
class Utils:
    def __init__(self):
        pass

    ## Metoda mapująca punkt z przestrzeni płótna na punkt na przestrzeni ekranu.
    # Zajmuje 20%-30% czasu CPU.
    # @param posc Punkt do zmapowania.
    # @param center Punkt środka ekranu w bazie współrzędnych ekranu.
    # @param zoom Współczynnik powiększenia płaszczyzny rysowania elementów w stosunku do bazy współrzędnych ekranu.
    # Im większy tym większe rysowane są elementy na ekranie.
    # @param pan_vec Wektor przesunięcia punktu środka płaszczyzny rysowania elementów w stosunku do lewego górnego rogu ekranu.
    # Wyrażony w bazie płaszczyzny rysowania elementów (nie ekranu!)
    # @return Zmapowany punkt na przestrzeni ekranu.
    @staticmethod
    # @jit
    def map_pos_canvas_to_screen(posc, center, zoom, pan_vec):
        return (posc + pan_vec) * zoom + center

    ## Metoda mapująca listę punktów z przestrzeni płótna na listę punktów na przestrzeni ekranu.
    @staticmethod
    def map_pos_list_canvas_to_screen(posc_list, center, zoom, pan_vec):
        pl_np = np.array(posc_list)

        # mapped_c_to_s_list = [Utils.map_pos_canvas_to_screen(posc, center, zoom, pan_vec) for posc in posc_list]  # list comprehension (python) version
        mapped_c_to_s_list = (pl_np + pan_vec) * zoom + center  # numpy version

        return mapped_c_to_s_list


    ## Metoda mapująca punkt z przestrzeni ekranu na punkt na przestrzeni płótna.
    # @param poss Punkt do zmapowania.
    # @param center Punkt środka ekranu w bazie współrzędnych ekranu.
    # @param zoom Współczynnik powiększenia płaszczyzny rysowania elementów w stosunku do bazy współrzędnych ekranu.
    # Im większy tym większe rysowane są elementy na ekranie.
    # @param pan_vec Wektor przesunięcia punktu środka płaszczyzny rysowania elementów w stosunku do lewego górnego rogu ekranu.
    # Wyrażony w bazie płaszczyzny rysowania elementów (nie ekranu!)
    # @return Zmapowany punkt na przestrzeni płótna.
    @staticmethod
    # @jit
    def map_pos_screen_to_canvas(poss, center, zoom, pan_vec):
        return ((poss - center) / zoom ) - pan_vec

    ## Metoda mapująca wektor z przestrzeni płótna na przestrzeń ekranu .
    # @param vec Wektor do zmapowania.
    # @param zoom Powiększenie płótna w stosunku do płaszczyzny ekranu.
    # @return Zmapowany wektor na przestrzeni ekranu.
    @staticmethod
    # @jit
    def map_vec_canvas_to_screen(vec, zoom):
        return vec * zoom

    ## Metoda mapująca wektor z przestrzeni ekranu na przestrzeń płótna.
    # @param vec Wektor do zmapowania.
    # @param zoom Powiększenie płótna w stosunku do płaszczyzny ekranu.
    # @return Zmapowany wektor na przestrzeni płótna.
    @staticmethod
    # @jit
    def map_vec_screen_to_canvas(vec, zoom):
        return vec / zoom

    ## Metoda pomocnicza zwracająca wybraną ilość najmniejszych elementów z listy.
    # @param list_to_check Lista elementów do przeskanowania.
    # @param n Maksymalna ilość elementów do zwrócenia.
    # @return Gotowa lista n (lub mniej) najmniejszych elementów.
    @staticmethod
    def get_smallest_n_from_list(list_to_check, n):
        worklist = set(list_to_check)

        for i in range(min(n, len(list_to_check))):
            # print("worklist: {}".format(worklist))

            # vmin = min(worklist, key=lambda x: x[0])
            vmin = min(worklist)

            worklist.remove(vmin)

            yield vmin

    ## Metoda przekształcająca wynikowy słownik macierzy hipergrafu na tekst.
    # @param M_dict Słownik macierzy hipergrafu zawierający macierz, opisy wierszy i opisy kolumn macierzy.
    # @return Wynikowa postać tekstowa macierzy.
    @staticmethod
    def matrix_result_dict_as_string(M_dict):
        res_as_str = ""

        print("matr. {} stringifying...".format(M_dict["matrix"].shape))

        res_as_str += " \t" + "\t".join([str(i) for i in M_dict["columns"]])
        for i, node in enumerate(M_dict["lines"]):
            res_as_str += "\n" + str(node) + "\t"
            for j, hbranch in enumerate(M_dict["columns"]):
                res_as_str += str(M_dict["matrix"][i][j]) if M_dict["matrix"].dtype == np.dtype('U21') else str(M_dict["matrix"].astype(np.int)[i][j])
                res_as_str += "\t"
        res_as_str += "\n"

        print("matr. {} stringifying done".format(M_dict["matrix"].shape))

        return res_as_str

    ## Metoda binaryzująca macierz tekstową lub liczbową.
    # @param nparray Macierz NumPy do zbinaryzowania.
    # @return Macierz zbinaryzowana.
    @staticmethod
    # @jit
    def binarize_nparray(nparray):
        shape = nparray.shape

        print("matr. {} binarizing...".format(shape))
        
        if nparray.dtype == np.dtype('U21'):
            binarr = np.ones(shape, dtype=np.int)
            
            binarr[nparray == '']      = 0
            binarr[nparray == '0']     = 0
            binarr[nparray == '0.0']   = 0
            binarr[nparray == 'False'] = 0
            binarr[nparray == 'None']  = 0
            
            #for x in range(shape[0]):
            #    for y in range(shape[1]):
            #        strnparrxy = str(nparray[x][y])
            #        if strnparrxy == '' or strnparrxy == '0' or strnparrxy == '0.0' or strnparrxy == 'False' or strnparrxy == 'None':
            #            binarr[x][y] = 0
            #        else:
            #            binarr[x][y] = 1
            
        else:
            binarr = np.where(nparray != 0, 1, 0).astype(np.int)
        
                        
        print("matr. {} binarizing done".format(shape))

        return binarr

    ## Metoda wykonująca sumę na macierzy A: A^1 + A^2 + ....
    # @param nparray Macierz NumPy, na której pracuje metoda.
    # @param n Maksymalna wartość potęgi.
    # @return Macierz wynikowa NumPy.
    @staticmethod
    # @jit
    def suma_szeregu_geometrycznego_nparray(nparray, n):

        sumarr = np.zeros((nparray.shape[0], nparray.shape[1]), dtype=np.int)

        old_sumarr = np.zeros((nparray.shape[0], nparray.shape[1]), dtype=np.int)

        for i in range(n):
            sumarr = Utils.binarize_nparray(old_sumarr + np.linalg.matrix_power(nparray, (i+1)))

            if (sumarr == old_sumarr).all():
                print('brak zmian po {} iteracjach'.format(i+1))
                break

            old_sumarr = sumarr

        return sumarr


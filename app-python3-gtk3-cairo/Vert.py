# -*- coding: utf-8 -*-

## @file Vert.py
## @package Vert

import math

import cairo

import numpy as np

from Utils import Utils


## Klasa abstrakcyjna Vert.
#  Klasa elementu wizualizacji hipergrafu. Opisuje wizualnie zarówno wierzchołki jak i hipergałęzie.
class Vert(object):
    # VARIABLES

    ## Wartość enum oznaczająca wierzchołek.
    T_NODE = 0

    ## Wartość enum oznaczająca hipergałąź.
    T_HBRANCH = 1

    ## Wartość enum oznaczająca pusty typ – obiekt nie będzie elementem hipergrafu.
    T_DUMMY = 2

    ## Domyślne właściwości elementu hipergrafu.
    # Są one kopiowane przez każdą instancję dowolnej klasy dziedziczącej.
    default_properties = {
        "id": "",
        "name": "a",
        "value": 1.0,

        "ring_color": (1.0, 1.0, 1.0),
        "selected_ring_color": (0.0, 0.0, 0.0),
        "activated_ring_color": (1.0, 0.0, 0.0),

        "bg_color": (0.3,  0.7 ,  0.3),
        "selected_bg_color": (1.0, 0.2, 0.2),
        "activated_bg_color": (1.0, 0.7, 0.35),

        "text_color": (0.2, 0.2, 0.2),
        "selected_text_color": (0.0, 0.0, 0.0),
        "activated_text_color": (0.0, 0.0, 0.0)
    }

    ## Zmienna klasy inkrementowana przy utworzeniu nowego elementu hipergrafu.
    vert_number = 0

    # CREATE

    ## Konstruktor.
    def __init__(self, name, pos, prop_dict, vtype=T_NODE):

        ## ID aktualnego elementu (numer obiektu klasy Vert).
        self.id = Vert.vert_number
        if vtype != Vert.T_DUMMY:
            Vert.vert_number += 1

        ## Zmienna słownikowa zawierająca właściwości elementu.
        self.properties_dict = dict(Vert.default_properties)
        self.properties_dict.update({"id": self.id})
        self.properties_dict.update({"name": name})
        self.properties_dict.update(prop_dict)

        ## Zmienna enum zawierająca informację o typie elementu (wierzchołek lub hipergałąź).
        self.vert_type = vtype

        # appearance
        ## Zmienna przechowująca promień elementu.
        self.radius = 16
        self.set_radius_from_degree(0)

        ## Zmienna przechowująca masę elementu.
        self.mass = 125
        self.set_mass_from_degree(0)
        # self.color  = (1, 1, 1)

        # movement variables
        ## Wektor siły przypisany do elementu.
        self.force_vec = np.array((0.0, 0.0), dtype=np.float)

        ## Wektor przyspieszenia elementu.
        self.acceleration_vec = np.array((0.0, 0.0), dtype=np.float)

        ## Wektor prędkości elementu.
        self.velocity_vec = np.array((0.0, 0.0), dtype=np.float)

        ## Współrzędne elementu.
        self.position_vec = np.array(pos, dtype=np.float)

        ## Zmienna informująca, czy element jest zaznaczony.
        self.selected = False

        ## Zmienna informująca, czy element został wyróżniony.
        self.activated = False

        # print("{} : {}".format(self, self.properties_dict))

    # READ

    ## Metoda zwracająca id obiektu.
    # @return Id obiektu.
    def get_id(self):
        return self.id

    ## Metoda zwracająca nazwę obiektu.
    # @return Nazwa obiektu.
    def get_name(self):
        return self.get_property_value("name")

    ## Metoda ustawiająca nazwę obiektu.
    # @param name Nazwa obiektu do przypisania..
    def set_name(self, name):
        self.name = name

    ## Metoda zwracająca wartość danej właściwości.
    # @param pname Nazwa parametru do uzyskania.
    # @return Wartość uzyskanego parametru.
    def get_property_value(self, pname):
        if pname in self.properties_dict:
            return self.properties_dict[pname]
        else:
            return None

    ## Metoda zwracająca wszystkie właściwości obiektu.
    # @return Słownik właściwości obiektu.
    def get_properties_dict(self):
        return dict(self.properties_dict)

    ## Metoda ustawiająca właściwość na daną wartość.
    # @param pname Nazwa właściwości.
    # @param pval Wartość ustawiana.
    def set_property_value(self, pname, pval):
        self.properties_dict[pname] = pval

    ## Metoda aktualizująca właściwości obiektu.
    # @param prop_dict Słownik nowych wartości właściwości.
    def update_properties(self, prop_dict):
        self.properties_dict.update(prop_dict)

    ## Metoda zwracająca promień elementu hipergrafu.
    # @return Wartość liczbowa promienia elementu.
    def get_radius(self):
        return self.radius

    ## Metoda ustawiająca wartość promienia obiektu.
    # @param rad Promień obiektu.
    def set_radius(self, rad):
        self.radius = rad

    ## Metoda przeliczająca stopień elementu (w sensie wizualizacji) na promień, a następnie przypisująca do obiektu ten promien.
    # @param deg Stopień elementu.
    def set_radius_from_degree(self, deg):

        if deg == 0:
            deg = 0.25

        # self.set_radius(np.log((deg) + 1) * 10 + 10)
        self.set_radius((deg ** (1.0 / 3)) * 16)

    ## Metoda zwracająca masę obiektu.
    # @return Masa obiektu.
    def get_mass(self):
        # return max(0.1, self.get_radius()) * 25
        return self.mass

    ## Metoda zwracająca masę obiektu.
    # @return Masa obiektu.
    def set_mass(self, mass):
        # return max(0.1, self.get_radius()) * 25
        self.mass = mass

    ## Metoda ustawiająca masę elementu na podstawie jego stopnia w sensie wizualizacji.
    # @param deg Stopień elementu.
    def set_mass_from_degree(self, deg):
        if deg == 0:
            deg = 0.25

        self.mass = deg*500

    ## Metoda ustawiająca parametry fizyczne elementu na podstawie jego stopnia w sensie wizualizacji.
    # @param deg Stopień elementu.
    def set_rad_and_mass_from_degree(self, deg):
        self.set_radius_from_degree(deg)
        self.set_mass_from_degree(deg)

    ## Metoda zwracająca prędkość elementu.
    # @return Prędkość elementu  w jednostkach płótna.
    def get_velocity(self):
        return self.velocity_vec

    ## Metoda ustawiająca prędkość elementu.
    # @param vel Prędkość w jednostkach płótna.
    def set_velocity(self, vel):
        self.velocity_vec = vel

    ## Metoda zwracająca aktualne przyspieszenie elementu.
    # @return Przyspieszenie elementu.
    def get_acceleration(self):
        return self.acceleration_vec

    ## Metoda ustawiająca przyspieszenie elementu.
    # @param acc Przyspieszenie elementu.
    def set_acceleration(self, acc):
        self.acceleration_vec = acc

    ## Metoda zwracająca typ elementu (wierzchołek lub hipergałąź)
    # @return Typ elementu.
    def get_vert_type(self):
        return self.vert_type

    ## Metoda zwracająca pozycję elementu w układzie płótna.
    # @return Pozycja elementu.
    def get_position(self):
        return self.position_vec

    ## Metoda obliczająca wektor przesunięcia między tym a innym elementem.
    # @param other Drugi element do obliczenia wektora.
    # @return Wektor przesunięcia.
    def distance_vect_from(self, other):
        return np.subtract(other.get_position(), self.get_position())

    ## Metoda obliczająca skalar odległości pomiędzy tym a innym elementem.
    # @param other Drugi element do obliczenia odległości.
    # @return Skalar odległości.
    def distance_norm_from(self, other):
        # return np.linalg.norm(self.distance_vect_from(other))
        D = self.distance_vect_from(other)
        return math.sqrt(D[0]**2 + D[1]**2)

    ## Metoda licząca, czy obiekt znajduje się na danej pozycji.
    # @param pos Pozycja do sprawdzenia.
    # @param rmul Mnożnik promienia, w którym szukana jest kolizja.
    # @return True/False
    def is_colliding(self, pos, rmul=1.0):
        col_bool = (self.position_vec[0] - pos[0]) ** 2 + (self.position_vec[1] - pos[1]) ** 2 < (rmul*self.get_radius()) ** 2
        return col_bool

    ## Metoda sprawdzająca czy ten element koliduje z innym elementem.
    # @param other_vert Drugi element.
    # @return True/False
    def is_colliding_with_another(self, other_vert):
        col_bool = (self.position_vec[0] - other_vert.position[0]) ** 2 + (self.position_vec[1] - other_vert.position[
            0]) ** 2 < (self.radius + other_vert.radius) ** 2
        return col_bool

    ## Metoda zwracająca, czy dany element jest zaznaczony.
    # @return True/False
    def is_selected(self):
        return self.selected

    ## Metoda zwracająca, czy dany element jest wyróżniony.
    # @return True/False
    def is_activated(self):
        return self.activated

    ## Metoda sprawdzająca, czy ten element jest danego typu
    # @param vtype
    # @return True/False
    def is_of_vert_type(self, vtype):
        return self.get_vert_type() == vtype

    # @staticmethod
    # def draw_vector(pos0: np.array, vec: np.array, thickness, color, cro):
    #
    #     cro.set_line_width(thickness)
    #     cro.set_source_rgb(*color)
    #
    #     cro.move_to(*pos0)
    #     cro.line_to(*(pos0 + vec/10))
    #     cro.stroke()

    ## Metoda rysująca dany element
    # Zajmuje ok 10% czasu CPU.
    # @param cro Kontekst rysowania biblioteki Cairo.
    # @param pan_vec Wektor przesunięcia punktu środka płaszczyzny rysowania elementów w stosunku do lewego górnego rogu ekranu.
    # Wyrażony w bazie płaszczyzny rysowania elementów (nie ekranu!)
    # @param center Punkt środka ekranu w bazie współrzędnych ekranu.
    # @param zoom Współczynnik powiększenia płaszczyzny rysowania elementów w stosunku do bazy współrzędnych ekranu.
    # Im większy tym większe rysowane są elementy na ekranie.
    def draw(self, cro, pos_zoomed, zoom):

        # pos_zoomed = Utils.map_pos_canvas_to_screen(self.position_vec, center, zoom, pan_vec)

        radius_zoomed = self.radius * zoom
        cro.set_line_width(radius_zoomed / 10.0)

        # RING DRAWING
        if not self.is_selected():
            if self.is_activated():
                cro.set_source_rgb(*self.get_property_value('activated_ring_color'))
            else:
                cro.set_source_rgb(*self.get_property_value('ring_color'))
        else:
            cro.set_source_rgb(*self.get_property_value('selected_ring_color'))
        cro.arc(pos_zoomed[0], pos_zoomed[1], radius_zoomed, 0, 2 * math.pi)
        cro.stroke_preserve()

        # BACKGROUND DRAWING

        if not self.is_selected():
            if self.is_activated():
                cro.set_source_rgb(*self.get_property_value('activated_bg_color'))
            else:
                cro.set_source_rgb(*self.get_property_value('bg_color'))

        else:
            cro.set_source_rgb(*self.get_property_value('selected_bg_color'))

        cro.fill()

        # TEXT DRAWING
        if radius_zoomed > 10:
            if not self.is_selected():
                if self.is_activated():
                    cro.set_source_rgb(*self.get_property_value('activated_text_color'))
                else:
                    cro.set_source_rgb(*self.get_property_value('text_color'))
            else:
                cro.set_source_rgb(*self.get_property_value('selected_text_color'))

            for i, prop in enumerate(('id', 'name', 'value', 'elements')):
                if prop in self.properties_dict:
                    if not prop == 'elements' or self.is_selected():
                        propval = self.get_property_value(prop)
                        if propval is not None:
                            text = str(propval)
                            if len(text) > 0:
                                cro.select_font_face("Terminal", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                                font_size = radius_zoomed*(1.5/(1+i/2))*(0.2/len(text) + 0.3)
                                # cro.set_font_size(radius_zoomed*1.5*(0.5/len(text) + 0.2))
                                cro.set_font_size(font_size)
                                e_xbearing, e_ybearing, e_width, e_height, e_xadvance, e_yadvance = cro.text_extents(text)
                                cro.move_to(*(pos_zoomed + (-(e_width/2 + e_xbearing), (i - 0.6)*radius_zoomed/2)))
                                cro.show_text(text)
            cro.stroke()

        # VECTORS DRAWING
        # self.draw_vector(pos_zoomed, self.get_acceleration() * zoom/100, radius_zoomed / 10.0, (1, 0, 0), cro)

        # self.draw_vector(pos_zoomed, self.get_velocity() * zoom, radius_zoomed / 10.0, (0, 0, 1), cro)

    ## Metoda zwracająca wartość tekstową hipergrafu.
    # @return Wartość tekstowa elementu zwracająca id oraz nazwę, jeśli jest dostępna.
    def __repr__(self):
        if self.get_name() is None or len(self.get_name()) == 0:
            return '{}'.format(self.get_id())
        else:
            return '{}:{}'.format(self.get_id(), self.get_name())

    # UPDATE

    ## Metoda pozwalająca zaznaczyć lub odznaczyć element.
    def select_toggle(self):
        if self.is_selected():
            self.deselect()
        else:
            self.select()

    ## Metoda zaznaczająca element.
    def select(self):
        self.selected = True

    ## Metoda odznaczająca element.
    def deselect(self):
        self.selected = False

    ## Metoda wyróżniająca element.
    def activate(self):
        self.activated = True

    ## Metoda zmieniająca stan elementu z wyróżninego na normalny.
    def deactivate(self):
        self.activated = False

    ## Metoda dodająca siłę do sił elementu.
    # @param F Siła do dodania.
    def add_force(self, F):
        # self.forces_list.append(F)
        # self.force_vec[0] += F[0]
        # self.force_vec[1] += F[1]
        self.force_vec += F

    ## Metoda ustawiająca pozycję elementu.
    # @param pos Pozycja do ustawienia
    def set_position(self, pos):
        self.position_vec = pos

    ## Metoda zatrzymująca element.
    def stop_movement(self):
        self.acceleration_vec = np.array((0.0, 0.0), dtype=np.double)
        self.velocity_vec = np.array((0.0, 0.0), dtype=np.double)

    ## Metoda uaktualniająca element.
    # Liczone są tu m.in. nowe właściwości dynamiczne na podstawie sił.
    def update(self, dt):

        # if len(self.forces_list) > 0:
        #     F_sum = np.array((0.0, 0.0))
        #
        #     for f in self.forces_list:
        #         F_sum += f
        #
        #     F = F_sum/len(self.forces_list)
        # else:
        #     F = self.force_vec = np.array((0.0, 0.0))

        # self.force_vec /= 100

        # self.force_vec = F
        m = self.get_mass()

        self.set_acceleration(self.force_vec / m)

        dv = self.get_acceleration() * dt
        self.velocity_vec += dv

        ds = self.get_velocity() * dt

        if not self.is_selected():
            self.position_vec += ds

        # print('force vec: {}'.format(self.force_vec))
        self.force_vec *= 0
        # self.forces_list = []

    ## Metoda pozwalająca przeusnąc element za pomocą wektora.
    # @param vec Wektor, o który przesunięty zostanie element.
    def translate_by_vec(self, vec):
        self.position_vec += vec


## Klasa Node.
#  Klasa elementu wizualizacji hipergrafu. Opisuje wizualnie wierzchołki hipergrafu.
class Node(Vert):

    ## Właściwości domyślne wierzchołka.
    node_properties = {
    }

    ## Konstruktor.
    def __init__(self, name, pos, prop_dict):
        super(Node, self).__init__(name=name, pos=pos, vtype=Vert.T_NODE, prop_dict=prop_dict)

        self.properties_dict.update(Node.node_properties)

        # self.color = (0.5, 1.0, 0.5)


## Klasa HBNode.
#  Klasa elementu wizualizacji hipergrafu. Opisuje wizualnie hipergałęzie hipergrafu.
class HBNode(Vert):
    # VARIABLES

    ## Wartość enum oznaczająca hiperkrawędź.
    HB_HYPEREDGE = 0

    ## Wartość enum oznaczająca hiperłuk.
    HB_HYPERARC  = 1

    ## Wartość enum oznaczająca hiperpętlę.
    HB_HYPERLOOP = 2

    ## Wartość enum oznaczająca typ pusty, wierzchołek nie jest tworzony w celu dodania go do hipergrafu.
    HB_DUMMY = 3

    ## Domyślne właściwości hipergałęzi.
    hbnode_properties = {
        "elements": "None"
    }

    ## Konstruktor
    def __init__(self, name, hbtype, pos, prop_dict):
        if hbtype == HBNode.HB_DUMMY:
            super(HBNode, self).__init__(name=name, pos=pos, vtype=Vert.T_DUMMY, prop_dict=prop_dict)
        else:
            super(HBNode, self).__init__(name=name, pos=pos, vtype=Vert.T_HBRANCH, prop_dict=prop_dict)

        ## Zmienna oznaczająca typ hipergałęzi (hiperkrawędź, hiperłuk, hiperpętla).
        self.hyperbranch_type = hbtype

        if self.get_hyperbranch_type() == HBNode.HB_HYPEREDGE:
            self.set_property_value('bg_color', (0.3, 0.8, 0.9))
        elif self.get_hyperbranch_type() == HBNode.HB_HYPERARC:
            self.set_property_value('bg_color', (0.8, 0.3, 0.9))
        elif self.get_hyperbranch_type() == HBNode.HB_HYPERLOOP:
            self.set_property_value('bg_color', (0.9, 0.8, 0.3))

        self.properties_dict.update(HBNode.hbnode_properties)

        # self.color = (0.5, 0.5, 1.0)

        # print("hbtype: " + str(self.hyperbranch_type))

    ## Metoda zwracająca typ hipergałęzi.
    # @return Typ hipergałęzi.
    # Może to byc hiperkrawędź, hiperłuk lub hiperpętla.
    def get_hyperbranch_type(self):
        return self.hyperbranch_type

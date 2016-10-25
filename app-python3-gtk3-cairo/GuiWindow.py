# -*- coding: utf-8 -*-

## @file GuiWindow.py
## @package GuiWindow

import gi
import cairo
# import cairocffi as cairo
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
# gi.require_version('GObject', '3.0')
# gi.require_version('GLib', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import Gtk, Gdk, GObject, GLib, GtkSource

import pickle
from functools import wraps

import time
#import threading
#from multiprocessing import Process

import numpy as np

from Vert import Vert, HBNode
from Utils import Utils
from HyperGraph import HyperGraph
from HgMatrixAnalyzer import HgMatrixAnalyzer as Ma


## Dekorator na funkcje, które modyfikują hipergraf.
#  Pozwala obudować funkcje, aby wykonać akcje przed i po wykonaniu funkcji.
# @param method Metoda, która ma zostać obudowana.
# @return Zwraca dalej funkcję, która obudowuje daną funkcję.
def undo_redo_function_decorator(method):
    @wraps(method)
    def _impl(*method_args, **method_kwargs):
        if not isinstance(method_args[0], GuiWindow):
            raise TypeError('method_args[0] ({}) nie jest klasy GuiWindow!'.format(type(method_args[0])))
        else:
            ## Metoda przed metodą obudowaną.
            method_args[0].before_modify_action_handler()

            ## Wywołanie metody obudowanej.
            method(*method_args, **method_kwargs)

            ## Metoda po metodzie obudowanej.
            method_args[0].after_modify_action_handler()

    return _impl


## Dekorator na funkcje, po których należy odświeżyć ekran.
#  Pozwala obudować funkcje, aby wykonać akcje przed i po wykonaniu funkcji.
# @param method Metoda, która ma zostać obudowana.
# @return Zwraca dalej funkcję, która obudowuje daną funkcję.
def redraw_function_decorator(method):
    @wraps(method)
    def _impl(*method_args, **method_kwargs):
        if not isinstance(method_args[0], GuiWindow):
            raise TypeError('method_args[0] nie jest klasy GuiWindow!')
        else:
            ## Wywołanie metody obudowanej.
            method(*method_args, **method_kwargs)

            ## Metoda po metodzie obudowanej - odświeżanie ekranu.
            method_args[0].queue_draw()

            # print('Redrawed from decorator func after calling: \n\t{} \n\twith args: \n\t\t{}, \n\tkwargs: \n\t\t{}.\n\n'
            #       .format(method, method_args, method_kwargs))

    return _impl


## Klasa EntryDialog.
#  Pozwala wyświetlać pola z podpisami, w celu ich edycji. Następnie pobiera się z jej obiektu słownik z wynikowymi wartościami.
class EntryDialog(Gtk.Dialog):
    ## Konstruktor.
    def __init__(self, parent, dialog_name, labels_entries_dict):
        Gtk.Dialog.__init__(self, dialog_name, parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(320, 240)

        box = self.get_content_area()

        ## Słownik na pola wprowadzania tekstu.
        self.entries = dict()

        EntryDialog.prepare_dict_for_edit(labels_entries_dict)

        for k in sorted(labels_entries_dict.keys()):
            box.add(Gtk.Label(k))
            self.entries[k] = Gtk.Entry()
            self.entries[k].set_text(str(labels_entries_dict[k]))
            box.add(self.entries[k])

        self.show_all()

    ## Przekształca wartości elementów słownika na postać tekstową, z której będzie dało się odzyskać oryginalny typ.
    # @param dict_for_edit Słownik do przygotowania.
    @staticmethod
    def prepare_dict_for_edit(dict_for_edit):
        for k in dict_for_edit.keys():
            if isinstance(dict_for_edit[k], str):
                dict_for_edit[k] = "\'{}\'".format(dict_for_edit[k])
            else:
                dict_for_edit[k] = str(dict_for_edit[k])

    ## Metoda zwracająca słownik wyjściowy.
    # Wartości słownika zostały przekształcone z wartości tekstowej na oryginalny typ tej wartości.
    # @return Słownik wyjściowy z przywróconymi typami wartości.
    def get_result_dict(self):
        result_dict = dict()
        for k in self.entries.keys():
            try:
                result_dict[k] = eval(self.entries[k].get_text())
            except:
                result_dict[k] = self.entries[k]

        return result_dict


## Klasa TreeViewResultDialog
#  Pozwala na wyświetlanie wyników w formie listy wierszy.
class TreeViewResultDialog(Gtk.Dialog):
    ## Konstruktor.
    def __init__(self, parent, dialog_name="Result", result_matrix_dict=None):
        Gtk.Dialog.__init__(self, dialog_name, parent, 0,
                            (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(320, 400)

        if result_matrix_dict is not None and len(result_matrix_dict['matrix']) > 0:

            lines_titles = [str(parent.active_hg.get_xnode_by_id(xid)) for xid in result_matrix_dict['lines']]
            columns_titles = [str(parent.active_hg.get_xnode_by_id(xid)) for xid in result_matrix_dict['columns']]

            box = self.get_content_area()

            matrix_liststore = Gtk.ListStore(str, *([str] * len(columns_titles)))

            for i, mat_row in enumerate(result_matrix_dict['matrix'].tolist()):
                list_of_str_mat_row = [str(el) for el in mat_row]
                matrix_liststore.append([str(lines_titles[i])] + list_of_str_mat_row)

            language_filter = matrix_liststore.filter_new()

            # creating the treeview, making it use the filter as a model, and adding the columns
            treeview = Gtk.TreeView.new_with_model(language_filter)
            treeview.set_grid_lines(3)

            for i, column_title in enumerate(['~'] + columns_titles):
                renderer = Gtk.CellRendererText()

                column = Gtk.TreeViewColumn(column_title, renderer, text=i)

                # TODO: nie działa sortowanie
                # column.set_sort_column_id(i)
                # self.matrix_liststore.set_sort_func(i, TreeViewResultDialog.compare, None)

                treeview.append_column(column)

            scrollable_treelist = Gtk.ScrolledWindow()
            scrollable_treelist.set_vexpand(True)
            scrollable_treelist.set_hexpand(True)
            scrollable_treelist.add(treeview)

            box.pack_start(scrollable_treelist, True, True, 0)
            box.set_vexpand(True)
            box.set_hexpand(True)

            self.show_all()

    # @staticmethod
    # def compare(model, row1, row2, user_data):
    #     sort_column, _ = model.get_sort_column_id()
    #     value1 = model.get_value(row1, sort_column)
    #     value2 = model.get_value(row2, sort_column)
    #     if value1 < value2:
    #         return -1
    #     elif value1 == value2:
    #         return 0
    #     else:
    #         return 1


## Klasa TextResultDialog
#  Pozwala na wyświetlanie wyników w formie tekstu.
class TextResultDialog(Gtk.Dialog):
    ## Konstruktor.
    def __init__(self, parent, dialog_name="Result", result_text="result text"):
        Gtk.Dialog.__init__(self, dialog_name, parent, 0,
                            (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(480, 640)

        box = self.get_content_area()

        scrolledwindow = Gtk.ScrolledWindow()

        textarea = Gtk.TextView()

        scrolledwindow.add(textarea)

        textbuffer = Gtk.TextBuffer()
        textbuffer.set_text(result_text)
        textarea.set_buffer(textbuffer)

        textarea.set_editable(False)

        box.pack_start(scrolledwindow, True, True, 0)

        self.show_all()


## Klasa edytora skryptów.
#  Pozwala na napisanie, wczytanie, zapisanie, uruchomienie skryptu w celu analizy hipergrafu.
#  Składa się z pola edytora kodu oraz pola wyników.
class EditorDialog(Gtk.Dialog):
    last_code_string = 'hgprint(\'Hello World\')\nhgprint(hg)'
    last_output_string = """Wynik pojawi się tutaj.

Dostępne zmienne
\thg - obiekt hipergrafu
\twin - obiekt okna aplikacji
\tUtils - klasa narzędzi pomocniczych
\tMa - klasa zawierająca algorytmy
\tOCL - klasa narzędzi OpenCL

Do wyświetlania tekstu służy funkcja hgprint()

Należy zwrócić szczególną uwagę, że do zmiennej \'hg\'
przypisywana jest wartość z \'win.active_hg\'
co oznacza, że w wyniku wykonywania komend
cofnięcia, powtórzenia, zapisania
lub wczytania stanu ewolucji hipergrafu
wartość w zmiennej \'hg\' może odbiegać
od tej w \'win.active_hg\'.
Należy ją wtedy przypisać ponownie
lub w całym skrypcie korzystać
jedynie z \'win.active_hg\'."""

    ## Konstruktor.
    def __init__(self, parent, dialog_name="Edytor"):
        Gtk.Dialog.__init__(self, dialog_name, parent, 0, ())


        ## Obiekt klasy, która wywołała okno edytora.
        self.parent = parent

        self.set_default_size(960, 640)

        box = self.get_content_area()

        grid1 = Gtk.Grid()
        grid1.set_column_spacing(12)

        code_scrolled_window = Gtk.ScrolledWindow()
        # code_textview = Gtk.TextView()
        code_textview = GtkSource.View()
        code_textview.set_hexpand(True)
        code_textview.set_vexpand(True)
        code_scrolled_window.add(code_textview)
        lang_manager = GtkSource.LanguageManager()
        code_textview.set_editable(True)

        grid1.attach(code_scrolled_window, 0, 0, 1, 1)

        grid2 = Gtk.Grid()
        grid2.set_column_spacing(12)

        ## Bufor zawierający tekst pola tekstowego kodu.
        self.code_textbuffer = code_textview.get_buffer()
        self.code_textbuffer.set_text(EditorDialog.last_code_string)
        self.code_textbuffer.set_language(lang_manager.get_language('python'))

        result_window = Gtk.ScrolledWindow()
        result_textvieew = Gtk.TextView()
        result_textvieew.set_hexpand(True)
        result_textvieew.set_vexpand(True)
        result_window.add(result_textvieew)
        result_textvieew.set_editable(False)

        grid2.attach(result_window, 0, 0, 1, 1)

        ## Bufor zawierający tekst pola tekstowego wyniku.
        self.result_textbuffer = result_textvieew.get_buffer()

        vpaned = Gtk.HPaned()
        box.add(vpaned)
        vpaned.pack1(grid1, True, True)
        vpaned.pack2(grid2, True, True)
        vpaned.show()


        # box.add(grid1)
        # box.add(grid2)

        button_code_load = Gtk.Button(label='wczytaj')
        button_code_load.connect("clicked", self.load_code)
        grid1.attach_next_to(button_code_load, code_scrolled_window, Gtk.PositionType.BOTTOM, 1, 1)

        button_code_save = Gtk.Button(label='zapisz')
        button_code_save.connect("clicked", self.save_code)
        grid1.attach_next_to(button_code_save, button_code_load, Gtk.PositionType.BOTTOM, 1, 1)

        button_code_run = Gtk.Button(label='wykonaj')
        button_code_run.connect("clicked", lambda butt: EditorDialog.execcode(self.parent, self, butt)) # NameError: free variable 'parent' referenced before assignment in enclosing scope
        grid2.attach_next_to(button_code_run, result_window, Gtk.PositionType.BOTTOM, 1, 1)

        buttbgcol = Gdk.RGBA()
        buttbgcol.parse('#ffe090')
        buttbgcol.to_string()
        button_code_run.override_background_color(Gtk.StateFlags.NORMAL, buttbgcol)

        button_clear = Gtk.Button(label='wyczyść')
        button_clear.connect("clicked", lambda butt: self.result_textbuffer.set_text(''))
        grid2.attach_next_to(button_clear, button_code_run, Gtk.PositionType.BOTTOM, 1, 1)

        self.hgprint(EditorDialog.last_output_string)

        self.show_all()

    ## Metoda pozwalająca zapisać kod z edytora do pliku.
    def save_code(self, butt=None):
        dialog = Gtk.FileChooserDialog("Wybierz plik do zapisu", self, Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

        filter_py = Gtk.FileFilter()
        filter_py.set_name("Pliki hgs")
        filter_py.add_pattern("*.hgs")
        dialog.add_filter(filter_py)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("File selected: " + dialog.get_filename())
            path = dialog.get_filename()
            if not path.endswith(".hgs"):
                path += ".hgs"

            with open(path, 'w') as f:
                start, end = self.code_textbuffer.get_bounds()
                f.write(self.code_textbuffer.get_text(start, end, True))

            EditorDialog.last_code_string = self.code_textbuffer.get_text(*self.code_textbuffer.get_bounds(), True)

        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    ## Metoda pozwalająca odczytać kod z pliku i wczytać go do okna edytora.
    def load_code(self, butt=None):
        dialog = Gtk.FileChooserDialog("Wybierz plik projektu do wczytania", self, Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK) )

        filter_py = Gtk.FileFilter()
        filter_py.set_name("Pliki hgs")
        filter_py.add_pattern("*.hgs")
        dialog.add_filter(filter_py)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("Open clicked")
            print("File selected: " + dialog.get_filename())

            path = dialog.get_filename()

            with open(path, 'r') as f:
                read_data = f.read()
                self.code_textbuffer.set_text(read_data)

            EditorDialog.last_code_string = self.code_textbuffer.get_text(*self.code_textbuffer.get_bounds(), True)

        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    ## Metoda pozwalająca na wyświetlanie tekstu w polu wynikowym edytora.
    def hgprint(self, inputstr):
        self.result_textbuffer.insert_at_cursor(text=str(inputstr))
        self.result_textbuffer.insert_at_cursor(text='\n')

    ## Metoda uruchamiająca napisany przez użytkownika kod.
    @staticmethod
    @undo_redo_function_decorator
    def execcode(win, editor, button=None):

        editor.result_textbuffer.set_text('')

        from OCL import OCL

        hgprint = editor.hgprint
        win = editor.parent
        hg = win.active_hg

        try:
            EditorDialog.last_code_string = editor.code_textbuffer.get_text(*editor.code_textbuffer.get_bounds(), True)
            scope = dict(globals())
            scope.update(locals())
            exec(EditorDialog.last_code_string, scope)
            EditorDialog.last_output_string = editor.result_textbuffer.get_text(*editor.result_textbuffer.get_bounds(), True)
        except Exception as e:
            editor.hgprint(e)
            EditorDialog.last_output_string = editor.result_textbuffer.get_text(*editor.result_textbuffer.get_bounds(), True)


## Klasa GuiWindow.
#  Główna klasa aplikacji, tworzy okno edycji hipergrafu.
class GuiWindow(Gtk.Window):
    ## Konstruktor klasy okna głównego.
    def __init__(self):
        super(GuiWindow, self).__init__()

        # SETUP
        self.set_icon_from_file('icon.png')
        # print("\n".join(dir(Gtk)))

        # WINDOW VARIABLES
        ## Zmienna przechowująca aktualną wielkość okna rysowania jako tablica NumPy.
        # Jest wyrażony w układzie współrzędnych ekranu.
        self.DRAWING_AREA_SIZE = np.array((1366.0, 768.0))

        ## Zmienna przechowująca aktualny punkt środka okna rysowania jako tablica NumPy.
        # Jest wyrażony w układzie współrzędnych ekranu.
        self.DRAWING_AREA_CENTER = self.DRAWING_AREA_SIZE / 2.0  # punkt na ekranie.

        ## Zmienna ustalająca tryb testowania.
        self.DEBUG_MODE = True

        ## Współczynnik powiększenia płaszczyzny rysowania elementów w stosunku do bazy współrzędnych ekranu.
        # Im większy tym większe rysowane są elementy na ekranie.
        self.ZOOM = 0.25

        ## Minimalna wartość powiększenia płótna.
        self.MINZOOM = 1.0 / 40.0

        ## Maksymalna wartość powiększenia płótna.
        self.MAXZOOM = 4.0

        ## Wektor przesunięcia punktu środka płaszczyzny rysowania elementów w stosunku do lewego górnego rogu ekranu.
        # Wyrażony w bazie płaszczyzny rysowania elementów (nie ekranu!)
        self.CANVAS_PAN_VECTOR = np.array((0, 0),
                                          dtype=np.double)  # kierunek zgodny z kierunkiem ruchu myszy, natywny dla plotna

        ## Zmienna ustalająca czy hipergraf ma być animowany.
        self.ANIMATE = False

        ## Stała czasowa, która wyraża ilość czasu jaki musi minąć pomiędzy dwoma kolejnymi odświeżeniami widoku.
        self.TIME_DELTA_SEC = 1.0 / 240.0

        ## Zmienna przechowująca poprzednią pozycję myszy przy kliknięciu.
        self.old_mouse_pos = np.array((0, 0), dtype=np.double)  # punkt na ekranie

        ## Zmienna przechowująca ostatnio używany przycisk myszy.
        self.old_mouse_button = None

        ## Zmienna czasu startu aplikacji
        self.START_TIME_SEC = time.time()

        # PROJECT VARIABLES
        ## Obiekt aktualnie używanego hipergrafu.
        self.active_hg =  HyperGraph()

        ## Lista dodatkowych elementów zdefiniowanych przez użytkownika, które mają być wyświetlone na płótnie.
        self.custom_drawables = None

        ## Lista dodatkowych elementów zdefiniowanych przez użytkownika, które mają reagować na kliknięcia.
        self.custom_clickables = None

        ## Zmienna przechowująca poprzednie stany hipergrafu, aby móc przywrócić stan przy cofnięciu akcji.
        self.undo_states = list()

        ## Zmienna przechowująca stany chronologicznie nowsze, niż aktualnie cofnięty.
        self.redo_states = list()
        self.after_modify_action_handler()

        # DEFINING WINDOW
        self.set_title("Środowisko do analizy systemów modelowanych jako hipergrafy lub hipersieci")
        self.resize(*self.DRAWING_AREA_SIZE)
        self.set_position(Gtk.WindowPosition.CENTER)

        # CREATING WINDOW LAYOUT
        ## Główna siatka elementów, nadaje ona kształt panelu przycisków i oknu wyświetlania.
        main_elements_grid = Gtk.Grid()
        self.add(main_elements_grid)

        # TITLEBAR AND TOOLBAR
        ag, tb = self.init_toolbar()
        self.add_accel_group(ag)
        main_elements_grid.attach(tb, 0, 0, 2, 1)

        # ICON PANEL
        bp = self.init_button_panel()
        main_elements_grid.attach_next_to(bp, tb, Gtk.PositionType.BOTTOM, 1, 1)

        # FRAME FOR DRAWING AREA
        df = self.init_drawing_frame()
        main_elements_grid.attach_next_to(df, bp, Gtk.PositionType.RIGHT, 1, 1)

        self.esa, es = self.init_evo_scale()
        main_elements_grid.attach_next_to(es, df, Gtk.PositionType.BOTTOM, 1, 1)

        # DRAWING AREA FOR CAIRO
        da = self.init_drawing_area()

        df.add(da)

        # DRAWING SURFACE FOR CAIRO
        ds = self.init_drawing_surface(df, da)

        # CAIRO SETUP
        cr = self.init_cairo_on_drawing_surface(ds)


        # EVENTS SETUP
        self.init_events_callbacks()

    ## Metoda inicjująca pasek narzędzi.
    # @returns Obiekt paska narzędzi.
    def init_toolbar(self):
        ## Zmienna przechowująca ustaloną kompozycję paska narzędziowego.
        # Jest ona zmienną tekstową w formacie XML.
        UI_INFO = """
                <ui>
                  <toolbar name='ToolBar'>
                    <toolitem action='SaveHg' />
                    <toolitem action='LoadHg' />
                    <toolitem action='UndoAction' />
                    <toolitem action='RedoAction' />
                    <toolitem action='SelectAllToggle' />
                    <toolitem action='DeactivateAll' />
                    <toolitem action='NewNode' />
                    <toolitem action='NewHyperedge' />
                    <toolitem action='NewHyperarc' />
                    <toolitem action='NewHyperloop' />
                    <toolitem action='AnimateToggle' />
                    <toolitem action='EditSelected' />
                    <toolitem action='DeleteSelected' />
                    <toolitem action='SaveEvoState' />
                    <toolitem action='ResetView' />
                    <toolitem action='ResetHG' />
                    <toolitem action='AddPropToNodes' />
                    <toolitem action='AddPropToHbranches' />
                    <toolitem action='AddPropToXNodes' />
                  </toolbar>
                </ui>
            """

        ## Grupa akcji, potrzebna do działania paska narzędziowego
        action_group = Gtk.ActionGroup("my_actions")

        action_list = [
            ("LoadHg", Gtk.STOCK_OPEN, "wczytaj", None, None, self.load_hypergraph_from_file),
            ["SaveHg", Gtk.STOCK_SAVE, "zapisz", None, None, self.save_hypergraph_to_file],
            ("UndoAction", Gtk.STOCK_UNDO, "cofnij", None, None, self.undo_action),
            ("RedoAction", Gtk.STOCK_REDO, "powtórz", None, None, self.redo_action),
            ("AnimateToggle", Gtk.STOCK_MEDIA_PLAY, "animuj", None, None, self.toggle_animate),
            ("SelectAllToggle", Gtk.STOCK_SELECT_ALL, "zaznacz", None, None, self.toggle_select_all),
            ("DeactivateAll", Gtk.STOCK_SELECT_ALL, "deaktywuj", None, None, self.deactivate_all),
            ("NewNode", Gtk.STOCK_ADD, "wierzchołek", None, None, self.make_node),
            ("NewHyperedge", Gtk.STOCK_ADD, "hiperkrawędź", None, None, self.make_hyperedge),
            ("NewHyperarc", Gtk.STOCK_ADD, "hiperłuk", None, None, self.make_hyperarc),
            ("NewHyperloop", Gtk.STOCK_ADD, "hiperpętla", None, None, self.make_hyperloop),
            ("EditSelected", Gtk.STOCK_EDIT, "edytuj", None, None, self.edit_all_selected_xnodes),
            ("DeleteSelected", Gtk.STOCK_DELETE, "usuń", None, None, self.delete_selected_xnode),
            ("SaveEvoState", Gtk.STOCK_ADD, "krok ewol.", None, None, lambda x: self.active_hg.save_evolutionary_state(True)),
            ("ResetView", Gtk.STOCK_CLEAR, "reset widoku", None, None, self.reset_view_pan_and_scale),
            ("ResetHG", Gtk.STOCK_CLEAR, "reset hg", None, None, self.reset_hypergraph),
            ("AddPropToNodes", Gtk.STOCK_ADD, "właśc. do wierz.", None, None, self.add_property_to_nodes),
            ("AddPropToHbranches", Gtk.STOCK_ADD, "właśc. do hipergał.", None, None, self.add_property_to_hbnodes),
            ("AddPropToXNodes", Gtk.STOCK_ADD, "właśc. do wszystkich", None, None, self.add_property_to_xnodes)
        ]

        action_group.add_actions(action_list)

        ## Manager Interfejsu Użytkownika
        uimanager = Gtk.UIManager()
        uimanager.add_ui_from_string(UI_INFO)
        accelgroup = uimanager.get_accel_group()

        uimanager.insert_action_group(action_group)
        toolbar = uimanager.get_widget("/ToolBar")
        toolbar.set_style(Gtk.ToolbarStyle.BOTH)
        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        toolbar.set_icon_size(
            Gtk.IconSize.SMALL_TOOLBAR)  # Gtk.IconSize.INVALID, Gtk.IconSize.MENU, Gtk.IconSize.SMALL_TOOLBAR, Gtk.IconSize.LARGE_TOOLBAR, Gtk.IconSize.BUTTON, Gtk.IconSize.DND, Gtk.IconSize.DIALOG

        return accelgroup, toolbar

    ## Metoda inicjująca pasek przycisków.
    # @returns Obiekt paska przycisków.
    def init_button_panel(self):

        ## Funkcja wspomagająca wypisywanie wyniku macierzy w formie tekstu w nowym oknie.
        # @param name Tytuł nowego okna.
        # @param fun Funkcja do wykonania, której wynikiem będzie macierz.
        def wyn_mac(name, fun):
            # strout = "\n{}\n{}".format(name, Utils.matrix_result_dict_as_string(fun(self.active_hg.get_selected_xnodes_id())))
            # dialog = TextResultDialog(self, dialog_name=name, result_text=strout)
            mat_wyn = fun(self.active_hg.get_selected_xnodes_id())

            if len(mat_wyn['matrix']) > 0:
                dialog = TreeViewResultDialog(self, dialog_name=name, result_matrix_dict=mat_wyn)
                dialog.run()
                dialog.destroy()

        ## Funkcja wspomagająca wypisywanie wyniku obliczania drogi pomiędzy wierzchołkami.
        # @param name Tytuł nowego okna.
        # @param fun Funkcja do wykonania, której wynikiem będzie ścieżka.
        def alg_droga(name, fun):
            xsel = self.active_hg.get_selected_xnodes_id()
            xsel = [xid for xid in xsel if self.active_hg.get_xnode_by_id(xid).is_of_vert_type(Vert.T_NODE)]

            if len(xsel) >= 1:
                start_nid = xsel[0]
                end_nid = xsel[-1]

                self.toggle_select_all()
                self.active_hg.deactivate_all()

                paths, dists = fun(self.active_hg, start_nid, end_nid)

                self.active_hg.deactivate_all()

                strout = name + "\n\n"

                if paths is not None and len(paths) > 0:
                    for p in paths:
                        self.active_hg.activate_xnode_by_id(p['a']),
                        self.active_hg.activate_xnode_by_id(p['h']),
                        self.active_hg.activate_xnode_by_id(p['b'])

                    strout += 'Najkrotsza droga z {} do {} to: \n{}.\n\n'.format(
                        self.active_hg.get_xnode_by_id(start_nid),
                        self.active_hg.get_xnode_by_id(end_nid),
                        ",\n".join(["    {}->({})->{}".format(
                            self.active_hg.get_xnode_by_id(ii['a']),
                            self.active_hg.get_xnode_by_id(ii['h']),
                            self.active_hg.get_xnode_by_id(ii['b'])
                        ) for ii in paths]))
                else:
                    if dists is None and start_nid != end_nid:
                        strout += '\nDroga z {} do {} nie istnieje!\n'.format(start_nid, end_nid)

                    if dists is not None:
                        strout +='Odległości z {} do wierzchołków:\n'.format(self.active_hg.get_xnode_by_id(start_nid))
                        for d in [x for x in dists if (x['mindist'] != np.nan and x['mindist'] > 0)]:
                            strout += '  {}: {}\n'.format(self.active_hg.get_xnode_by_id(d['nid']), d['mindist'])

                dialog = TextResultDialog(self, dialog_name=name, result_text=strout)
                dialog.run()
                dialog.destroy()

        ## Funkcja wspomagająca wpisywanie danych użytkownika do wygenerowania nowego hipergrafu.
        # @param winobj Obiekt okna.
        # @param name Tytuł nowego okna.
        # @param fun Funkcja do wykonania, która wygeneruje hipergraf.
        @undo_redo_function_decorator
        def gen_hg(winobj, name, fun):
            param_dict = dict()

            nn = 100
            nh = 25
            evo = False

            param_dict['Liczba wierzchołków'] = nn
            param_dict['Liczba hipergałęzi'] = nh
            param_dict['Ewolucja'] = evo

            dialog = EntryDialog(self, dialog_name="Generuj Hipergraf", labels_entries_dict=param_dict)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                return_dict = dialog.get_result_dict()

                nn = return_dict['Liczba wierzchołków']
                nh = return_dict['Liczba hipergałęzi']
                evo = return_dict['Ewolucja']

                fun(winobj.active_hg, nn, nh, evo)

            dialog.destroy()

        ## Funkcja wspomagająca uruchomienie i zniszczenie okna edytora.
        def show_editor():
            dialog = EditorDialog(parent=self)
            dialog.run()
            dialog.destroy()

        ## Zmienna typu lista na informacje o przyciskach, z niej generowane są przyciski na lewym panelu.
        buttons_info = [
            {
                'id': 'genhg1',
                'text': 'generuj hipergraf',
                'bg': '#fff0f0',
                'cb': lambda x: gen_hg(self, 'Generuj hg', Ma.generuj_hipergraf)
            },
            {
                'id': 'edytor',
                'text': 'edytor skryptów',
                'bg': '#fff0f0',
                'cb': lambda butt: show_editor()
            },
            {
                'id': 'getmat',
                'text': 'wszystkie macierze',
                'bg': None,
                'cb': self.show_matricies
            },
            {
                'id': 'getmatincs',
                'text': 'macierz A tekstowa',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz incydencji A', self.active_hg.macierz_incydencji_u21)
            },
            {
                'id': 'getmatincn',
                'text': 'macierz A numeryczna',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz incydencji A', self.active_hg.macierz_incydencji)
            },
            {
                'id': 'getmatincb',
                'text': 'macierz A binarna',
                'bg': None,
                'cb': lambda x: wyn_mac('Binarna macierz incydencji Ab', self.active_hg.bin_macierz_incydencji)
            },
            {
                'id': 'getmatprzylw',
                'text': 'macierz R',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz przyleglosci wierzcholkow R',
                                        self.active_hg.macierz_przyleglosci_wierzcholkow)
            },
            {
                'id': 'getmatprzylwb',
                'text': 'macierz R binarna',
                'bg': None,
                'cb': lambda x: wyn_mac('Binarna macierz przyleglosci wierzcholkow Rb',
                                        self.active_hg.bin_macierz_przyleglosci_wierzcholkow)
            },
            {
                'id': 'getmatprzylg',
                'text': 'macierz B',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz przyleglosci galezi B', self.active_hg.macierz_przyleglosci_galezi)
            },
            {
                'id': 'getmatprzylgb',
                'text': 'macierz B binarna',
                'bg': None,
                'cb': lambda x: wyn_mac('Binarna macierz przyleglosci galezi Bb',
                                        self.active_hg.bin_macierz_przyleglosci_galezi)
            },
            {
                'id': 'getmatprzejsc',
                'text': 'macierz P',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz przejsc P', self.active_hg.macierz_przejsc)
            },
            {
                'id': 'getmatprzejscb',
                'text': 'macierz P binarna',
                'bg': None,
                'cb': lambda x: wyn_mac('Binarna macierz przejsc Pb', self.active_hg.bin_macierz_przejsc)
            },
            {
                'id': 'getmatosiag',
                'text': 'macierz D',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz osiągalności (silnej spójności) D',
                                        self.active_hg.macierz_osiagalnosci)
            },
            {
                'id': 'getmatspoj',
                'text': 'macierz S',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz spójności S', self.active_hg.macierz_spojnosci)
            },
            {
                'id': 'getmatskalodl',
                'text': 'macierz skal. odległości',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz skalarów odległości', self.active_hg.macierz_skalarow_odleglosci)
            },
            {
                'id': 'getmatwektodl',
                'text': 'macierz wekt. odległości',
                'bg': None,
                'cb': lambda x: wyn_mac('Macierz wektorow odległości', self.active_hg.macierz_wekt_odleglosci)
            },
            # {
            #     'id': 'getshortpath',
            #     'text': 'najkrotsza droga',
            #     'bg': '#f0fff0',
            #     'cb': lambda x: alg_droga('Najkrótsza droga z A do B', Ma.return_paths_from_a_to_b_from_shortest)
            # },
            {
                'id': 'getshortpathdij',
                'text': 'alg. Dijsktry',
                'bg': '#f0fff0',
                'cb': lambda x: alg_droga('Najkrótsza droga z A do B wg Dijkstry', Ma.return_dijkstra_path_from_a_to_b)
            },
        ]

        ## Poboczna siatka na przyciski.
        buttongrid = Gtk.Grid()

        ## Słownik na obiekty przycisków.
        # Jest przydatny do konfiguracji przycisków w pętli.
        buttons = {}
        for i, but_inf in enumerate(buttons_info):
            button = Gtk.Button(label=but_inf['text'])

            if but_inf['bg'] is not None:
                buttbgcol = Gdk.RGBA()
                buttbgcol.parse(but_inf['bg'])
                buttbgcol.to_string()
                button.override_background_color(Gtk.StateFlags.NORMAL, buttbgcol)

            buttons[but_inf['id']] = button
            if i == 0:
                buttongrid.add(buttons[but_inf['id']])
            else:
                buttongrid.attach_next_to(buttons[but_inf['id']],
                                               buttons[buttons_info[i - 1]['id']], Gtk.PositionType.BOTTOM, 1,
                                               1)

        for but_inf in buttons_info:
            if but_inf['cb'] is not None:
                buttons[but_inf['id']].connect("clicked", but_inf['cb'])

        return buttongrid

    ## Metoda inicjująca ramkę rysowania.
    # @returns Obiekt ramki rysowania.
    def init_drawing_frame(self):
        ## Ramka na pole do rysowania.
        self.frame = Gtk.Frame()
        self.frame.set_shadow_type(Gtk.ShadowType.IN)

        return self.frame

    ## Metoda inicjująca suwak historii ewolucji.
    # @returns Obiekty kontrolera suwaka i samego suwaka.
    def init_evo_scale(self):
        evo_scale_adjustment = Gtk.Adjustment(0, 0, 0, 1, 1, 0)

        evo_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=evo_scale_adjustment)
        evo_scale.set_digits(0)
        evo_scale.set_hexpand(True)
        evo_scale.set_valign(Gtk.Align.START)

        evo_scale.connect("value-changed", self.scale_value_changed)

        return evo_scale_adjustment, evo_scale

    ## Metoda inicjująca okno rysowania.
    # @returns Obiekt okna rysowania.
    def init_drawing_area(self):
        ## Pole do rysowania za pomocą Cairo.
        drawing_area = Gtk.DrawingArea()
        drawing_area.set_size_request(640, 640)
        drawing_area.set_hexpand(True)
        drawing_area.set_vexpand(True)

        drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        drawing_area.add_events(Gdk.EventMask.BUTTON_MOTION_MASK)
        drawing_area.add_events(Gdk.EventMask.SCROLL_MASK)

        drawing_area.connect("button-press-event", self.mouse_button_clicked)
        drawing_area.connect("motion_notify_event", self.mouse_moved_while_clicked)
        drawing_area.connect("scroll-event", self.mouse_wheel_scrolled)
        drawing_area.connect('draw', self.expose)

        return drawing_area

    ## Metoda inicjująca powierzchnię rysowania.
    # @param frame Ramka rysowania.
    # @param drawing_area Okno rysowania.
    # @returns Obiekt powierzchni rysowania dla Cairo.
    def init_drawing_surface(self, frame, drawing_area):
        ## Powierzchnia, na której Cairo będzie rysował.
        self.surface = None
        self.show_all()

        allocation = frame.get_allocation()
        self.surface = drawing_area.get_window().create_similar_surface(cairo.CONTENT_COLOR, allocation.width, allocation.height)

        return self.surface

    ## Inicjalizacja Cairo na danej powierzchni rysowania.
    # @param surface Powierzchnia rysowania na której rysować będzie Cairo .
    # @returns Obiekt kontekstu Cairo.
    @staticmethod
    def init_cairo_on_drawing_surface(surface):
        ## Obiekt kontekstu Cairo.
        cairo_ctx = cairo.Context(surface)

        return cairo_ctx

    ## Metoda przypisująca metody obsługi zdarzeń odpowiednim zdarzeniom na obiektach .
    def init_events_callbacks(self):


        self.connect("key-press-event", self.key_pressed)
        self.connect('destroy', self.quit)

        # SETTING REFRESH TIME FOR ANIMATION

        # GLib.timeout_add(int(1000 * self.TIME_DELTA_SEC), self.animate)  # segfault with PyPy
        # GObject.timeout_add(int(1000 * self.TIME_DELTA_SEC), self.animate)  # no effect in PyPy, refresh only on key/mouse events; works with CPython 2, 3

    # MANAGING PROJECT/HYPERGRAPH

    ## Metoda ustawiająca dany hipergraf jako aktywny.
    # @param hg Obiekt hipergrafu, który ma zostać ustawiony jako aktywny.
    def set_active_hypergraph(self, hg):

        self.active_hg = hg

        print(self.active_hg)

    ## Metoda zapisująca zserializowany plik hipergrafu do pliku.
    # Wyświetlane jest okno wyboru folderu i nazwy pliku.
    # @param button Opcjonalna referencja do przycisku, w przypadku, gdy metoda jest wywoływana jako callback po wciśnięciu przycisku.
    # @param path Opcjonalna ścieżka. Jeśli jest ustawiona, hipergraf zapisywany jest do danego pliku bez okna zapisu.
    def save_hypergraph_to_file(self, button=None, path=None):

        if self.active_hg.evolution_view_current_frame < len(self.active_hg.evolution_history) - 1:
            self.active_hg.load_evolutionary_state(frame=len(self.active_hg.evolution_history) - 1)


        if path is None:
            dialog = Gtk.FileChooserDialog("Wybierz plik projektu do zapisu", self, Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

            filter_py = Gtk.FileFilter()
            filter_py.set_name("Hg files")
            filter_py.add_pattern("*.hg")
            dialog.add_filter(filter_py)

            filter_any = Gtk.FileFilter()
            filter_any.set_name("Any files")
            filter_any.add_pattern("*")
            dialog.add_filter(filter_any)

            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                print("File selected: " + dialog.get_filename())
                path = dialog.get_filename()
                if not path.endswith(".hg"):
                    path += ".hg"
                pickle.dump(self.active_hg.dump_hg_as_dict(), open(path, "wb"))
            elif response == Gtk.ResponseType.CANCEL:
                print("Cancel clicked")

            dialog.destroy()
        else:
            pickle.dump(self.active_hg.dump_hg_as_dict(), open(path, "wb"))

    ## Metoda ładująca zserializowany plik hipergrafu do projektu.
    # Wyświetlane jest okno wyboru pliku.
    # @param button Opcjonalna referencja do przycisku, w przypadku, gdy metoda jest wywoływana jako callback po wciśnięciu przycisku.
    # @param path Opcjonalna ścieżka. Jeśli jest ustawiona, hipergraf ładowany jest z danego pliku bez okna wyboru.
    @redraw_function_decorator
    def load_hypergraph_from_file(self, button=None, path=None):
        newhg = HyperGraph()
        if path is None:
            dialog = Gtk.FileChooserDialog("Wybierz plik projektu do wczytania", self, Gtk.FileChooserAction.OPEN,
                                           (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                            Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
                                           )

            filter_py = Gtk.FileFilter()
            filter_py.set_name("Hg files")
            filter_py.add_pattern("*.hg")
            dialog.add_filter(filter_py)

            filter_any = Gtk.FileFilter()
            filter_any.set_name("Any files")
            filter_any.add_pattern("*")
            dialog.add_filter(filter_any)

            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                print("Open clicked")
                print("File selected: " + dialog.get_filename())

                path = dialog.get_filename()

            elif response == Gtk.ResponseType.CANCEL:
                print("Cancel clicked")
                dialog.destroy()
                return

            dialog.destroy()

        if path is not None:
            if path.endswith('py3hg'):
                hgastuple = pickle.load(open(path, "rb"))
                newhg.load_hg_from_tuple(hgastuple)
            else:
                hgasdict = pickle.load(open(path, "rb"))
                newhg.load_hg_from_dict(hgasdict)

            self.esa.set_upper(len(newhg.evolution_history) - 1)
            newhg.evolution_view_current_frame = len(newhg.evolution_history) - 1
            self.esa.set_value(newhg.evolution_view_current_frame)

            self.reset_hypergraph(hg=newhg)

    ## Metoda resetująca przesunięcie i powiększenie widoku.
    @redraw_function_decorator
    def reset_view_pan_and_scale(self, button=None):
        self.CANVAS_PAN_VECTOR *= 0
        self.ZOOM = 0.25

    ## Metoda czyszcząca całkowicie wszystkie elementy hipergrafu.
    @redraw_function_decorator
    def reset_hypergraph(self, button=None, hg=None):
        print("hg.reset")

        if hg is None:
            hg = HyperGraph()

        self.set_active_hypergraph(hg)

        Vert.vert_number = self.active_hg.get_max_xnode_index() + 1

    ## Metoda wykonywana przed akcją edytującą w jakiś sposób stan hipergrafu.
    def before_modify_action_handler(self):
        print('Zapisano akcje do listy')
        self.redo_states = list()
        self.undo_states.append(pickle.dumps(self.active_hg))

    ## Metoda wykonywana po akcji edytującej w jakiś sposób stan hipergrafu.
    @redraw_function_decorator
    def after_modify_action_handler(self):
        # print('Zapisano akcje do listy')
        # self.redo_states = list()
        # self.undo_states.append(pickle.dumps(self.active_hg))

        pass

    # MOUSE CALLBACKS

    ## Metoda pozwalająca reagować na kliknięcie przyciskiem myszy.
    #
    # @param event Obiekt zdarzenia, które zawiera informacje m.in. o numerze przycisku i krotności kliknięcia.
    @redraw_function_decorator
    def mouse_button_clicked(self, widget, event):
        # x, y, state = event.window.get_pointer()
        x = event.x
        y = event.y
        state = event.state
        pos_unzoomed = Utils.map_pos_screen_to_canvas(np.array((x, y), dtype=np.double), self.DRAWING_AREA_CENTER, self.ZOOM, self.CANVAS_PAN_VECTOR)

        if self.DEBUG_MODE:
            print("press:{}; mapped:{}; from:{}".format((x, y), pos_unzoomed, state, widget))

        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == 1:
                print("left click")

            elif event.button == 2:
                self.add_node(pos_unzoomed)

            elif event.button == 3:
                xid = self.active_hg.get_colliding_xnode_id_by_position(pos_unzoomed, rmul = max(1.0, 1.0/self.ZOOM))
                if xid is not None:
                    self.select_toggle_colliding_xnode(xid)

                    self.deactivate_all()

                    xsel = self.active_hg.get_selected_xnodes_id()

                    if len(xsel) > 0:
                        selnid = self.active_hg.get_selected_nodes_id()
                        selhbid = self.active_hg.get_selected_hbnodes_id()

                        lastselxid = xsel[-1]
                        lastselxnode = self.active_hg.get_xnode_by_id(lastselxid)

                        if lastselxnode.is_of_vert_type(Vert.T_NODE):
                            connodes = self.active_hg.get_all_reachable_nodes_id_from_node_id(xid)
                            for cn in connodes:
                                self.active_hg.activate_xnode_by_id(cn)
                        else:
                            commonnodesid = self.active_hg.get_all_shared_nodes_id_in_hyperbranches_list(hbid_list=selhbid)
                            for cnid in commonnodesid:
                                self.active_hg.activate_xnode_by_id(cnid)

        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            pass
        elif event.type == Gdk.EventType._3BUTTON_PRESS:
            pass

        if self.custom_clickables is not None and len(self.custom_clickables) > 0:
            try:
                for cc in self.custom_clickables:
                    try:
                        cc.mouse_button_clicked(widget, event)
                    except Exception as e:
                        print(' >> nie da sie narysowac {} : {}'.format(cc, e))
                        # TODO: usuwanie cc z listy self.custom_clickables
            except:
                pass

        self.old_mouse_pos = np.array((x, y), dtype=np.double)
        self.old_mouse_button = event.button

    ## Metoda pozwalająca utworzyć wierzchołek w danym miejscu.
    # @param pos Miesce utworzenia wierzchołka.
    @undo_redo_function_decorator
    def add_node(self, pos):
        node_id = self.active_hg.add_node(name="", position=pos, prop_dict={})
        # node = self.active_hg.get_xnode_by_id(node_id)
        self.active_hg.select_xnode_by_id(node_id)
        print("added new vert {} at {}".format(node_id, pos))

    ## Metoda pozwalająca zaznaczyć lub odznaczyć kliknięty element hipergrafu.
    # @param xid Id elementu hipergrafu.
    @undo_redo_function_decorator
    def select_toggle_colliding_xnode(self, xid):
        self.active_hg.select_toggle_xnode_by_id(xid)
        print("clicked at vert: {}".format(xid))

    ## Metoda pozwalająca reagować na przeciągnięcie myszy podczas kliknięcia.
    #
    # @param event Obiekt zdarzenia, które zawiera informacje m.in. o wektorze przesunięcia.
    @redraw_function_decorator
    def mouse_moved_while_clicked(self, widget, event):
        # x, y, state = event.window.get_pointer()
        x = event.x
        y = event.y
        state = event.state

        nppos = np.array((x, y), dtype=np.double)
        vec = nppos - self.old_mouse_pos

        vselected = [self.active_hg.get_xnode_by_id(xid) for xid in self.active_hg.get_selected_xnodes_id()]

        if self.old_mouse_button == 1:
            self.CANVAS_PAN_VECTOR += Utils.map_vec_screen_to_canvas(vec, self.ZOOM)
        elif self.old_mouse_button == 2:
            pass
        elif self.old_mouse_button == 3:
            for sv in vselected:
                sv.translate_by_vec(Utils.map_vec_screen_to_canvas(vec, self.ZOOM))
            if len(vselected) == 0:
                self.CANVAS_PAN_VECTOR += Utils.map_vec_screen_to_canvas(vec, self.ZOOM)

        # if DEBUG_MODE:
        #     print("motion:({},{});vec:{}".format(x, y, vec))

        self.old_mouse_pos = nppos

    ## Metoda pozwalająca reagować na obrót rolki myszy.
    #
    # @param event Obiekt zdarzenia, które zawiera informacje m.in. o kierunku obrotu.
    @redraw_function_decorator
    def mouse_wheel_scrolled(self, widget, event):
        # print("mouse scrolled")

        if event.direction == Gdk.ScrollDirection.UP:
            self.ZOOM *= 1.1
            if self.ZOOM > self.MAXZOOM:
                self.ZOOM = self.MAXZOOM
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.ZOOM /= 1.1
            if self.ZOOM < self.MINZOOM:
                self.ZOOM = self.MINZOOM

    # KEYBOARD CALLBACKS

    ## Metoda pozwalająca reagować na wciśnięte klawisze na klawiaturze.
    #
    # @param event Obiekt zdarzenia, które zawiera informacje m.in. o kodzie wciśniętego klawisza.
    @redraw_function_decorator
    def key_pressed(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        xsel = self.active_hg.get_selected_xnodes_id()

        print("key {}".format(key))

        # GDK_CONTROL_MASK

        if   key == "p":
            self.toggle_animate()

        elif key == "a":
            self.toggle_select_all()

        elif key == "m":  # nowa hipergalaz
            self.make_hyperarc()

        elif key == "e":  # edycja
            self.edit_all_selected_xnodes()

        elif key == "KP_Add" or key == "KP_Subtract":
            if len(xsel) > 0:
                if key == "KP_Add":
                    selnid = self.active_hg.get_selected_nodes_id()
                    selhbid = self.active_hg.get_selected_hbnodes_id()

                    lastselxid = xsel[-1]
                    lastselxnode = self.active_hg.get_xnode_by_id(lastselxid)

                    all_conn_nodes_id_to_last_sel = self.active_hg.get_all_connected_xnodes_id_by_xnode_id(lastselxid)

                    if len(all_conn_nodes_id_to_last_sel) > 0:
                        for xid in xsel:
                            nodes_id_to_sel = self.active_hg.get_all_connected_xnodes_id_by_xnode_id(xid)
                            for xi in nodes_id_to_sel:
                                self.select_xnode(xi)

                    else:

                        if lastselxnode.is_of_vert_type(Vert.T_NODE):

                            unselected_nodes_id = [xid for xid in self.active_hg.get_all_nodes_id() if xid not in selnid]
                            closest_node_id = self.active_hg.get_closest_xnode_id_by_xnode_id(lastselxid, xid_list=unselected_nodes_id)

                            if closest_node_id is not None:
                                print("nid: {}".format(closest_node_id))
                                self.select_xnode(closest_node_id)
                        else:
                            unselected_hbnodes_id = [xid for xid in self.active_hg.get_all_hyperbranches_id() if xid not in selhbid]
                            closest_hbnode_id = self.active_hg.get_closest_xnode_id_by_xnode_id(lastselxid, xid_list=unselected_hbnodes_id)

                            if closest_hbnode_id is not None:
                                print("hbid: {}".format(closest_hbnode_id))
                                self.select_xnode(closest_hbnode_id)


                    # for xid in list(xsel):
                    #     all_conn_nodes_id = self.active_hg.get_all_connected_xnodes_id_by_xnode_id(xid)
                    #
                    #     if all_conn_nodes_id is not None and len(all_conn_nodes_id) > 0:
                    #         for xid_to_sel in all_conn_nodes_id:
                    #             self.select_xnode(xid_to_sel)
                    #     else:
                    #         unc_nodes_id = [nid for nid in self.active_hg.get_all_unconnected_nodes_id() if nid not in list(xsel)]
                    #         print("uncnodes {}".format(unc_nodes_id))
                    #         if len(unc_nodes_id) > 0:
                    #             closest_node_id = self.active_hg.get_closest_xnode_id_by_xnode_id(xsel[-1], xid_list=unc_nodes_id)
                    #             self.select_xnode(closest_node_id)
                    #         break

                else:
                    self.deselect_xnode(xsel[-1])

        elif key == "l":
            self.active_hg.load_next_evolutionary_state()

        elif key == "j":
            self.active_hg.load_previous_evolutionary_state()

        elif key == "k":
            self.active_hg.save_evolutionary_state(True)

        elif key == "Delete":
            self.delete_selected_xnode()

    ## Metoda pozwalająca reagować na zmiany położenia suwaka historii ewolucji hipergrafu.
    @redraw_function_decorator
    def scale_value_changed(self, event):
        val = self.esa.get_value()

        self.active_hg.evolution_view_current_frame = int(val)
        self.active_hg.load_evolutionary_state(int(val))

    # BUTTON CALLBACKS

    ## Metoda pozwalająca włączyć lub wyłączyć animację elementów hipergrafu.
    # @param button Obiekt przycisku, z którego ewentualnie wywoływana jest metoda.
    def toggle_animate(self, button=None):
        self.ANIMATE = not self.ANIMATE

    ## Metoda pozwalająca cofnąć cofniętą wykonaną akcję.
    # @param button Obiekt przycisku, z którego ewentualnie wywoływana jest metoda.
    def undo_action(self, button=None):

        if len(self.undo_states) > 0:
            self.redo_states.append(pickle.dumps(self.active_hg))

            prev_state = self.undo_states.pop()

            newhg = pickle.loads(prev_state)

            self.esa.set_upper(len(newhg.evolution_history) - 1)
            newhg.evolution_view_current_frame = len(newhg.evolution_history) - 1
            self.esa.set_value(newhg.evolution_view_current_frame)

            self.reset_hypergraph(hg=newhg)
            print('Mozna cofnac jeszcze {} razy'.format(len(self.undo_states)))
        else:
            print('Maksymalnie cofnieto akcje')

    ## Metoda pozwalająca powtórzyć cofniętą akcję.
    # @param button Obiekt przycisku, z którego ewentualnie wywoływana jest metoda.
    def redo_action(self, button=None):
        if len(self.redo_states) > 0:
            self.undo_states.append(pickle.dumps(self.active_hg))

            next_state = self.redo_states.pop()
            self.reset_hypergraph(hg=pickle.loads(next_state))
        else:
            print('Maksymalnie powtorzono akcje')

    ## Metoda pozwalająca zaznaczyć lub odznaczyć element hipergrafu po jego id.
    @undo_redo_function_decorator
    def toggle_select_all(self, button=None):
        xsel = self.active_hg.get_selected_xnodes_id()

        if len(xsel) == 0:
            for xid in self.active_hg.get_all_xnodes_id():
                # print("selecting xnode {}".format(xid))
                self.active_hg.select_xnode_by_id(xid)
                self.active_hg.get_xnode_by_id(xid).stop_movement()
        else:
            for xid in list(xsel):
                # print("deselecting xnode {} from xsel {}".format(xid, list(xsel)))
                self.active_hg.deselect_xnode_by_id(xid)

    ## Metoda usuwająca wyróżnienie ze wszystkich elementów hipergrafu.
    @undo_redo_function_decorator
    def deactivate_all(self, button=None):
        xact = self.active_hg.get_activated_xnodes_id()

        if len(xact) > 0:
            for xid in list(xact):
                # print("deselecting xnode {} from xsel {}".format(xid, list(xsel)))
                self.active_hg.deactivate_xnode_by_id(xid)

    ## Metoda pozwalająca zaznaczyć element hipergrafu po jego id.
    # @param xid Id elementu hipergrafu.
    def select_xnode(self, xid):
        self.active_hg.select_xnode_by_id(xid)

    ## Metoda pozwalająca odznaczyć element hipergrafu po jego id.
    # @param xid Id elementu hipergrafu.
    def deselect_xnode(self, xid):
        self.active_hg.deselect_xnode_by_id(xid)

    ## Metoda pozwalająca utworzyć nowy wierzchołek.
    @undo_redo_function_decorator
    def make_node(self, button=None):
        pos = Utils.map_pos_screen_to_canvas(self.DRAWING_AREA_CENTER, self.DRAWING_AREA_CENTER, self.ZOOM, self.CANVAS_PAN_VECTOR)
        nid = self.active_hg.add_node(name='', position=pos, prop_dict={})
        self.active_hg.select_xnode_by_id(nid)

    ## Metoda pozwalająca utworzyć nową hiperkrawędź.
    # Wyświetlany jest dialog z polami, które można edytować.
    @undo_redo_function_decorator
    def make_hyperedge(self, button=None):
        xsel = self.active_hg.get_selected_xnodes_id()
        heelems_id_list = [xid for xid in xsel if
                               self.active_hg.get_xnode_by_id(xid).is_of_vert_type(Vert.T_NODE)]

        if len(heelems_id_list) >= 2:
            pd = dict(self.active_hg.project_properties['additional_xnode_properties'])
            pd.update(self.active_hg.project_properties['additional_hbnode_properties'])
            properties = HBNode(name='he', hbtype=HBNode.HB_DUMMY, prop_dict=pd,
                                pos=self.DRAWING_AREA_CENTER).get_properties_dict()  # name, hbtype, pos, prop_dict):

            for prop_to_delete in ['id', 'elements']:
                if prop_to_delete in properties:
                    properties.pop(prop_to_delete)

            dialog = EntryDialog(self, dialog_name="Nowa hiperkrawędź", labels_entries_dict=properties)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                self.toggle_select_all()
                return_dict = dialog.get_result_dict()
                hbid = self.active_hg.add_hyperbranch(name=return_dict['name'], hbtype=HBNode.HB_HYPEREDGE,
                                                      nodes_id_list=heelems_id_list, prop_dict=return_dict)
                self.select_xnode(hbid)

            dialog.destroy()

    ## Metoda pozwalająca utworzyć nową hiperpętlę.
    # Wyświetlany jest dialog z polami, które można edytować.
    @undo_redo_function_decorator
    def make_hyperloop(self, button=None):
        xsel = self.active_hg.get_selected_xnodes_id()

        heelems_id_list = [xid for xid in xsel if self.active_hg.get_xnode_by_id(xid).is_of_vert_type(Vert.T_NODE)]

        if len(heelems_id_list) == 1:
            pd = dict(self.active_hg.project_properties['additional_xnode_properties'])
            pd.update(self.active_hg.project_properties['additional_hbnode_properties'])
            properties = HBNode(name='hl', hbtype=HBNode.HB_DUMMY, prop_dict=pd,
                                pos=self.DRAWING_AREA_CENTER).get_properties_dict()  # name, hbtype, pos, prop_dict):

            for prop_to_delete in ['id', 'elements', 'bg_color']:
                if prop_to_delete in properties:
                    properties.pop(prop_to_delete)

            properties['multiplicity'] = 2

            dialog = EntryDialog(self, dialog_name="Nowa hiperpętla", labels_entries_dict=properties)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                self.toggle_select_all()
                return_dict = dialog.get_result_dict()

                mult = return_dict.pop('multiplicity')

                hbid = self.active_hg.add_hyperbranch(name=return_dict['name'], hbtype=HBNode.HB_HYPERLOOP,
                                                      nodes_id_list=[heelems_id_list[0] for nid in range(mult)], prop_dict=return_dict)
                self.select_xnode(hbid)

            dialog.destroy()

    ## Metoda pozwalająca utworzyć nowy hiperłuk.
    # Wyświetlany jest dialog z polami, które można edytować.
    @undo_redo_function_decorator
    def make_hyperarc(self, button=None):
        xsel = self.active_hg.get_selected_xnodes_id()
        heelems_id_list = [xid for xid in xsel if self.active_hg.get_xnode_by_id(xid).is_of_vert_type(Vert.T_NODE)]

        if len(heelems_id_list) >= 2:
            pd = dict(self.active_hg.project_properties['additional_xnode_properties'])
            pd.update(self.active_hg.project_properties['additional_hbnode_properties'])
            properties = HBNode(name='ha', hbtype=HBNode.HB_DUMMY, prop_dict=pd, pos=self.DRAWING_AREA_CENTER).get_properties_dict()  # name, hbtype, pos, prop_dict):

            for prop_to_delete in ['id', 'elements']:
                if prop_to_delete in properties:
                    properties.pop(prop_to_delete)

            dialog = EntryDialog(self, dialog_name="Nowy hiperłuk", labels_entries_dict=properties)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                self.toggle_select_all()
                return_dict = dialog.get_result_dict()
                hbid = self.active_hg.add_hyperbranch(name=return_dict['name'], hbtype=HBNode.HB_HYPERARC, nodes_id_list=heelems_id_list, prop_dict=return_dict)
                self.select_xnode(hbid)

            dialog.destroy()

    ## Metoda pozwalająca edytować ostatni zaznaczony element hipergrafu.
    # Wyświetlany jest dialog z polami, które można edytować.
    @undo_redo_function_decorator
    def edit_selected_xnode(self, button=None):
        xsel = self.active_hg.get_selected_xnodes_id()

        if len(xsel) > 0:
            xnode_id = xsel[len(xsel) - 1] if len(xsel) > 0 else None
            xnode = self.active_hg.get_xnode_by_id(xnode_id)
            print("editing {}".format(xnode_id))

            properties = xnode.get_properties_dict()

            props_not_editable = ['id', 'elements']

            for prop in props_not_editable:
                if prop in properties:
                    properties.pop(prop)

            dialog = EntryDialog(self, dialog_name="Edycja", labels_entries_dict=properties)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                return_dict = dialog.get_result_dict()

                # return_dict = dict([(k, res_dict[k]) for k in res_dict.keys()])

                print("return_dict: {} ".format(return_dict))

                xnode.update_properties(return_dict)

            dialog.destroy()

    ## Metoda pozwalająca edytować wszystkie zaznaczone elementy hipergrafu.
    # Wyświetlany jest dialog z polami, które można edytować.
    @undo_redo_function_decorator
    def edit_all_selected_xnodes(self, button=None):
        xsel = self.active_hg.get_selected_xnodes_id()

        if len(xsel) > 0:
            common_props = None

            for xid in xsel:
                xnode = self.active_hg.get_xnode_by_id(xid)
                print("reading {}".format(xid))

                xnode_properties = xnode.get_properties_dict()
                if common_props is None:
                    common_props = xnode_properties

                props_not_editable = ['id', 'elements']
                for p in props_not_editable:
                    if p in xnode_properties:
                        xnode_properties.pop(p)

                for p in [k for k in common_props.keys()]:
                    if p not in xnode_properties:
                        common_props.pop(p)
                    else:
                        if common_props[p] != '*':
                            if common_props[p] != xnode_properties[p]:
                                common_props[p] = '*'

            dialog = EntryDialog(self, dialog_name="Edycja", labels_entries_dict=common_props)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                return_dict = dialog.get_result_dict()

                print("return_dict: {} ".format(return_dict))

                for p in [k for k in return_dict.keys()]:
                    if return_dict[p] == '*':
                        return_dict.pop(p)

                for xid in xsel:
                    xnode = self.active_hg.get_xnode_by_id(xid)
                    print("editing {}".format(xid))

                    xnode.update_properties(return_dict)

            dialog.destroy()

    ## Metoda usuwająca zaznaczone elementy hipergrafu.
    @undo_redo_function_decorator
    def delete_selected_xnode(self, button=None):
        xsel = self.active_hg.get_selected_xnodes_id()

        for xid in list(xsel):
            self.active_hg.delete_xnode_by_id(xid)

    ## Metoda pozwalająca dodać nową właściwość do wierzchołków hipergrafu.
    @undo_redo_function_decorator
    def add_property_to_nodes(self, button=None):
        prop_dict = dict()

        prop_dict['property name'] = 'prop name'
        prop_dict['property value'] = 0

        dialog = EntryDialog(self, dialog_name="Dodaj właściwość do wierzchołków", labels_entries_dict=prop_dict)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            return_dict = dialog.get_result_dict()


            prop_to_add = dict()

            propname = return_dict['property name']
            propval = return_dict['property value']
            prop_to_add[propname] = propval

            if propname not in self.active_hg.project_properties['additional_node_properties']:
                self.active_hg.project_properties['additional_node_properties'].update(prop_to_add)

                nid_list = self.active_hg.get_all_nodes_id()
                for nid in nid_list:
                    self.active_hg.get_node_by_id(nid).set_property_value(propname, propval)

        dialog.destroy()

    ## Metoda pozwalająca dodać nową właściwość do hipergałęzi hipergrafu.
    @undo_redo_function_decorator
    def add_property_to_hbnodes(self, button=None):
        prop_dict = dict()

        prop_dict['property name'] = 'prop name'
        prop_dict['property value'] = 0

        dialog = EntryDialog(self, dialog_name="Dodaj właściwość do hipergałęzi", labels_entries_dict=prop_dict)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            return_dict = dialog.get_result_dict()

            prop_to_add = dict()

            propname = return_dict['property name']
            propval = return_dict['property value']
            prop_to_add[propname] = propval

            if propname not in self.active_hg.project_properties['additional_hbnode_properties']:
                self.active_hg.project_properties['additional_hbnode_properties'].update(prop_to_add)

                hid_list = self.active_hg.get_all_hyperbranches_id()
                for hid in hid_list:
                    self.active_hg.get_hbnode_by_id(hid).set_property_value(propname, propval)

        dialog.destroy()

    ## Metoda pozwalająca dodać nową właściwość do wierzchołków i hipergałęzi hipergrafu.
    @undo_redo_function_decorator
    def add_property_to_xnodes(self, button=None):
        prop_dict = dict()

        prop_dict['property name'] = 'prop name'
        prop_dict['property value'] = 0

        dialog = EntryDialog(self, dialog_name="Dodaj właściwość do elementów", labels_entries_dict=prop_dict)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            return_dict = dialog.get_result_dict()

            prop_to_add = dict()

            propname = return_dict['property name']
            propval = return_dict['property value']
            prop_to_add[propname] = propval

            if propname not in self.active_hg.project_properties['additional_xnode_properties']:
                self.active_hg.project_properties['additional_xnode_properties'].update(prop_to_add)

                xid_list = self.active_hg.get_all_xnodes_id()
                for xid in xid_list:
                    self.active_hg.get_xnode_by_id(xid).set_property_value(propname, propval)

        dialog.destroy()

    ## Metoda wyświetlająca okno z listą macierzy hipergrafu.
    def show_matricies(self, button=None):
        res_as_str = Ma.example_result_generator(self.active_hg)

        dialog = TextResultDialog(self, dialog_name="Hipergraf", result_text=res_as_str)
        response = dialog.run()

        dialog.destroy()

    # DRAWING

    ## Metoda rysująca krzyż w danym punkcie o danej wielkości.
    # @param cr Obiekt biblioteki Cairo.
    # @param p Punkt środka.
    # @param r_canv Promień na płótnie.
    @staticmethod
    def draw_cross(cr, p, r_canv):
        cr.move_to(*(p - (r_canv, 0)))
        cr.line_to(*(p + (r_canv, 0)))
        cr.stroke()

        cr.move_to(*(p - (0, r_canv)))
        cr.line_to(*(p + (0, r_canv)))
        cr.stroke()

        # text = str(p)
        # cr.select_font_face("Terminal", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        # font_size = 10
        # cr.set_font_size(font_size)
        # e_xbearing, e_ybearing, e_width, e_height, e_xadvance, e_yadvance = cr.text_extents(text)
        # cr.move_to(*(p + (-(e_width / 2 + e_xbearing), -5)))
        # cr.show_text(text)
        #
        # text = str(Utils.map_pos_screen_to_canvas(p, self.DRAWING_AREA_CENTER, self.ZOOM, self.PAN_VECTOR))
        # cr.select_font_face("Terminal", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        # font_size = 10
        # cr.set_font_size(font_size)
        # e_xbearing, e_ybearing, e_width, e_height, e_xadvance, e_yadvance = cr.text_extents(text)
        # cr.move_to(*(p + (-(e_width / 2 + e_xbearing), +5)))
        # cr.show_text(text)
        # cr.stroke()

    ## Metoda rysująca krzyż środka ekranu.
    # @param cr Obiekt biblioteki Cairo.
    def draw_center_cross(self, cr):
        self.draw_cross(cr, self.DRAWING_AREA_CENTER, 10)

    ## Metoda rysująca krzyż środka płótna rysowania Cairo.
    # @param cr Obiekt biblioteki Cairo.
    def draw_canvas_cross(self, cr):
        p = Utils.map_pos_canvas_to_screen(np.array((0.0,0.0)), self.DRAWING_AREA_CENTER, self.ZOOM, self.CANVAS_PAN_VECTOR)

        self.draw_cross(cr, p, 10 * self.ZOOM)

    ## Metoda rysująca siatkę tła okna wyświetlania.
    # @param cr Obiekt biblioteki Cairo.
    def draw_canvas_grid(self, cr):
        cr.set_source_rgb(*(0.85, 0.85, 0.85))
        cr.set_line_width(1)

        p = Utils.map_pos_canvas_to_screen(np.array((0.0, 0.0)), self.DRAWING_AREA_CENTER, self.ZOOM, self.CANVAS_PAN_VECTOR)

        p00 = np.array((0,0), dtype=np.float)
        p11 = self.DRAWING_AREA_CENTER*2

        rscrx = self.DRAWING_AREA_CENTER[0]
        rscry = self.DRAWING_AREA_CENTER[1]

        r = 250*self.ZOOM

        for iy in range(int(p11[1] // r)):
            cr.move_to(*(p00[0], (p[1]) % r + iy*r))
            cr.line_to(*(p11[0], (p[1]) % r  + iy*r))
            cr.stroke()

        for ix in range(int(p11[0] // r)):
            cr.move_to(*((p[0]) % r + ix*r, p00[1] ))
            cr.line_to(*((p[0]) % r  + ix*r, p11[1]))
            cr.stroke()

        # cr.move_to(*(p[0], p00[1]))
        # cr.line_to(*(p[0], p11[1]))
        # cr.stroke()

        cr.stroke()

        cr.set_source_rgb(*(0.5, 0.5, 0.5))
        cr.set_line_width(1)

        self.draw_center_cross(cr)

        p0 = self.DRAWING_AREA_CENTER
        p1 = Utils.map_pos_canvas_to_screen(np.array((0.0, 0.0)), self.DRAWING_AREA_CENTER, self.ZOOM, self.CANVAS_PAN_VECTOR)

        # cr.move_to(*(p0))
        # cr.line_to(*(p1))
        cr.stroke()

        self.draw_canvas_cross(cr)

    ## Metoda powodująca rysowanie hipergrafu.
    # Jest wywoływana przez obiekt klasy DrawingArea.
    # @param da Obiekt klasy DrawingArea z biblioteki Gtk3.
    # @param cr Obiekt biblioteki Cairo.
    @redraw_function_decorator
    def expose(self, da, cr):
        t_start = time.time()

        #def a():
        #    self.active_hg.update(self.TIME_DELTA_SEC)
        #    time.sleep(self.TIME_DELTA_SEC)

        if self.ANIMATE:
            self.active_hg.update(self.TIME_DELTA_SEC)
        else:
            time.sleep(self.TIME_DELTA_SEC)
            
            #self.wt = threading.Thread(target=a, args=())
            #self.wt.start()
            
            # należy dorobić manager, proxy itd... nie da sie w ten sposob wspoldzielic obiektow (np active_hg)
            # jest to jednak dosc obiecujacy sposob
            #self.p = Process(target=a, args=()) 
            #self.p.start()

        allocation = self.frame.get_allocation()

        self.DRAWING_AREA_SIZE[0] = allocation.width
        self.DRAWING_AREA_SIZE[1] = allocation.height

        self.DRAWING_AREA_CENTER = self.DRAWING_AREA_SIZE / 2

        cr.set_source_surface(self.surface, 0, 0)

        cr.set_tolerance(1.0)
        cr.set_antialias(cairo.ANTIALIAS_GRAY) #  ANTIALIAS_DEFAULT ANTIALIAS_NONE ANTIALIAS_GRAY ANTIALIAS_SUBPIXEL

        cr.set_source_rgb(*(0.9, 0.9, 0.9))
        cr.paint()

        self.draw_canvas_grid(cr)

        cr.set_source_rgb(*(0.5, 0.5, 0.5))
        cr.set_line_width(1)

        self.active_hg.draw(cr, self.CANVAS_PAN_VECTOR, self.DRAWING_AREA_CENTER, self.ZOOM)

        if self.custom_drawables is not None and len(self.custom_drawables) > 0:
            try:
                for cd in self.custom_drawables:
                    try:
                        cd.draw(cr, self.CANVAS_PAN_VECTOR, self.DRAWING_AREA_CENTER, self.ZOOM)
                    except Exception as e:
                        print(' >> nie da sie narysowac {} : {}'.format(cd, e))
                        # TODO: usuwanie cd z listy self.custom_drawables
            except:
                pass

        self.esa.set_upper(len(self.active_hg.evolution_history) - 1)
        self.esa.set_value(self.active_hg.evolution_view_current_frame)

        # if self.ad1.get_value() > self.ad1.get_upper():
        #     self.ad1.set_value(self.ad1.get_upper())

        cr.fill()

        t_end = time.time()
        dt_real = t_end - t_start
        dur = time.time() - self.START_TIME_SEC
        # print('t{0:.2f}s {1:.2f}fps'.format(dur, 1 / dt_real))
        # 

    ## Metoda realizująca zamknięcie aplikacji.
    @staticmethod
    def quit(widget=None):
        # self.working_thread.
        Gtk.main_quit()
        
    def documenting_dummy_fun(self):
        self.dialog = EditorDialog()
        self.dialog = EntryDialog()
        self.dialog = TextResultDialog()
        self.dialog = TreeViewResultDialog()  

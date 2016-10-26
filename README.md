## README 

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen13.png)

### Teoria 

Projekt powstał głównie w oparciu o informacje z książki: B. Korzan, "Grafy, hipergrafy i sieci".

Hipergraf: H = [X, U, P],
gdzie:

* X - zbiór wierzchołków,
* U - zbiór hipergałęzi (kiperkrawędzie, hiperłuki, hiperpętle, inne),
* P - zbiór relacji wierzchołków do hipergałęzi.

Sposoby przedstawienia hipergrafu jako macierz:

* macierz incydencji A(G) (zwykła lub binarna Ab(G)),
* macierz przyległości wierzchołków R(G) (zwykła lub binarna Rb(G)),
* macierz przyległości gałęzi B(G) (zwykła lub binarna Bb(G)),
* macierz przejść P(G) (zwykła lub binarna Pb(G)).
* macierz osiągalności (silnej spójności) D
* macierz spójności S

### Aktualny stan 

* Program napisany w języku Python (najlepiej działa z implementacją CPython3),
* interfejs zaimplementowany za pomocą pakietu GTK3 (przez Python GObject Introspection),
* rysowanie hipergrafu za pomocą biblioteki Cairo,
* obliczenia macierzowe z wykorzystaniem biblioteki NumPy,
* zapis/odczyt pliku projektu do/z pliku (pickle: dump/load),
* undo/redo akcji (pickle: dumps/loads)
* sterowanie za pomocą myszki i klawiatury,
* toolbar umożliwiający wykonanie operacji na hipergrafie,
* boczny pasek przycisków umożliwiający obliczenie własności hipergrafu - po kliknięciu pojawia się okno z wynikiem,
* reprezentacja hipergrafu za pomocą grafu dwudzielnego - jedna grupa wierzchołków tego grafu to wierzchołki hipergrafu, druga to hipergałęzie,
* możliwość edytowania słownika właściwości wierzchołków i hipergałęzi (także wielu naraz),
* układanie wierzchołków na płaszczyźnie na podstawie sił oddziałujących między nimi (sprężyna, grawitacja, opór). 
W pewnym stopniu zoptymalizowano:

    - zamiast pętli jęz. Python3, wektoryzacja i operacje macierzowe NumPy,
    - PyOpenCL wspomagający krytyczne wydajnościowo fragmenty.

* metody przekształcające hipergraf na macierze A, Ab, R, Rb, B, Bb, P, Pb, D, S,
* możliwość znalezienia najkrótszej drogi za pomocą alg. Dijkstry,
* edytor skryptów, w którym można uruchomić algorytm analizujący/edytujący/tworzący model,
* dodatkowe klasy pomocnicze, metody pomocnicze.

### Zależności 

#### Ubuntu 

(dla python3: na Ubuntu 16.04 Mate 64bit aplikacja działa bez instalowania dodatkowych zależności, standardowa wersja Ubuntu 16.04 64bit wymaga zainstalowania numpy)

##### apt dla Python3: 

* python3
* python3-dev
* python-wheel-common
* pip3
* python-gi-cairo
* llvm (opcjonalnie)

##### pip3 dla Python3: 

* numpy
* cairo
* pgi
* pyopencl (opcjonalnie)

### Using the environment

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen01.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen02.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen03.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen04.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen05.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen06.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen07.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen08.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen09.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen10.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen11.png)

![screen](https://raw.githubusercontent.com/michal2229/environment-to-analyze-systems-modeled-as-hypergraphs-or-hypernetworks/master/results/screen12.png)

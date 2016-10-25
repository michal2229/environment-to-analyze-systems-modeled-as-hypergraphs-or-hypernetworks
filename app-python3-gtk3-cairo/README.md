## README ##

### Zależności ###

Przed uruchomieniem programu należy upewnić się, że w systemie 
obecne są biblioteki wyspecyfikowane w pliku *requirements.txt*. 
Na systemach posiadających już środowisko uruchomieniowe języka Python 3 
oraz zainstalowany program *pip*, wystarczy zwykle uruchomić terminal/wiersz polecenia 
w folderze programu oraz wpisać w terminalu komendę:
```
pip install -r requirements.txt

```
Prawdopodobnie komendę tą trzeba będzie uruchomić z prawami administratora. 
W przypadku niepowodzenia należy upewnić się, czy dodatkowe zależności nie 
powinny być zainstalowane z repozytorium (na systemach Linux) lub za pomocą instalatora 
pobranego ze strony głównej danego pakietu - dotyczyć to może w szczególności pakietu *GTK+ 3* 
(w skład gtórego wchodzą *GI* oraz *Cairo*), 
*OpenCL SDK* (w przypadku chęci używania biblioteki *PyOpenCL*). 

Przydatne linki:

* https://wiki.tiker.net/PyOpenCL/Installation/Windows
* http://www.gtk.org/download/windows.php
* http://www.scipy.org/scipylib/download.html
* http://developer.amd.com/tools-and-sdks/opencl-zone
* https://software.intel.com/en-us/intel-opencl
* https://developer.nvidia.com/opencl

### Uruchamianie ###

Plikiem głównym aplikacji jest plik *application-main.py* 
i ten plik należy uruchamiać za pomocą interpretera języka Python 3. 
Można to zrobić na kilka sposobów:

* klikając dwukrotnie na plik application-main.py, ustawiając go wcześniej jako wykonywalny
* otwierając terminal w folderze projektu i wpisując:
```
python3 application-main.py
```
* otwierając terminal w folderze projektu i wpisując:
```
python application-main.py
```
* otwierając terminal w folderze projektu i wpisując:
```
./application-main.py
```
* otwierając terminal w folderze projektu i wpisując (wymaga zainstalowanego programu Make):
```
make
```

### Konfiguracja ###

Domyślnie używanie OpenCL jest wyłączone. Aby 
je włączyć, należy zmienić edytować plik *OCL.py* zmieniając w nim linijkę 
```
DEFAULT_ENABLE_OPENCL = False
``` 
na 
```
DEFAULT_ENABLE_OPENCL = True
```

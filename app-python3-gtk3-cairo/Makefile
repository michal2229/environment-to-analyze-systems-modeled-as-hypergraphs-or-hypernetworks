cpython3=/usr/bin/env python3
mainsrc=application-main.py

all: main

main: $(mainsrc) *.py
	PYOPENCL_COMPILER_OUTPUT=1 $(cpython3) $(mainsrc)
	
ctx0: $(mainsrc) *.py
	PYOPENCL_COMPILER_OUTPUT=1 PYOPENCL_CTX=0 $(cpython3) $(mainsrc)	
	
ctx1: $(mainsrc) *.py
	PYOPENCL_COMPILER_OUTPUT=1 PYOPENCL_CTX=1 $(cpython3) $(mainsrc)


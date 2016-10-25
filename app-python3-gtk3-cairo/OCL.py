# -*- coding: utf-8 -*-

## @file OCL.py
## @package OCL

import numpy as np

## Zmienna ustawiająca, czy program powinien korzystać z OpenCL.
# DEFAULT_ENABLE_OPENCL = True
DEFAULT_ENABLE_OPENCL = False


if DEFAULT_ENABLE_OPENCL:
    import pyopencl as cl

import time
# import numba
# from numba import double
# from numba.decorators import jit
# import locale
# locale.setlocale(locale.LC_NUMERIC, 'C')

# from Vert import Node, HBNode, Vert
# from VertArranger import VertArranger
# from Utils import Utils

## Klasa narzędzi OpenCL.
# Korzysta z biblioteki PyOpenCL.
# Aktualnie wąskim gardłem użytkowania OpenCL na GPU jest ilość transferów z/do GPU,
# dlatego też małe zestawy danych liczone są na procesorze głównym.
# Można zoptymalizować użycie GPU (zmniejszyć ilość zapytań na jednostkę czasu)
# poprzez wysłanie jednego zapytania, w którym znajdą się informacje co wykonać i dla jakich zestawów wierzchołków.
# Wymaga to napisania jednego, głównego kernela OpenCL, który zarządzał będzie pracą GPU w taki sposób, aby
# z danych zestawów wierzchołków przekazanych do GPU, ich pozycji itd generował odpowiedź i zwracał ją tylko raz
# na każde odświeżenie hipergrafu.
class OCL:
    ENABLE_OPENCL = DEFAULT_ENABLE_OPENCL

    prog = None

    ## Metoda, która dla każdego wiersza macierzy zwraca jego n najmniejszych elementów z pominięciem przekątnej.
    @staticmethod
    def get_n_min_elements_indices_for_every_element(nparr, n):
        # rozmiar macierzy we i wy
        shape_out = (nparr.shape[0], min(n, nparr.shape[1]-1))

        # zmienne numpy
        a_np = nparr
        res_np = np.zeros(shape_out).astype(np.float32)

        shape_in_np = np.array(a_np.shape).astype(np.float32)
        shape_out_np = np.array(res_np.shape).astype(np.float32)

        # if OCL.ENABLE_OPENCL and cl:
        OCL.run_with_ocl(
            np_in_list=[shape_out_np, a_np],
            np_out_list=[res_np],
            shape=(shape_out[0],1),
            #oclfun=OCL.prog['prog'].opencl_kernel_n_closest_elements_array
            oclfun=OCL.prog['opencl_kernel_n_closest_elements_array']
        )

        return res_np

    ## Inicjalizacja kerneli OpenCL.
    # @dot
    # digraph example {
    #     node [ shape="rectangle"];
    #     init_ok [ shape="diamond"];
    #     start,koniec [ shape="ellipse"];
    #     start -> init_kernel;
    #     init_kernel -> init_ok;
    #     init_ok -> koniec [ label="tak" ];
    #     init_ok -> ustaw_fallback [ label="nie" ];
    #     ustaw_fallback -> koniec;
    # }
    # @enddot
    @staticmethod
    def init_kernel():

        OCL.prog = dict()

        if OCL.ENABLE_OPENCL:
            print("OCL: INIT KERNEL")
            
            try:
                import pyopencl as cl

                kernels_filename = 'OpenClKernels.cl'
                with open(kernels_filename, 'r') as f:
                    OCL.prog['code'] = f.read()

                # konfiguracja
                OCL.prog['ctx'] = cl.create_some_context()
                OCL.prog['queue'] = cl.CommandQueue(OCL.prog['ctx'])
                OCL.prog['mf'] = cl.mem_flags

                OCL.prog['prog'] = cl.Program(OCL.prog['ctx'], OCL.prog['code']).build()

                OCL.prog['opencl_kernel_scalar_dist'] = OCL.prog['prog'].opencl_kernel_scalar_dist
                OCL.prog['opencl_kernel_vector_dist'] = OCL.prog['prog'].opencl_kernel_vector_dist
                OCL.prog['opencl_kernel_vector_dir'] = OCL.prog['prog'].opencl_kernel_vector_dir
                OCL.prog['opencl_kernel_vector_force'] = OCL.prog['prog'].opencl_kernel_vector_force
                OCL.prog['opencl_kernel_vector_vector_force'] = OCL.prog['prog'].opencl_kernel_vector_vector_force
                OCL.prog['opencl_kernel_n_closest_elements_array'] = OCL.prog['prog'].opencl_kernel_n_closest_elements_array
                OCL.prog['opencl_kernel_mat_line_sum_to_vec'] = OCL.prog['prog'].opencl_kernel_mat_line_sum_to_vec
                OCL.prog['opencl_kernel_a_to_p'] = OCL.prog['prog'].opencl_kernel_a_to_p

            except Exception as e:
                print('Nie udalo sie zainicjowac kerneli: \n{}\n\n'.format(e))

                OCL.ENABLE_OPENCL = False

    ## Metoda wspomagająca pisanie innych funkcji przy pomocy PyOpenCL.
    @staticmethod
    def run_with_ocl(np_in_list, np_out_list, shape, oclfun, preset_outbuf=False, rw_outbuf=False):
        assert(DEFAULT_ENABLE_OPENCL == True and OCL.ENABLE_OPENCL == True)
        t_start = time.time()

        buf_in_list = [
            cl.Buffer(
                OCL.prog['ctx'],
                OCL.prog['mf'].READ_ONLY | OCL.prog['mf'].COPY_HOST_PTR,
                size=np_in.nbytes,
                hostbuf=np_in
            ) for np_in in np_in_list ]

        if preset_outbuf:
            buf_out_list = [
                cl.Buffer(
                    OCL.prog['ctx'],
                    (OCL.prog['mf'].READ_WRITE if rw_outbuf else OCL.prog['mf'].WRITE_ONLY) | OCL.prog['mf'].USE_HOST_PTR,
                    size=np_out.nbytes,
                    hostbuf=np_out
                ) for np_out in np_out_list ]

            for i, outbuf in enumerate(buf_out_list):
                cl.enqueue_write_buffer(
                    OCL.prog['queue'],
                    outbuf,
                    np_out_list[i]
                )
        else:
            buf_out_list = [
                cl.Buffer(
                    OCL.prog['ctx'],
                    (OCL.prog['mf'].READ_WRITE if rw_outbuf else OCL.prog['mf'].WRITE_ONLY) | OCL.prog['mf'].ALLOC_HOST_PTR,
                    size=np_out.nbytes
                ) for np_out in np_out_list ]

        runevent = oclfun(OCL.prog['queue'], shape,  None, *(buf_in_list+buf_out_list))  # queue, globalSize, localSize, *buffers)
        runevent.wait()
        
        for buf_from, np_to in  zip(buf_out_list, np_out_list):
            # cl.enqueue_copy(OCL.prog['queue'], np_to, buf_from)

            cl.enqueue_read_buffer(
                OCL.prog['queue'],
                buf_from,
                np_to
            )

            # np_to1, e = cl.enqueue_map_buffer(
            #     OCL.prog['queue'],
            #     buf_from,
            #     cl.map_flags.READ,
            #     0,
            #     np_to.shape,
            #     np_to.dtype,
            #     "C"
            # )
            # np_to += np_to1

        OCL.prog['queue'].finish()

        t_end = time.time()
        dt_real = t_end - t_start

        #print('{0}: {1:.4f}s na wykonanie \n\t{2}\t->\t{3},\n\tmax {4:.2f} 1/s. \n'.format(
        #    __name__,
        #    dt_real,
        #    [a.shape for a in np_in_list],
        #    [a.shape for a in np_out_list],
        #    1 / dt_real))

        # print('{0}: {1:.4f}s \n\t{3}\t->\t{4},\n\tmax {5:.2f} 1/s. \n'.format(
        #     __name__,
        #     dt_real,
        #     oclfun,
        #     [a.shape for a in np_in_list],
        #     [a.shape for a in np_out_list],
        #     1 / dt_real))

    ## Metoda informująca, czy kernele OpenCL zostały zainicjowane.
    @staticmethod
    def is_initialized():
        return not OCL.ENABLE_OPENCL \
               or ( OCL.prog is not None
                   and (
                       'prog' in OCL.prog.keys()
                       or 'fallback' in OCL.prog.keys()
                   )
               )

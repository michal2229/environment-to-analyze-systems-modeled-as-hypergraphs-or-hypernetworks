/**
 * \file OpenClKernels.cl
 * \module OpenClKernels
 */


/**
 * Funkcja obliczająca skalar odległości pomiędzy dwoma punktami.
 */
float dist_s(float ax, float ay, float bx, float by) {
    return sqrt((bx-ax)*(bx-ax) + (by-ay)*(by-ay));
}



/**
 *  Funkcja obliczająca macierz skalarów odległości pomiędzy danymi punktami.
 */
__kernel void opencl_kernel_scalar_dist(
    __global const float *read_buffer, // bufor wejsciowy
    __global float *write_buffer      // bufor wyjsciowy
) {
    int x = get_global_id(0);
    int y = get_global_id(1);
    
    int xmax = get_global_size(0); //n
    //int ymax = get_global_size(1); //n

    float a[2] = {read_buffer[2*x + 0], read_buffer[2*x + 1]};
    float b[2] = {read_buffer[2*y + 0], read_buffer[2*y + 1]};

    write_buffer[xmax*x + y] = dist_s(a[0],a[1],b[0],b[1]);
}



/**
 *  Funkcja obliczająca macierz wektorów odległości pomiędzy danymi punktami.
 */
__kernel void opencl_kernel_vector_dist(
    __global const float *read_buffer, // bufor wejsciowy
    __global float *write_buffer      // bufor wyjsciowy
) {

    int x = get_global_id(0);
    int y = get_global_id(1);
    //int z = get_global_id(2);

    int maxbx = get_global_size(0); //n
    int maxby = get_global_size(1); //n
    int maxbz = 2; //2

    float a[2] = {read_buffer[2*x + 0], read_buffer[2*x + 1]};
    float b[2] = {read_buffer[2*y + 0], read_buffer[2*y + 1]};
    

    write_buffer[maxbz*maxby*x + maxbz*y + 0] = b[0]-a[0];
    write_buffer[maxbz*maxby*x + maxbz*y + 1] = b[1]-a[1];
}



/**
 *  Funkcja obliczająca macierz wektorów kierunkowych pomiędzy danymi punktami.
 */
__kernel void opencl_kernel_vector_dir(
    __global const float *read_buffer, // bufor wejsciowy
    __global float *write_buffer      // bufor wyjsciowy
) {
    int x = get_global_id(0);
    int y = get_global_id(1);
    //int z = get_global_id(2);

    int maxbx = get_global_size(0); //n
    int maxby = get_global_size(1); //n
    int maxbz = 2; //2

    float a[2] = {read_buffer[2*x + 0], read_buffer[2*x + 1]};
    float b[2] = {read_buffer[2*y + 0], read_buffer[2*y + 1]};
    
    float d = dist_s(a[0],a[1],b[0],b[1]);
    
    if (d == 0.0f) {
        write_buffer[maxbz*maxby*x + maxbz*y + 0] = sqrt(2.0f)/2.0f;
        write_buffer[maxbz*maxby*x + maxbz*y + 1] = sqrt(2.0f)/2.0f;
    } else {
        write_buffer[maxbz*maxby*x + maxbz*y + 0] = (b[0]-a[0])/d;
        write_buffer[maxbz*maxby*x + maxbz*y + 1] = (b[1]-a[1])/d;
    }
}



/**
 *  Funkcja obliczająca indeksy n najmniejszych elementów dla każdego wiersza macierzy.
 */
__kernel void opencl_kernel_n_closest_elements_array(
    __global const float *shape_out, // tablica, ktorej elementy oznaczaja kolejne wymiary bufora wyjsciowego
    __global const float *read_buffer, // bufor wejsciowy
    __global float *write_buffer      // bufor wyjsciowy
) {
    int x = get_global_id(0);
    int xmax = get_global_size(0);
    
    int n = shape_out[1];
    
    float lastminval = -1;
    float a = 0;

    // dla kazdej liczy na wyjscie
    for (int y = 0; y<n; y++) {
        float currminval = -1;
        int currminy = -1;
    
        // przeczesywanie tablicy
        for (int i=0; i<xmax; i++) {
            float e = read_buffer[xmax*x + i];
        
            if (e > 0 && e > lastminval) {
                if (currminy < 0 ) {
                    currminval = e;
                    currminy = i;
                }
            

                if (e < currminval) {
                    currminval = e;
                    currminy = i;
                }
            }
        }
        
        write_buffer[n*x + y] = currminy;
        lastminval = currminval;
    }
}







/**
 *  Funkcja obliczająca macierz sil pomiędzy danymi punktami.
 */
__kernel void opencl_kernel_vector_force(
    __global const float *pos_vec_n_x_2,
    __global const float *mass_vec_n_x_2,
    __global const float *rad_vec_n_x_2,
    __global const float *coeffs_vec_3_x_1,
    __global float *force_mat_n_x_n_x_2
    //__global __read_write float *vec_n_x_2
) {
    int x = get_global_id(0);
    int y = get_global_id(1);
    //int z = get_global_id(2);

    int maxbx = get_global_size(0); //n
    int maxby = get_global_size(1); //n
    int maxbz = 2; //2

    float a[2] = {pos_vec_n_x_2[2*x + 0], pos_vec_n_x_2[2*x + 1]};
    float b[2] = {pos_vec_n_x_2[2*y + 0], pos_vec_n_x_2[2*y + 1]};
     
    float m1 = mass_vec_n_x_2[x]; 
    float m2 = mass_vec_n_x_2[y];
    
    float r1 = rad_vec_n_x_2[x];
    float r2 = rad_vec_n_x_2[y];  
    
    float u_mul = coeffs_vec_3_x_1[0];
    float k     = coeffs_vec_3_x_1[1];
    float grav  = coeffs_vec_3_x_1[2];
    
    float ds    = dist_s(a[0],a[1],b[0],b[1]);
    float dv[2] = {b[0]-a[0], b[1]-a[1]};
    float vv[2];

    if (ds == 0.0f) {
        vv[0] = sqrt(2.0f)/2.0f; vv[1] = sqrt(2.0f)/2.0f;
    } else {
        vv[0] = dv[0]/ds; vv[1] = dv[1]/ds;
    }
    
    float r1plusr2 = r1 + r2; 
        
    float u = (r1plusr2 + 100) * u_mul; // u_mul, r1plusr2
    float m1xm2 = m1*m2; // m1, m2    
        
    float fs = k * (ds - u); // k, u, ds
    
    float nds = ds;
    if (nds < 32) nds = 32;
    
    float fg = (grav * m1xm2) / (nds*nds); // grav, m1xm2, nds
        
    float fsv[2] = {fs*vv[0], fs*vv[1]}; // fs * vv
    float fgv[2] = {fg*vv[0], fg*vv[1]}; // fg * vv

    float fv[2] = {fsv[0]+fgv[0], fsv[1]+fgv[1]}; // fsv+fgv
        
       
    if (x == y) {
        force_mat_n_x_n_x_2[maxbz*maxby*x + maxbz*y + 0] = 0.0f;
        force_mat_n_x_n_x_2[maxbz*maxby*x + maxbz*y + 1] = 0.0f;
    } else {
        force_mat_n_x_n_x_2[maxbz*maxby*x + maxbz*y + 0] = fv[0];
        force_mat_n_x_n_x_2[maxbz*maxby*x + maxbz*y + 1] = fv[1];
    }
}






/**
 *  Funkcja obliczająca sumę dla każdego wiersza macierzy.
 */
__kernel void opencl_kernel_mat_line_sum_to_vec(
    __global const float *mat_n_x_n_x_2,
    __global float *vec_n_x_2      
) {
    int y = get_global_id(0);
    int z = get_global_id(1);

    int maxby = get_global_size(0); //n
    int maxbz = get_global_size(1); //2
    int maxbx = maxby;
    
    vec_n_x_2[maxbz*y + z] = 0.0f;

    for (int x = 0; x < maxbx; x++) {
        float a = mat_n_x_n_x_2[maxbz*maxby*y + maxbz*x + z];
        
        vec_n_x_2[maxbz*y + z]+= a;
    }
}






/**
 *  Funkcja obliczająca macierz P z macierzy A.
 */
__kernel void opencl_kernel_a_to_p(
    __global const int *A_nm,
    __global const int *hbtype_m,
    __global int *kmax,
    __global int *P_nn
) {

    int n = get_global_size(0);
    int m = kmax[0];

    // P(i, j) += 1 gdy A(i, k) != 0 i A(j, k) >= A(i, k)
    int i = get_global_id(0); // 0..n-1 // start
    int j = get_global_id(1); // 0..n-1 // koniec
    int k = 0; // 0..m-1
    
    int l = 0;
    int s; // suma kolumny kolumny
    int c; // licznik petlu sumujacej kolumne
    
    int amik = 0;
    int amjk = 0;
    
    int hbtype = 0;
    
    const int HB_HYPEREDGE = 0;
    const int HB_HYPERARC  = 1;
    const int HB_HYPERLOOP = 2;
    
    
    
    for (k=0; k<m; k++) {
        /*
        s = 0;
        
        for (c=0; c<n; c++) { // nieefektywne, zawiesza kernel
            s += A_nm[m*c + k];
        }
        */
        
        hbtype = hbtype_m[k]; // lepsza opcja
        
        amik = A_nm[m*i + k];
        amjk = A_nm[m*j + k];
    
        if (
            (amik > 0) && 
            (
                (amik < amjk) || 
                (
                    (amik == amjk) && 
                    (amik == 1) && (i != j) && (hbtype == HB_HYPEREDGE)
                ) ||  
                (
                    (amik == amjk) && 
                    (amik >= 1) && (i == j) && (hbtype == HB_HYPERLOOP)
                )
            )
        ) { 
            l+=1; 
        }
    }
    
    P_nn[n*i + j] = l; //10*i + j;

    
}

//for (int y = 0; y<maxby; y++) 
//	s += A[maxby*x + y];
//
//B[x] = s;





/**
 *  Funkcja obliczająca wektor sily dla kazdego punktu.
 */
__kernel void opencl_kernel_vector_vector_force(
    __global const float *pos_vec_n_x_2,
    __global const float *mass_vec_n_x_2,
    __global const float *rad_vec_n_x_2,
    __global const float *coeffs_vec_3_x_1,
    //__global float *force_mat_n_x_n_x_2,
    __global float *vec_n_x_2
) {
    int x = 0;
    int y = get_global_id(0);
    //int z = get_global_id(2);
    int ly = get_local_id(0);

    int maxby = get_global_size(0); //n
    int maxlby = get_local_size(0);
    int maxbx = maxby; //n
    int maxbz = 2; //2
    
    float fx = 0.f;
    float fy = 0.f;
        
    float u_mul = coeffs_vec_3_x_1[0];
    float k     = coeffs_vec_3_x_1[1];
    float grav  = coeffs_vec_3_x_1[2];
    
    float b[2] = {pos_vec_n_x_2[2*y + 0], pos_vec_n_x_2[2*y + 1]};
    float m2 = mass_vec_n_x_2[y];
    float r2 = rad_vec_n_x_2[y];  
   
    
    float a[2];
    float m1; 
    float r1;
    float ds;
    float dv[2];
    float vv[2];
    float r1plusr2; 
    float u; // u_mul, r1plusr2
    float m1xm2; // m1, m2  
    float fs; // k, u, ds
    float nds;
    float fg; // grav, m1xm2, nds
    float fsv[2]; // fs * vv
    float fgv[2]; // fg * vv
    float fv[2]; // fsv+fgv
    
    float2 p;
        
    for (x=0; x<maxbx; x++) {

        // poczatek zapytan do pamieci globalnej
        p = (float2) (pos_vec_n_x_2[2*x + 0], pos_vec_n_x_2[2*x + 1]);
        a[0] = p.x; a[1] = p.y;
        
        m1 = mass_vec_n_x_2[x]; 
        r1 = rad_vec_n_x_2[x];
        // koniec zapytan do pamieci globalnej
        
        ds    = dist_s(a[0],a[1],b[0],b[1]);
        
        dv[0] = b[0]-a[0]; 
        dv[1] = b[1]-a[1];        

        if (ds == 0.0f) {
            vv[0] = sqrt(2.0f)/2.0f; 
            vv[1] = sqrt(2.0f)/2.0f;
        } else {
            vv[0] = dv[0]/ds; 
            vv[1] = dv[1]/ds;
        }
        
        r1plusr2 = r1 + r2; 
            
        u = (r1plusr2 + 100) * u_mul; // u_mul, r1plusr2
        m1xm2 = m1*m2; // m1, m2    
            
        fs = k * (ds - u); // k, u, ds
        
        nds = ds;
        if (nds < 32) nds = 32;
        
        fg = (grav * m1xm2) / (nds*nds); // grav, m1xm2, nds
            
        fsv[0] = fs*vv[0]; 
        fsv[1] = fs*vv[1]; // fs * vv
        
        fgv[0]=fg*vv[0]; 
        fgv[1]=fg*vv[1]; // fg * vv

        fv[0] = fsv[0]+fgv[0];
        fv[1] = fsv[1]+fgv[1]; // fsv+fgv
            
        if (x != y) {            
            fx += fv[0];
            fy += fv[1];
        }
    }
    
    vec_n_x_2[maxbz*y + 0] = -fx;
    vec_n_x_2[maxbz*y + 1] = -fy;
}

















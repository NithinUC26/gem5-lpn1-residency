/* Sensor-node kernels for the LPN-1 study (integer only, no C library). */
#ifndef NODE_H
#define NODE_H
#ifndef FRAMES
#define FRAMES 20          /* number of 256-sample frames processed */
#endif
#define NS 256             /* samples per frame */
#define TAPS 16            /* FIR taps */
#ifndef KERNEL
#define KERNEL 4           /* 1 = FIR, 2 = feature, 3 = CRC, 4 = full pipeline */
#endif
unsigned run(void);
#endif

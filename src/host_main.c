/* Host-side reference: same kernels, built natively, prints the expected checksum. */
#include <stdio.h>
#include "node.h"
int main(void) { printf("checksum %08x\n", run()); return 0; }

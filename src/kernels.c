#include "node.h"

/* 16-tap low-pass FIR coefficients, Q15 */
static const short h[TAPS] = {-137, -316, -195, 664, 2100, 4064, 5876, 7054,
                              7054, 5876, 4064, 2100, 664, -195, -316, -137};
static short x[NS + TAPS];
static short y[NS];
static unsigned lcg_state = 12345u;

static unsigned lcg(void) {
    lcg_state = lcg_state * 1664525u + 1013904223u;
    return lcg_state;
}

/* Stand-in for reading a sensor: a triangle wave plus noise. */
static void sample_frame(int frame) {
    for (int i = 0; i < NS + TAPS; i++) {
        int tri = ((i * 37 + frame * 11) & 255) - 128;
        int noise = (int)((lcg() >> 20) & 63) - 32;
        x[i] = (short)(tri * 16 + noise);
    }
}

static void fir(void) {
    for (int n = 0; n < NS; n++) {
        int acc = 0;
        for (int k = 0; k < TAPS; k++) acc += h[k] * x[n + TAPS - 1 - k];
        y[n] = (short)(acc >> 15);
    }
}

/* Moving average (window 16), threshold crossings, min, max, mean |deviation|. */
static unsigned feature(const short *s) {
    int sum = 0, minv = 32767, maxv = -32768, cross = 0, dev = 0;
    for (int i = 0; i < NS; i++) {
        sum += s[i];
        if (i >= 16) sum -= s[i - 16];
        int avg = sum >> 4;
        int d = s[i] - avg;
        if (d < 0) d = -d;
        if (d > 40) cross++;
        dev += d;
        if (s[i] < minv) minv = s[i];
        if (s[i] > maxv) maxv = s[i];
    }
    return (unsigned)cross * 65537u + (unsigned)(maxv - minv) * 31u + (unsigned)dev;
}

/* CRC-16/CCITT-FALSE over the 512-byte packet. */
static unsigned crc16(const unsigned char *p, int len) {
    unsigned crc = 0xFFFFu;
    for (int i = 0; i < len; i++) {
        crc ^= (unsigned)p[i] << 8;
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x8000u) ? ((crc << 1) ^ 0x1021u) & 0xFFFFu : (crc << 1) & 0xFFFFu;
    }
    return crc;
}

unsigned run(void) {
    unsigned chk = 0;
    for (int f = 0; f < FRAMES; f++) {
        sample_frame(f);
#if KERNEL == 1
        fir();
        for (int i = 0; i < NS; i++) chk = chk * 31u + (unsigned)(y[i] & 0xFFFF);
#elif KERNEL == 2
        chk = chk * 31u + feature(&x[TAPS]);
#elif KERNEL == 3
        chk = chk * 31u + crc16((const unsigned char *)&x[TAPS], NS * 2);
#else
        fir();
        chk = chk * 31u + feature(y);
        chk = chk * 31u + crc16((const unsigned char *)y, NS * 2);
#endif
    }
    return chk;
}

#include <stdio.h>

#define MAX (1 << 18) /* 262144 */

int hocchann[MAX * 2 - 1];

void init(const int* data, int num) {
	int i;
	for (i = 0; i < MAX; i++) {
		hocchann[MAX - 1 + i] = i < num ? data[i] : 0;
	}
	for (i = MAX - 1 - 1; i >= 0; i--) {
		int c1 = hocchann[i * 2 + 1];
		int c2 = hocchann[i * 2 + 2];
		hocchann[i] = c1 > c2 ? c1 : c2;
	}
}

int get_i(int idx, int qmin, int qmax, int smin, int smax) {
	if (qmax <= smin || smax <= qmin) return 0;
	else if (qmin <= smin && smax <= qmax) return hocchann[idx];
	else {
		int smid = smin + (smax - smin) / 2;
		int l = get_i(idx * 2 + 1, qmin, qmax, smin, smid);
		int r = get_i(idx * 2 + 2, qmin, qmax, smid, smax);
		return l > r ? l : r;
	}
}

int get(int min, int max) {
	return min < max ? get_i(0, min, max, 0, MAX) : 0;
}

int N, K;
int a[271828];

char nokosu[271828];

int main(void) {
	int i;
	int start, left;
	if (scanf("%d%d", &N, &K) != 2) return 1;
	for (i = 0; i < N; i++) {
		if (scanf("%d", &a[i]) != 1) return 1;
	}
	init(a, N);
	start = 0;
	left = K;
	while (start + left < N) {
		int max = get(start, start + left + 1);
		int no = 0, yes = left + 1;
		while (no + 1 < yes) {
			int mid = no + (yes - no) / 2;
			if (get(start, start + mid) == max) yes = mid; else no = mid;
		}
		printf("%d", max);
		start += yes;
		left -= yes - 1;
	}
	putchar('\n');
	return 0;
}


#include<stdio.h>
int main() {
    int x, k;

    if(scanf("%d", &x) == 1) {
        k = 360 / x;
        printf("%d", k);
    }
    return 0;
}
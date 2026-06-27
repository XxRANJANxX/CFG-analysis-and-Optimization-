int main() {
    int i = 2;
    int j = 100;
    int k = 50;  /* DEAD: Overwritten before it is ever used */
    
    if (i < 5) {
        k = i + 1;
    } else {
        k = j - 1;
    }
    
    return k;
}
int main() {
    int sum = 0;
    int i = 0;
    int dead_val = 999; /* DEAD: Never used */
    
    while (i < 10) {
        int temp = i * 2; /* DEAD: Calculated but never used */
        sum = sum + i;
        i = i + 1;
    }
    
    return sum;
}
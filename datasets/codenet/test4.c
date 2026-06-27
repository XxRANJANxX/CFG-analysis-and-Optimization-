int main() {
    int sum = 0;
    int i = 0;
    int temp = 999; /* DEAD: Never used */
    
    while (i < 10) {
        sum = sum + i;
        i = i + 1;
    }
    
    return sum;
}
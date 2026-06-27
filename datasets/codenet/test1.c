int main() {
    int a = 10;
    int b = 20;      /* DEAD: Never used */
    int c = a + 5;
    int d = c * 10;  /* DEAD: Assigned but never returned or used */
    
    return c;
}
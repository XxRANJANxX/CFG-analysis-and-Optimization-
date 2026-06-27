int main() {
    int x = 5;
    int y = 10;
    
    return x + y;
    
    /* UNREACHABLE: Graph traversal should never reach here */
    int z = 100;
    x = z + 5;
    return x;
}
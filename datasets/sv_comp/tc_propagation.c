int main() {
    int manan = 42;
    
    // TA should see this turn into: int aryan = 42;
    int aryan = manan;    
    
    // TA should see this turn into: int total = 42 + 8;
    // (And if Folding runs after, it becomes 50)
    int total = aryan + 8; 
    
    return total;
}
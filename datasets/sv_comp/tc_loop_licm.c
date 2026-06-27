int main() {
    int i = 0;
    int result = 0;
    int ammar = 10;
    
    while (i < 100) {
        // LICM CANDIDATE: 'ammar * 5' never changes inside this loop!
        // The optimizer should suggest moving 'int invariant = ammar * 5;' 
        // to BEFORE the while loop starts.
        int invariant = ammar * 5; 
        
        result = result + invariant;
        i = i + 1;
    }
    
    return result;
}
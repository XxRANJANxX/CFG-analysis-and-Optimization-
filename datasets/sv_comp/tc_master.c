int main() {
    int base = 50 + 50;     // Folds to 100
    int offset = base;      // Propagates 100
    int dead_weight = 999;  // DCE drops this completely
    int i = 0;
    int result = 0;
    
    while (i < 5) {
        int temp = i * 2;   // DCE drops this (calculated but not used)
        
        if (offset == 100) {
            result = result + 1;
        } else {
            result = result - 1;
        }
        i = i + 1;
    }
    
    return result;
    
    int secret = 777;       // Unreachable Code Removal drops this
    return secret;
}
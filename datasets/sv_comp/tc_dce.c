int main() {
    int x = 5;
    
    // DEAD: Assigned but never used anywhere. Should vanish.
    int y = 10;           
    
    int z = x * 2;
    
    // DEAD: Uses 'z', but 'unused' itself is never returned or passed. Should vanish.
    int unused = z + 1;   
    
    return z;
}
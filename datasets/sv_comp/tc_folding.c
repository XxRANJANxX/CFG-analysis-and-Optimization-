int main() {
    // we should see this merge into: int a = 30;
    int a = 10 + 20;      
    
    // we should see this merge into: int b = 15;
    int b = (50 / 5) + 5; 
    
    return a + b;
}
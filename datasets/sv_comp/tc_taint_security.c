int main() {
    int user_input;
    int safe_val = 100;
    
    // SOURCE: 'user_input' is now marked as TAINTED
    scanf("%d", &user_input); 
    
    // TAINT PROPAGATION: 'dangerous_var' is now TAINTED because it uses 'user_input'
    int dangerous_var = user_input + 5; 
    
    // SINK: The scanner should throw a WARNING here because tainted data hits a sink
    printf("Result: %d", dangerous_var);
    
    // SAFE: This should NOT throw a warning because 'safe_val' was never tainted
    printf("Safe output: %d", safe_val);
    
    return 0;
}
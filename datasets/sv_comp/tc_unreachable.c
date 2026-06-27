int main() {
    int status = 1;
    return status;
    
    // UNREACHABLE: Everything below here must be completely dropped from the CFG.
    int ghost_var = 404;
    status = status + ghost_var;
    return status;
}
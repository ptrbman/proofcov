void main() {
    int a = 1;
    int b = 0;
    int x = 0;
    int y = 0;
    if (a) { x = 1; } if (b) { y = 1; }
    assert(x == 1);
}

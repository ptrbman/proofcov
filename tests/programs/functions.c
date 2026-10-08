int g;

int twice_g() {
    int t;
    t = g + g;
    return t;
}

int is_big() {
    return g > 10;
}

void main() {
    int x;
    g = 6;
    x = twice_g();
    if (is_big()) {
        x = 0;
    }
    assert(x == 12);
}

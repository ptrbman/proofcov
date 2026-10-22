int g;

int check() {
    int t;
    t = g + 1;
    return t > 0;
}

void main() {
    int x;
    g = 0;
    x = 0;
    if (g > 5 && check()) {
        x = 1;
    }
    assert(x == 0);
}

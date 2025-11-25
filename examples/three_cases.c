void main() {

    int x;
    int y;
    int z;

    x = 12;
    y = 13;
    z = 14;

    int n = 14;
    int found = 0;

    if (n == x) {
        found = 1;
    }

    if (n == y) {
        found = 1;
    }

    if (n == z) {
        found = 1;
    }

    assert(found == 1);
}
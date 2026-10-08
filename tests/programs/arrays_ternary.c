/* Thresholds,
   indexed by level */
#define LOW 400
int thresh[3];

void main() {
    int level;
    int limit;
    int climb;
    thresh[0] = LOW;
    thresh[1] = 500;
    thresh[2] = 640;
    level = 1;
    climb = 0;
    limit = climb ? thresh[level] + 100 : thresh[level];
    assert(limit == 500);
}

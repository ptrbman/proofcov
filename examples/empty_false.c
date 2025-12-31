#include <assert.h>

void main() {
    int validation_passed = 0;

    if (1 > 0) {
        validation_passed = 1;

        if (validation_passed == 1) {
            int a = 0;
            a = a;
        }
    }

    assert(validation_passed == 1);
}

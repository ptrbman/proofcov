#include <assert.h>
#include <stdio.h>

void main() {

    int x;
    int y;
    int z;

    int n = 12;
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

    char vowels[5];
    vowels[0] = 'a';
    vowels[1] = 'e';
    vowels[2] = 'i';
    vowels[3] = 'o';
    vowels[4] = 'u';
    int vowel_count = 5;

    char* text = "aa";
    int len = 2;

    int vowel_found = 0;

    for (int i = 0; i < len; i++) {
        char c = text[i];
        // printf("Character: %c\n", c);
        for (int j = 0; j < vowel_count; j++) {
            // printf(" Comparing with vowel: %c\n", vowels[j]);
            if (c == vowels[j]) {
                // printf("  Vowel matched: %c\n", c);
                vowel_found = vowel_found + 1;
            }
        }
    }

    // printf("Total vowels found: %d\n", vowel_found);

    __CPROVER_assert(vowel_found == 2, "vowel count check");
}
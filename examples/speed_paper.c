#include<assert.h>

void main(){
int temp;
int speed;
temp = 28;
speed = 3;

if (temp > 25) {
    temp = temp + 1;
    if (speed > 5) {
        speed = 5;
        temp = temp - 2;
    } else {
        speed = speed + 1;
        temp = temp - 1;
    }
    temp = temp - 1;
} else {
    speed = speed - 1;
    temp = temp + 1;
}
temp = temp - 1;
assert(speed > 0);
}

int main() {
    int leftSwitch;
    int rightSwitch;
    leftSwitch = 1;
    rightSwitch = 1;

    int lightOn = 0;

    if (leftSwitch == 1 || rightSwitch == 1) {
        lightOn = 1;
    }

    assert(lightOn == 1);
}
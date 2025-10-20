void main() {
	int a = 2;
	int b = 4;
	if (a > 0) {
		a = a + 3;
		if (a > 4) {
			b = b + 2;
		} else {
			a = a / 3;
		}
	} else {
		b = b - 2;
	}
	a = a + b;
	assert(b == 6);
}
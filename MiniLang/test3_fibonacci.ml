n = 8;
a = 0;
b = 1;
i = 0;

print(a);
print(b);

while (i < n - 2) {
    temp = a + b;
    print(temp);
    a = b;
    b = temp;
    i = i + 1;
}
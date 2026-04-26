n = 5;
i = 0;
sum = 0;

while (i < n) {
    sum = sum + i;
    i = i + 1;
}

if (sum == 10) {
    print(999);
}

if (sum != 10) {
    print(404);
}

print(sum);
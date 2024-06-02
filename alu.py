class ALU:
    def __init__(self):
        self.a = 0
        self.b = 0

        self.result = None

        self.zero = False
        self.negative = False

    def add(self):
        self.result = self.a + self.b
        self.zero = self.result == 0
        self.negative = self.result < 0

    def sub(self):
        self.result = self.a - self.b
        self.zero = self.result == 0
        self.negative = self.result < 0

    def mul(self):
        self.result = self.a * self.b
        self.zero = self.result == 0
        self.negative = self.result < 0

    def div(self):
        self.result = self.a // self.b
        self.zero = self.result == 0
        self.negative = self.result < 0

    def mod(self):
        self.result = self.a % self.b
        self.zero = self.result == 0
        self.negative = self.result < 0

    def compare(self):
        if self.a > self.b:
            self.result = 1
        elif self.a < self.b:
            self.result = -1
        else:
            self.result = 0

        self.zero = self.result == 0
        self.negative = self.result < 0

    def equals(self):
        if self.a == self.b:
            self.result = -1
        else:
            self.result = 0
        self.zero = self.result == 0
        self.negative = self.result < 0

    def less(self):
        if self.a < self.b:
            self.result = -1
        else:
            self.result = 0
        self.zero = self.result == 0
        self.negative = self.result < 0

    def greater(self):
        if self.a > self.b:
            self.result = -1
        else:
            self.result = 0
        self.zero = self.result == 0
        self.negative = self.result < 0

    def not_a(self):
        self.result = int(not self.a)

        self.zero = self.result == 0
        self.negative = self.result < 0

    def not_b(self):
        self.result = int(not self.b)

        self.zero = self.result == 0
        self.negative = self.result < 0

    def __str__(self):
        return f'ALU: result={self.result}, zero={self.zero}, negative={self.negative}'

    def __repr__(self):
        return str(self)

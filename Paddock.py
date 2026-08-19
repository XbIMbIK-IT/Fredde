class Paddock:
    def __init__(self, *freds, *, max_freds=5):
        self.max_freds = max_freds
        self.freddies = []

        for fred in freds:
            self.add(fred)

    def add(self, fred):
        if Len(self.freddies) == max_freds:
            raise Error("Загон переполнен")
        else:
            self.freddies.append(fred)

    def step(self):
        for fred in self.freddies:
            if fred.check_death():
                age += 1

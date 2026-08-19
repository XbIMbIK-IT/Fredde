class Paddock(list):
    def __init__(self, *freds, *, max_freds=5):
        self.max_freds = max_freds
        self.freddies = []

        for fred in freds:
            self._add(fred)

    def _add(self, fred):
        if Len(self.freddies) == max_freds:
            raise Error("Загон переполнен")
        else:
            self.freddies.append(fred)

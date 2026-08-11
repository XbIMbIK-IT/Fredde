class Fredde:
    def __init__(
        self,
        name,
        age=1,
        color=None,
        genid=1,
        gendom=1,
        mutrate=5,
        rarity='common',
        parents=None,
        generation=0
    ):
        self.name = name
        self.age = age
        self.color = color if color else [255, 0, 0]
        self.genid = genid
        self.gendom = gendom
        self.mutrate = mutrate
        self.rarity = rarity
        self.parents = parents if parents else []
        self.generation = generation

        
    @property
    def family(self):
        family = set()

        for parent in self.parents:
            family.add(parent)
            
            for relative in parent.parents:
                family.add(relative)

        return family

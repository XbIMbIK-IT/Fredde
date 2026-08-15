freddies = []

class fredde:
    def __init__(
        self,
        alive=True,
        name='No name',
        age=1,
        gender='is', #boy, girl, is (intersex), cf (childfree)
        genid=1,
        gendom=1,
        mutrate=5,
        rarity='common',
        parents=None,
        generation=0,
        # Визуальные параметры
        color=None,
        eye='blue',
        hatAcs='cylinder',
        faceAcs='none',
        eyeAcs='none',
        bodyPattern='basic',
        eyelash=False
    ):
        self.alive = alive
        self.name = name
        self.age = age
        self.color = color if color else [255, 185, 107]
        self.genid = genid
        self.gendom = gendom
        self.mutrate = mutrate
        self.rarity = rarity
        self.parents = parents if parents else []
        self.generation = generation
        self.gender = gender
        self.eye = eye
        self.hatAcs = hatAcs
        self.faceAcs = faceAcs
        self.eyeAcs = eyeAcs
        self.bodyPattern = bodyPattern
        self.eyelash = eyelash

        freddies.append(self)
        
    @property
    def family(self):
        family = set()

        for parent in self.parents:
            family.add(parent)
            
            for relative in parent.parents:
                family.add(relative)

        return family

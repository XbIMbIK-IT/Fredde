import random

with open("NameList.txt", 'r') as f:
    NameList = f.read().splitlines()

RarityList = ['common', 'uncommon', 'rare', 'epic', 'mythic', 'legendary']

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




def is_inbreeding(parent1, parent2):
    family1 = parent1.family
    family2 = parent2.family

    return parent1 in family2 or parent2 in family1 or bool(family1 & family2)

def SEX(parent1, parent2, name):

    if parent1.generation <= parent2.generation:
        babygeneration = parent2.generation + 1
    else:
        babygeneration = parent1.generation + 1
    # Шанс мутации
    MutRate = (parent1.mutrate + parent2.mutrate) / 2

    # Инбридинг
    if is_inbreeding(parent1, parent2):
        if MutRate <= 0:
            MutRate = 13
        else:
            MutRate *= 1.3
    elif random.random() <= 0.4 and parent1.generation == parent2.generation:
        MutRate -= 4

    # Разница поколений
    if parent1.generation != parent2.generation:
        gendif = abs(parent2.generation - parent1.generation)
        MutRate += (gendif * 2)

    # Общая доминантность
    total_dom = parent1.gendom + parent2.gendom
    # GenID
    babygenid = (
        parent1.genid * parent1.gendom +
        parent2.genid * parent2.gendom
    ) / total_dom

    # Цвет
    babycolor = []

    for i in range(3):
        color = (
            parent1.color[i] * parent1.gendom +
            parent2.color[i] * parent2.gendom
        ) / total_dom

        babycolor.append(round(color))

    # Наследование gendom
    parent1_chance = parent1.gendom / total_dom

    if random.random() <= parent1_chance:
        babygendom = parent1.gendom
    else:
        babygendom = parent2.gendom

    # Редкость
    if random.random() <= parent1_chance:
        babyrarity = parent1.rarity
    else:
        babyrarity = parent2.rarity

    # Мутация
    if random.uniform(0, 100) <= MutRate:

        # GenID
        babygenid *= random.uniform(0.8, 1.2)

        # Цвет
        for i in range(3):
            babycolor[i] *= random.uniform(0.8, 1.2)
            babycolor[i] = max(
                0,
                min(255, round(babycolor[i]))
            )

        # Доминантность
        babygendom *= random.uniform(0.8, 1.2)
        babygendom = max(0, min(1, babygendom))

        # Редкость
        rarity_index = RarityList.index(babyrarity)

        if random.random() < 0.5:
            rarity_index += 1
        else:
            rarity_index -= 1

        rarity_index = max(
            0,
            min(len(RarityList) - 1, rarity_index)
        )

        babyrarity = RarityList[rarity_index]

    babygenid = round(babygenid)
    babygendom = round(babygendom, 3)
    MutRate = round(MutRate,1)
    return Fredde(
        name=name,
        color=babycolor,
        genid=babygenid,
        gendom=babygendom,
        mutrate=MutRate,
        rarity=babyrarity,
        parents=[parent1, parent2],
        generation=babygeneration
    )

Ded1 = Fredde(
    'Дедушка',
    color=[255, 20, 0],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare'
)

Babka1 = Fredde(
    'Бабушка',
    color=[40, 0, 200],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common'
)

Ded2 = Fredde(
    'Другой дедушка',
    color=[55, 0, 0],
    genid=-30,
    gendom=0.3,
    mutrate=0,
    rarity='legendary'
)

Babka2 = Fredde(
    'Другая бабушка',
    color=[255, 0, 70],
    genid=-42,
    gendom=0.8,
    mutrate=0,
    rarity='mythic'
)

Fred1 = SEX(Ded1, Babka1, random.choice(NameList))

Fred2 = SEX(Ded2, Babka2, random.choice(NameList))

baby = SEX(Fred1, Fred2, random.choice(NameList))

print(baby.name)
print(baby.generation)
print(baby.genid)
print(baby.gendom)
print(baby.mutrate)
print(baby.color)
print(baby.rarity)

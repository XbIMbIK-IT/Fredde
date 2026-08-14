from fredde import  Fredde

import random

RarityList = ['common', 'uncommon', 'rare', 'epic', 'mythic', 'legendary']
with open("NameList.txt", 'r') as f:
    NameList = f.read().splitlines()
SEX_AGE = 3

def checkranname():
    print(random.choice(NameList))

def TrySex(parent1, parent2):
    if not parent1.alive or not parent2.alive:
        return None

    # CF вообще не участвует
    if parent1.gender == 'cf' or parent2.gender == 'cf':
        return None

    # IS может с кем угодно
    if parent1.gender == 'is' or parent2.gender == 'is':
        pass
    elif parent1.gender == parent2.gender:
        return None

    if parent1.age < SEX_AGE or parent2.age < SEX_AGE:
        return None

    return SEX(parent1, parent2)

def is_inbreeding(parent1, parent2):
    family1 = parent1.family
    family2 = parent2.family

    return parent1 in family2 or parent2 in family1 or bool(family1 & family2)


def SEX(parent1, parent2):

    if parent1.generation <= parent2.generation:
        babygeneration = parent2.generation + 1
    else:
        babygeneration = parent1.generation + 1

    # Общая доминантность
    total_dom = parent1.gendom + parent2.gendom

    # Шанс мутации
    MutRate = mut_chance(parent1, parent2, total_dom)

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
        babygenid *= random.uniform(0.6, 1.4)

        # Цвет
        for i in range(3):
            babycolor[i] *= random.uniform(0.5, 2)
            babycolor[i] = max(
                0,
                min(255, round(babycolor[i]))
            )

        # Доминантность
        babygendom *= random.uniform(0.6, 1.3)
        babygendom = max(0, min(1, babygendom))

        # Редкость
        rarity_index = RarityList.index(babyrarity)

        if random.random() < 0.25:
            rarity_index += 1
        else:
            rarity_index -= 1

        rarity_index = max(
            0,
            min(len(RarityList) - 1, rarity_index)
        )

        babyrarity = RarityList[rarity_index]

    # Пол ребенка
    gender_roll = random.uniform(0, 100)
    if gender_roll < 45:
        babygender = 'boy'
    elif gender_roll < 90:
        babygender = 'girl'
    elif gender_roll < 95:
        babygender = 'cf'
    else:
        babygender = 'is'
    
    babygenid = round(babygenid)
    babygendom = round(babygendom, 3)
    MutRate = round(MutRate,1)
    babyname = random.choice(NameList)
    return Fredde(
        name=babyname,
        color=babycolor,
        genid=babygenid,
        gendom=babygendom,
        mutrate=MutRate,
        rarity=babyrarity,
        parents=[parent1, parent2],
        generation=babygeneration,
        gender=babygender
    )




def mut_chance(parent1, parent2, total_dom):
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

    return MutRate

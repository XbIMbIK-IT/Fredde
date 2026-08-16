from fredde import  Fredde
import random


RarityList = ['common', 'uncommon', 'rare', 'epic', 'mythic', 'legendary']


SEX_AGE = 3

def try_sex(parent1, parent2):
    try:
        if not parent1.alive or not parent2.alive:
            return None, "Один из родителей мёртв"

        if parent1.gender == 'cf' or parent2.gender == 'cf':
            return None, "CF не может размножаться"

        if parent1.gender == 'is' or parent2.gender == 'is':
            pass
        elif parent1.gender == parent2.gender:
            return None, "Одинаковый пол"

        if parent1.age < SEX_AGE or parent2.age < SEX_AGE:
            return None, "Один из родителей слишком молод"

        return sex(parent1, parent2), "Успешно"

    except Exception as e:
        return None, f"Ошибка при размножении: {e}"


def is_inbreeding(parent1, parent2):
    family1 = parent1.family
    family2 = parent2.family

    return parent1 in family2 or parent2 in family1 or bool(family1 & family2)


def sex(parent1, parent2):
    # Общая доминантность
    total_dom = parent1.gendom + parent2.gendom


    # Шанс мутации
    MutRate = mut_chance(parent1, parent2, total_dom)

    is_mutant = random.uniform(0, 100) <= MutRate

    if parent1.generation <= parent2.generation:
        generation = parent2.generation + 1
    else:
        generation = parent1.generation + 1


    # GenID
    genid = (
        parent1.genid * parent1.gendom +
        parent2.genid * parent2.gendom
    ) / total_dom

    genid *= random.uniform(0.6, 1.4)
    genid = round(genid)


    # Цвет
    color = []

    for i in range(3):
        value = (
            parent1.color[i] * parent1.gendom +
            parent2.color[i] * parent2.gendom
        ) / total_dom

        if is_mutant:
            value *= random.uniform(0.5, 2)
            value = max(
                0,
                min(255, round(value[i]))
            )

        color.append(round(value))


    # Доминантность
    parent1_chance = parent1.gendom / total_dom

    if random.random() <= parent1_chance:
        gendom = parent1.gendom
    else:
        gendom = parent2.gendom

    if is_mutant:
        gendom *= random.uniform(0.6, 1.3)
        gendom = max(0, min(1, gendom))

    gendom = round(gendom, 3)


    # Редкость
    if random.random() <= parent1_chance:
        rarity = parent1.rarity
    else:
        rarity = parent2.rarity

    if is_mutant:
        rarity_index = RarityList.index(rarity)

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
        gender = 'boy'
    elif gender_roll < 90:
        gender = 'girl'
    elif gender_roll < 95:
        gender = 'cf'
    else:
        gender = 'is'


    # Реснички
    if gender == 'boy':
        eyelash = False
    elif gender == 'girl':
        eyelash = True
    elif random.random() <= 0.5:
        eyelash = False
    else:
        eyelash = True
    

    return Fredde(
        color=color,
        genid=genid,
        gendom=gendom,
        mutrate=MutRate,
        rarity=rarity,
        parents=[parent1, parent2],
        generation=generation,
        gender=gender,
        eyelash=eyelash
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

    MutRate = round(MutRate,1)

    return MutRate

import const as Const
from itertools import product
from copy import deepcopy
class Model:
    def __init__(self, state=None):
        self.action = None
        self.prev = None
        if state:
            self.materials, self.lots, equipments = state
            self.equipment = [
                dict(zip(['recipe', 'step', 'time', 'down'], equipment))
            for equipment in equipments]
        else:
            self.materials = [0,0,0]
            self.lots = [0,0,0,0,0]
            self.equipment = [
                {
                    "recipe": -1, # recipe or -1
                    "step": -1,
                    "time": 0,
                    "down": False,
                } for _ in range(3)
            ]
    def state(self):
        return (self.materials, self.lots, tuple(map(lambda x: list(x.values()), self.equipment)))
    def copy(self):
        return Model(deepcopy(self.state()))
    # deepcopy(self.state()))
    def print(self):
        names = ['Alpha', 'Beta', 'Gamma']
        for i, obj in enumerate(self.equipment):
            if obj['time'] == 0:
                print(f"Equipment {names[i]} idle, was in recipe {obj['recipe']}")
            elif obj['down']:
                print(f"Equipment {names[i]} down, {obj['time']}h left")
            else:
                print(f"Equipment {names[i]} processing step {obj['step']}, {obj['time']}h left")
        print(f"Lots: {self.lots}")
        print(f"Materials used: {self.materials}")

    def step(self, action):
        # an action is a 3-tuple of (recipe, step)
        new_self = self.copy()
        new_self.prev = self
        new_self.action = action
        just_switched = [False, False, False]
        # step through time
        for i, obj in enumerate(new_self.equipment):
            if obj['time'] == 1: # if just finished
                if obj['down']:
                    new_self.equipment[i]['down'] = False
                    just_switched[i] = True
                else:
                    new_self.lots[obj['step']] += 1
            new_self.equipment[i]['time'] = max(0, obj['time'] - 1)

        for i, (recipe, step) in enumerate(action):
            if recipe == -1:
                # no change in state (i.e. still working or idling)
                if step != -1:
                    raise Exception(f"Invalid action, step must be -1 when recipe -1, found {step}")
                continue

            if step == -1:
                # switching recipe
                if new_self.equipment[i]['time'] != 0:
                    raise Exception(f"Invalid action, machine {i} busy")
                if just_switched[i]:
                    raise Exception(f"Machine {i} just switched, cannot switch again")
                if recipe not in Const.validRecipeforEquipment[i]:
                    raise Exception(f"Invalid action, machine {i} cannot do recipe {recipe}")
                if recipe == new_self.equipment[i]['recipe']:
                    raise Exception(f"New recipe ({recipe}) should be different from old recipe ({new_self.equipment[i]['recipe']}) when step == -1")
                
                new_self.equipment[i]['down'] = True
                new_self.equipment[i]['time'] = Const.downtime[new_self.equipment[i]['recipe']][recipe]
                new_self.equipment[i]['recipe'] =  recipe
                continue

            # Starting new job
            if recipe not in Const.validRecipeforEquipment[i]:
                    raise Exception(f"Invalid action, machine {i} cannot do recipe {recipe}")
            if new_self.equipment[i]['time'] != 0:
                raise Exception(f"Invalid action, machine {i} busy")
            
            if recipe not in Const.validRecipeforStep[step]:
                raise Exception(f"Invalid action, recipe {recipe} cannot do step {step}")
            

            if new_self.equipment[i]['recipe'] != recipe and new_self.equipment[i]['recipe'] != -1:
                # if recipe not in Const.validRecipeforEquipment[i]:
                #     raise Exception(f"Invalid action, machine {i} cannot do recipe {recipe}")

                # new_self.equipment[i]['down'] = True
                # new_self.equipment[i]['time'] = Const.downtime[new_self.equipment[i]['recipe']][recipe]
                # new_self.equipment[i]['recipe'] =  recipe
                # # continue
                raise Exception(f"New recipe ({recipe}) must be the same as old recipe ({new_self.equipment[i]['recipe']}) when step != -1")
            else:
                
                if step != 0:
                    if new_self.lots[step-1] == 0:
                        raise Exception(f"Invalid action, no lot at step {step-1}")
                    new_self.lots[step-1] -= 1
                for material,usage in enumerate(Const.recipeMaterialUse[recipe]):
                    new_self.materials[material] += usage

                new_self.equipment[i]['step'] = step
                new_self.equipment[i]['time'] = Const.time[recipe]
                new_self.equipment[i]['recipe'] = recipe
        return new_self
    def is_valid_action(self, action):
        try:
            return action, self.step(action)
        except Exception:
            return action, False    
    def get_all_possible_actions(self):
        action_space = product(product(list(range(-1,5)), list(range(-1,5))), repeat=3)
        return list(filter(lambda x: x[1], map(self.is_valid_action, action_space)))
            
    def cost(self):
        cost = 0
        for i, x in enumerate(self.materials):
            if x <= 50:
                cost += Const.materialCosts[i][0] * x
            elif x <= 500:
                cost += Const.materialCosts[i][1] * x
            else:
                cost += Const.materialCosts[i][2] * x
        return cost
    
    def revenue(self):
        return self.lots[4] * Const.sellingPrice

    def profit(self):
        return self.revenue() - self.cost()
    def get_plan(self):
        if self.prev == None:
            return []
        return self.prev.get_plan() + [self.action,] 
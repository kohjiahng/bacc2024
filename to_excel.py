import pandas as pd
import const as Const
def plan_to_state_list(plan):
    state_list = []
    # state is a list of ((lot_index, recipe, step) x 3)
    materials = [0,0,0]
    lots = [[],[],[],[],[]]
    lot_num = 0
    equipment = [
        {
            "recipe": -1, # recipe or -1
            "step": -1,
            "time": 0,
            "lot": -1,
            "down": False
        } for i in range(3)
    ]
    
    for index, action in enumerate(plan):
        for i, obj in enumerate(equipment):
            if obj['time'] == 1: # if just finished
                if obj['down']:
                    equipment[i]['down'] = False
                else:
                    lots[obj['step']].append(equipment[i]['lot'])
                    equipment[i]['lot'] = -1
            equipment[i]['time'] = max(0, obj['time'] - 1)

        for i, (recipe, step) in enumerate(action):
            if recipe == -1:
                if step != -1:
                    raise Exception(f"Invalid action, step must be -1 when recipe -1, found {step}")
                continue
            if step == -1:
                if recipe == equipment[i]['recipe']:
                    raise Exception(f"New recipe ({recipe}) should be different from old recipe ({equipment[i]['recipe']}) when step == -1")
                # switching recipe
                equipment[i]['down'] = True
                equipment[i]['time'] = Const.downtime[recipe][equipment[i]['recipe']]
                equipment[i]['recipe'] =  recipe
                continue

            if equipment[i]['time'] != 0:
                raise Exception(f"Invalid action, machine {i} {equipment[i]['time']} busy, {index}")
            if recipe not in Const.validRecipeforEquipment[i]:
                raise Exception(f"Invalid action, machine {i} cannot do recipe {recipe}")
            if recipe not in Const.validRecipeforStep[step]:
                raise Exception(f"Invalid action, recipe {recipe} cannot do step {step}")
            

            if equipment[i]['recipe'] != recipe and equipment[i]['recipe'] != -1:
                # if recipe not in Const.validRecipeforEquipment[i]:
                #     raise Exception(f"Invalid action, machine {i} cannot do recipe {recipe}")

                # equipment[i]['down'] = True
                # equipment[i]['time'] = Const.downtime[equipment[i]['recipe']][recipe]
                # equipment[i]['recipe'] =  recipe
                raise Exception(f"New recipe ({recipe}) must be the same as old recipe ({equipment[i]['recipe']}) when step != -1")
            else:
                if step != 0:
                    if lots[step-1] == []:
                        raise Exception(f"Invalid action, no lot at step {step-1}")
                    used_lot = lots[step-1].pop(0)
                    equipment[i]['lot'] = used_lot
                else:
                    lot_num += 1
                    equipment[i]['lot'] = lot_num
                for material,usage in enumerate(Const.recipeMaterialUse[recipe]):
                    materials[material] += usage

                equipment[i]['step'] = step
                equipment[i]['time'] = Const.time[recipe]
                equipment[i]['recipe'] = recipe

        
        # print(equipment)
        # process equipment to get states
        def process_equipment(obj):
            if obj['down']:
                return ["SWITCH", "SWITCH", "SWITCH"]
            else:
                if obj['lot'] == -1:
                    return ["IDLE", "IDLE", "IDLE"]
                else:
                    return [obj['lot'], chr(65+obj['recipe']), obj['step']]
        state_list.append(list(map(process_equipment, equipment)))
    for lot_arr in lots[:-1]:
        for lot in lot_arr:
            # useless lot, remove
            for i, state in enumerate(state_list):
                for j, machine_state in enumerate(state):
                    
                    if machine_state[0] == lot:
                        recipe = ord(machine_state[1])-65
                        for material,usage in enumerate(Const.recipeMaterialUse[recipe]):
                            materials[material] -= usage
                        state_list[i][j] = ["IDLE","IDLE","IDLE"]
    cost = 0
    for i, x in enumerate(materials):
        if x <= 50:
            cost += Const.materialCosts[i][0] * x
        elif x <= 500:
            cost += Const.materialCosts[i][1] * x
        else:
            cost += Const.materialCosts[i][2] * x
    revenue = len(lots[4]) * Const.sellingPrice
    print(f"Profit: {revenue-cost}")
    return state_list

def to_excel(plan):
    state_list = [sum(action,[]) for action in plan_to_state_list(plan)]
    pd.DataFrame(state_list).to_excel('out.xlsx')
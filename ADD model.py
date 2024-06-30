import math
import numpy as np
import random
from matplotlib import pyplot as plt 
from tqdm import tqdm
import copy
import csv
            
'''
----------------------------------------- INITIALISING MACROECONOMIC CLOUD---------------------------------------------------
'''
    
    
def initialise_ISPs(StartingMarket, InitialMoneyPool):
    '''
    function to reset ISP attributes to their initial parameters according to the starting market selected
    
    Starting markets include:
        super realistic: based on current (as of Apr 23 2023) plans available on the market
        simplified realsitic: translates ^ into a more simplified version that simplifies the market
        pre_NBN: taken as a stating market with low levels of competition
        idealsitic: highly competitve, equal-access ideal market 
    '''
    
    # begin by using the correct data-importing funtion
    if StartingMarket == "super_realistic":
        plans = initialise_ISPs_super_realistic()
    elif StartingMarket == "simplified_realistic":
        plans = initialise_ISPs_super_realistic()
        plans = initialise_ISPs_simplified_realistic(plans)
    elif StartingMarket == "pre_NBN":
        plans = initialise_ISPs_pre_NBN()
    elif StartingMarket == "idealistic":
        plans = initialise_ISPs_idealistic()
    else:
        print("ERROR: please provide a valid input as a starting market either:\n - 'super_realistic'\n - 'simplified_realistic'\n - 'pre_NBN'\n - 'idealistic'")
    
    # convert the CSV strings to the correct data type
    for i in range(len(plans)):
        row = plans[i]
        plans[i] = [row[0], row[1], float(row[2]), row[3], float(row[4]), row[5]]
    
    # initialising the data structure for all the ISPs and ISPs-per-location
    separated_plans = separate_plans_by_ISP(plans)
    initial_profits = get_initial_profits(StartingMarket)
    ISPs = create_ultimate_list_of_ISPs(separated_plans, initial_profits, InitialMoneyPool)
    operator_locations = define_ISPs_per_location(ISPs)
    return ISPs, operator_locations


def separate_plans_by_ISP(plans):
    '''function which takes a list of internet plans and turns it into a list of lists of plans
    where each inner list is the plans for one specific internet provider'''
    current_provider = plans[0][0]
    current_provider_plans = []
    separated_plans_list = []
    for row in plans:
        if row[0] == current_provider:
            current_provider_plans.append(row)
        else:
            separated_plans_list.append(current_provider_plans)
            current_provider_plans = [row]
            current_provider = row[0]
    separated_plans_list.append(current_provider_plans)
    return separated_plans_list


def create_ultimate_list_of_ISPs(separated_plans, initial_profits, InitialMoneyPool):
    '''
    Function to create the data structure for storing all the ISP info
    
    Entries in the ISP list have the form:
        [0: ISP name (string), 
        1: plans offered (list), 
        2: mobile offered? (bool),
        3: mobile locations offered (list or None),
        4: wifi offered? (bool),
        5: wifi locations offered (list or None),
        6: currently in price experiment? (False or list),
        7: currently in tech experiment? (False or list),
        8: monthly profit (float)
        9: moneypool]
        
    Every plan in the list of plans offered has the form:
        [0: ISP name (string),
        1: service type ('mobile' or 'wifi'),
        2: speed or GB float (speed if 'wifi' ^, GB if 'mobile' ^)
        3: locations available (string)
        4: price ($ per month)
        5: wholesale supplier]
    '''
    
    ISPs = []
    
    for i in range(len(separated_plans)):
        ISP = separated_plans[i][0][0]
        plans_offered = separated_plans[i]
        
        mobile_offered = (plans_offered[0][1] == "mobile")
        if mobile_offered:
            mobile_locations_offered = translate_footprints_into_quads(plans_offered, True)
        else:
            mobile_locations_offered = None
        
        wifi_offered = (plans_offered[-1][1] == "wifi")
        if wifi_offered:
            wifi_locations_offered = translate_footprints_into_quads(plans_offered, False)
        else:
            wifi_locations_offered = None
        
        price_exp = False
        tech_exp = False
        profit = initial_profits[i] 
        moneypool = InitialMoneyPool 
        
        ISP_data = [ISP, plans_offered, mobile_offered, mobile_locations_offered, wifi_offered, wifi_locations_offered, price_exp, tech_exp, profit, moneypool]
        ISPs.append(ISP_data)
    
    return ISPs 


def translate_footprints_into_quads2(plans, mobile):
    '''function which translates input location strings "urban", "regional" and "remote", into the quadrants
    that service would cover in footprint.'''
    total_locations_operational = []
    for p in plans:
        if not mobile and p[1] == "wifi":
            location = p[3]
            if location == "remote":
                if not 3 in total_locations_operational:
                    total_locations_operational.append(3)
            elif location == "regional":
                if not 1 in total_locations_operational:
                    total_locations_operational.append(1)
                    total_locations_operational.append(2)
            else:
                if not 0 in total_locations_operational:
                    total_locations_operational.append(0)
        elif mobile and p[1] == "mobile":
            location = p[3]
            if location == "remote":
                total_locations_operational = [0, 1, 2, 3]
            elif location == "regional":
                total_locations_operational = [0, 1, 2]
            else:
                total_locations_operational = [0]
    total_locations_operational.sort()
    return total_locations_operational

def translate_footprints_into_quads(plans, mobile):
    '''function which translates input location strings "urban", "regional" and "remote", into the quadrants
    that service would cover in footprint.'''
    total_locations_operational = []
    for p in plans:
        if not mobile and p[1] == "wifi":
            location = p[3]
            if location == "remote":
                if not 3 in total_locations_operational:
                    total_locations_operational.append(3)
                if not 1 in total_locations_operational:
                    total_locations_operational.append(1) #satellite assumed to be avail in regional areas too 
                    total_locations_operational.append(2)
            elif location == "regional":
                if not 1 in total_locations_operational:
                    total_locations_operational.append(1)
                    total_locations_operational.append(2)
            else:
                if not 0 in total_locations_operational:
                    total_locations_operational.append(0)
        elif mobile and p[1] == "mobile":
            location = p[3]
            if location == "remote":
                total_locations_operational = [0, 1, 2, 3]
                break
            elif location == "regional":
                total_locations_operational = [0, 1, 2]
            else:
                total_locations_operational = [0]
    total_locations_operational.sort()
    return total_locations_operational 


def define_ISPs_per_location(ISPs):
    ''' 
    creating a 2d array where each element in the outer array is a list for the location (quadrant), 
    and those lists are made up of numbers referring to the indexes of an ISP in ISPs that operates
    in said location.
    '''
    
    operator_locations = [[], [], [], []]
    
    for i in range(len(ISPs)):
        if ISPs[i][4] == True:
            for quad in ISPs[i][5]:
                operator_locations[quad].append(i)
        if ISPs[i][2] == True:
            for quad in ISPs[i][3]:
                operator_locations[quad].append(i)
                    
    # Remove duplicates
    for quad in operator_locations:
        i = 0
        while i < len(quad):
            j = i + 1
            while j < len(quad):
                if quad[i] == quad[j]:
                    del quad[j]  # Remove the duplicate element
                else:
                    j += 1
            i += 1
                        
    return operator_locations


def get_initial_profits(StartingMarket):
    #market share data is used as a proxy for the intial profit
    market_shares = get_market_share_data(StartingMarket)
    avg_shares = []
    for company in market_shares:
        avg_shares.append(float(company[3]))
    total = sum(avg_shares)
    profits = [share / total for share in avg_shares]
    return profits


def get_market_share_data(StartingMarket):
    if StartingMarket == "super_realistic":
        shares = []
        with open("../data_files/market/isp_market_shares.csv", "r") as file:
            csvreader = csv.reader(file)
            header = next(csvreader)
            for row in csvreader:
                shares.append(row)
        return shares


def initialise_ISPs_super_realistic():
    '''opens and saves a csv data file with real-world plan data as of 23 April 2024'''
    plans = []
    with open("../data_files/market/plans_data/realistic_plans_data.csv", 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            plans.append(row)
    return plans


def initialise_ISPs_pre_NBN():
    '''opens and saves a csv data file with pre-NBN plan data as example of low-competition market'''
    plans = []
    with open("../data_files/market/plans_data/pre_NBN_plans_data.csv", 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            plans.append(row)
    return plans


def initialise_ISPs_idealistic():
    '''opens and saves a csv data file with plan data which reflects idealistically competitive market'''
    plans = []
    with open("../data_files/market/plans_data/idealistic_plans_data.csv", 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            plans.append(row)
    return plans


'''
--------------------------------- HOUSEHOLD DECISION MAKING 'PREPERATRION' STAGE MODULES ---------------------------------
'''


def prep_bundles(person, ISPs, TimeBudget, MarketingBudget, operator_locations, Seed):
    '''stage 3 of the decsion making process where a person prepares their bundles (analagous to research)'''
    global add_to_seed
    
    y = person[0][0]
    x = person[0][1]
    if x < 50:
        if y < 50:
            quad = 0
        else:
            quad = 1
    else:
        if y < 50:
            quad = 2
        else:
            quad = 3 
    
    # establishing the operators available in their location (who's website should I look at?)
    mobile_operators, wifi_operators = pick_operators(ISPs, quad, operator_locations, TimeBudget, MarketingBudget, Seed)    
    
    # establishing the bundles physically available (which plans on the website are relevant?)
    mobile_plans = []
    wifi_plans = []
    bundles = []
        
    for m in range(len(mobile_operators)):
        for plan in mobile_operators[m][1]:
            if plan[1] == "mobile" and plan_available_in_my_area(plan, quad):
                mobile_plans.append(plan)
    for w in range(len(wifi_operators)):
        for plan in wifi_operators[w][1]:
            if plan[1] == "wifi" and plan_available_in_my_area(plan, quad):
                wifi_plans.append(plan)
    for m in range(len(mobile_plans)):
        for w in range(len(wifi_plans)):
            bundles.append((mobile_plans[m], wifi_plans[w]))
    if quad == 1 or quad ==2:        
        for w in wifi_plans:
            if w[2] > 101:
                print("Here's one:")
                print(person)
                print(w)
    
    return bundles, mobile_plans, wifi_plans

def plan_available_in_my_area(plan:list, quad:int):
    if plan[0] == "PLAN GONE":
        return False
    footprint = plan[3]
    if plan[1] == "wifi":
        if quad == 0 and footprint == "urban":
            return True
        if (quad == 1 or quad == 2) and footprint == "regional":
            return True
        if quad != 0 and footprint == "remote":
            return True
    else:
        if footprint == "remote":
            return True
        if footprint == "regional" and quad != 3:
            return True
    return False


def pick_operators(ISPs:list, quad:int, operator_locations:list, TimeBudget:int, MarketingBudget:float, Seed:int):
    '''function which biased-randomly picks ISPs for a person agent to consider plans from'''
    
    global add_to_seed
    selected_mobile_operators = []
    selected_wifi_operators = []
    indexes = [] 
    choices = operator_locations[quad]
    
    marketing_budgets = []
    industry_total = 0
    for choice in choices:
        if ISPs[choice][8] <= 0:
            marketing_budget = MarketingBudget * ISPs[choice][9] #if they experiences no profits marketing money comes out of their savings
        else:
            marketing_budget = MarketingBudget * ISPs[choice][8] #if they experienced profits marketing money comes from profits
        marketing_budgets.append(marketing_budget)
        industry_total += marketing_budget
        
    pr_effective_marketing = []
    for budget in marketing_budgets:
        pr = budget/industry_total #normalisation
        round_up_to_nearest_001(pr) #setting a minimum probability threshhold
        pr_effective_marketing.append(pr)
    pr_effective_marketing = ensure_adds_to_1(pr_effective_marketing, Seed) #incase there are errors in rounding 
        
    if TimeBudget > len(choices): 
        TimeBudget = len(choices) #avoids infinite loop below
    
    while TimeBudget > 0:
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        choice = random.choices(range(len(choices)), weights=pr_effective_marketing, k=1)[0] #probability of an ISP being chosen is proportional to that ISP's marketing budget
        index = choices[choice]
        if ISPs[index][2] and quad in ISPs[index][3]:
            selected_mobile_operators.append(ISPs[index])
            if ISPs[index][4] and quad in ISPs[index][5]:
                selected_wifi_operators.append(ISPs[index])
            TimeBudget -= 1
        elif ISPs[index][4] and quad in ISPs[index][5]:
            selected_wifi_operators.append(ISPs[index])
            TimeBudget -= 1
        
        # Remove the choice from choices and re-normalise probabilities
        choices = choices[:choice] + choices[choice+1:]
        pr_effective_marketing = pr_effective_marketing[:choice] + pr_effective_marketing[choice+1:]
        pr_sum = sum(pr_effective_marketing)
        pr_effective_marketing = [p / pr_sum for p in pr_effective_marketing]
    
    #handelling for if the chosen lists end up different sizes with wifi with less
    while len(choices) > 0 and len(selected_mobile_operators) > len(selected_wifi_operators):
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        choice = random.choices(range(len(choices)), weights=pr_effective_marketing, k=1)[0] #probability of an ISP being chosen is proportional to that ISP's marketing budget
        index = choices[choice]
        if ISPs[index][4] and quad in ISPs[index][5]:
            selected_wifi_operators.append(ISPs[index])    
        # Remove the choice from choices and re-normalise probabilities
        choices = choices[:choice] + choices[choice+1:]
        pr_effective_marketing = pr_effective_marketing[:choice] + pr_effective_marketing[choice+1:]
        pr_sum = sum(pr_effective_marketing)
        pr_effective_marketing = [p / pr_sum for p in pr_effective_marketing] 
    
    #handelling for if the chosen lists end up different sizes with mobile with less
    while len(choices) > 0 and len(selected_mobile_operators) < len(selected_wifi_operators):
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        choice = random.choices(range(len(choices)), weights=pr_effective_marketing, k=1)[0] #probability of an ISP being chosen is proportional to that ISP's marketing budget
        index = choices[choice]
        if ISPs[index][2] and quad in ISPs[index][3]:
            selected_mobile_operators.append(ISPs[index]) 
        # Remove the choice from choices and re-normalise probabilities
        choices = choices[:choice] + choices[choice+1:]
        pr_effective_marketing = pr_effective_marketing[:choice] + pr_effective_marketing[choice+1:]
        pr_sum = sum(pr_effective_marketing)
        pr_effective_marketing = [p / pr_sum for p in pr_effective_marketing] 

    return selected_mobile_operators, selected_wifi_operators


def ensure_adds_to_1(probs_array, Seed):
    '''Simple function to ensure the probabilities in an array always add up to 1'''
                     
    global add_to_seed
    total = sum(probs_array)
    if total == 1:
        return probs_array
    if total < 1: #happens very very rarely due to python's rounding to like 32 bits or whatever
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        add_to_me = random.randint(0, len(probs_array) - 1)
        amount_under = 1 - total #garunteed to be a tiiiiiny number
        probs_array[add_to_me] += amount_under
        return probs_array
    amount_over = total - 1
    while amount_over > 0: #should be a tiny number which is a scalar multiple of 0.001 (the minimum probability threshhold)
        for p in range(len(probs_array)):
            if probs_array[p] > 0.001:
                if amount_over > 0.001:
                    probs_array[p] -= 0.001
                    amount_over - 0.001
                else:
                    probs_array[p] -= amount_over
                    return probs_array


def round_up_to_nearest_001(number):
    if number > 0:
        return ((number + 0.0005) // 0.001) * 0.001
    else:
        return ((number - 0.0005) // 0.001) * 0.001
    
    
    
    
    
    
    
    
'''
--------------------------------- HOUSEHOLD DECISION MAKING 'ACTION' STAGE MODULES ---------------------------------
'''
    
    
    
    
    
    
    
    
def decide_bundle(person, complete_bundles, mobile_plans, wifi_plans, PrSacrificeWifi, PrPickBetterValue, IncomeBudget, Seed, initial_call=False):
    '''function which chooses a person's bundle from a prepared set of options'''
    
    #preference is to choose a complete bundle
    chosen_bundle = decision_tree(person, complete_bundles, IncomeBudget, PrSacrificeWifi, PrPickBetterValue, Seed, initial_call)
    if chosen_bundle != None:
        if chosen_bundle == 'no change':
            return person[3]
        return complete_bundles[chosen_bundle]
    
    else:
        #try to choose a mobile plan
        chosen_mobile_plan = decision_tree(person, mobile_plans, IncomeBudget, PrSacrificeWifi, PrPickBetterValue, Seed, initial_call)
        if chosen_mobile_plan != None:
            if chosen_mobile_plan == 'no change':
                return person[3]
            return (mobile_plans[chosen_mobile_plan], None)
        else:
            #try to choose a wifi plan
            chosen_wifi_plan = decision_tree(person, wifi_plans, IncomeBudget, PrSacrificeWifi, PrPickBetterValue, Seed, initial_call)
            if chosen_wifi_plan != None:
                if chosen_wifi_plan == 'no change':
                    return person[3]
                return (None, wifi_plans[chosen_wifi_plan])
            
    return (None, None)


def decision_tree(person, bundles, IncomeBudget, PrSacrificeWifi, PrPickBetterValue, Seed, initial_call):
    '''function which replicates the decsion-tree logic to choose the best bundle from a list of options, 
    returning the index of that bundle'''
    global add_to_seed
    if len(bundles) == 0: #early return if nothing to choose from
        return None
    
    bundle_evaluation_list = create_bundle_eval_list(bundles)
    
    x = person[0][1]
    y = person[0][0]
    if x < 50:
        if y < 50:
            quad = 0
        else:
            quad = 1
    else:
        if y < 50:
            quad = 2
        else:
            quad = 3
    income = person[2]
    
    #intitalising current in different circumstances
    if initial_call or person[3] == (None, None):
        current_best = (1000000000, 0, "dummy", "dummy") #dummy bundle
    elif isinstance(bundles[0], tuple) and (person[3][0] == None or person[3][1] == None):
        current_best = (1000000000, 0, "dummy", "dummy") #dummy bundle
    elif (person[3][0] == None and bundles[0][1] == "mobile") or (person[3][1] == None and bundles[0][1] == "wifi"):
        current_best = (1000000000, 0, "dummy", "dummy") #dummy bundle
    else: #turn current into bundle_eval_list tuple
        if person[3][0] == None:
            current_best = create_bundle_eval_list([person[3][1]])[0] #current is wifi-only
        elif person[3][1] == None:
            current_best = create_bundle_eval_list([person[3][0]])[0] #current is mobile-only
        else:
            current_best = create_bundle_eval_list([person[3]])[0] #current is complete bundle
    current_best_index = -1
    
    #the decsion tree processing 
    for new_bundle in range(len(bundle_evaluation_list)):
        current_best_cost = current_best[0]
        current_best_value = current_best[1]
        new_cost = bundle_evaluation_list[new_bundle][0]
        new_value = bundle_evaluation_list[new_bundle][1]

        if new_cost/income < IncomeBudget: #is the bundle under budget?
            if current_best_cost/income >= 0.05: #is current >= 5% of income?
                if new_cost < current_best_cost: #is new bundle cheaper?
                    current_best = bundle_evaluation_list[new_bundle]
                    current_best_index = new_bundle
            else:
                if new_cost/income < 0.05: #is new bundle < 5% of income?
                    if (new_cost/income <= 0.02) and (new_value > current_best_value): #is new bundle <= 2% of income and better value?
                        random.seed(Seed + add_to_seed)
                        add_to_seed += 23
                        if random.random() < PrPickBetterValue:
                            current_best = bundle_evaluation_list[new_bundle]
                            current_best_index = new_bundle
                        else:
                            if new_is_a_cheaper_minimum_quality(bundle_evaluation_list[new_bundle], current_best, PrSacrificeWifi, Seed): #is new bundle better value for money?
                                current_best = bundle_evaluation_list[new_bundle]
                                current_best_index = new_bundle
                    else:
                        if new_is_a_cheaper_minimum_quality(bundle_evaluation_list[new_bundle], current_best, PrSacrificeWifi, Seed): #is new bundle better value for money?
                            current_best = bundle_evaluation_list[new_bundle]
                            current_best_index = new_bundle
    
    #handeling for when a person experiences 'internet proverty' (can't afford any bundle)
    if current_best_index == -1 and current_best[0] == 'dummy':
        return None
    
    #handeling for if prices have increased since user last checked thier plan, but it was still better than everything else
    if current_best_index == -1:
        if current_best[0]/income > IncomeBudget:
            return None
        else:
            return "no change"
        
    return current_best_index


def create_bundle_eval_list(bundles:list):
    '''turning a list of bundles into a bundle_evaluation_list for decsion tree processing'''
    
    bundle_evaluation_list = []
    
    if isinstance(bundles[0], tuple): 
        max_GB = 0
        max_Mbps = 0
        for bundle in bundles:
            if bundle[0][2] > max_GB:
                max_GB = bundle[0][2]
            if bundle[1][2] > max_Mbps:
                max_Mbps = bundle[1][2]
        
        for bundle in bundles:
            price = bundle[0][4] + bundle[1][4]
            value = ((bundle[0][2]/max_GB) + (bundle[1][2]/max_Mbps))/2 #0-1 standarised avg value
            if bundle[0][2] > 61:
                minimum_quality_mobile = True
            else:
                minimum_quality_mobile = False
            if bundle[1][2] > 25:
                minimum_quality_wifi = True
            else:
                minimum_quality_wifi = False
            bundle_evaluation_list.append((price, value, minimum_quality_mobile, minimum_quality_wifi))
    
    else:
        max_value = 0
        for plan in bundles:
            if plan[2] > max_value:
                max_value = plan[2]
                
        for plan in bundles:
            price = plan[4]
            value = plan[2]/max_value #standardise value
            minimum_quality_mobile = None
            minimum_quality_wifi = None
            if plan[1] == "mobile":
                if plan[2] > 61:
                    minimum_quality_mobile = True
                else:
                    minimum_quality_mobile = False
            elif plan[1] == "wifi":
                if plan[2] > 25:
                    minimum_quality_wifi = True
                else:
                    minimum_quality_wifi = False
            bundle_evaluation_list.append((price, value, minimum_quality_mobile, minimum_quality_wifi))
    
    return bundle_evaluation_list  


def new_is_a_cheaper_minimum_quality(new_bundle, current_best, PrSacrificeWifi, Seed):
    '''function to decide implementing the "pick the cheapest plan surpassing a minimum
    quality threshhold" decision strategy '''
    
    global add_to_seed
    random.seed(Seed + add_to_seed)
    add_to_seed += 23 #there will only ever be one random decision made in this algorithm, if any
    
    new_mqm = new_bundle[2]
    new_mqw = new_bundle[3]
    current_mqm = current_best[2]
    current_mqw = current_best[3]
    
    if new_mqm == "dummy":
        return False
    if current_mqm == "dummy":
        return True
    
    if new_mqm != None and new_mqw != None and current_mqm != None and current_mqw != None:
        # use matrix for comparing complete bundles
        new = (new_mqm, new_mqw)
        current = (current_mqm, current_mqw)
        
        if new == (True, True):
            if current == (True, True):
                decision = "pick cheaper"
            else:
                return True
        elif new == (True, False):
            if current == (True, True):
                return False
            elif current == (True, False):
                decision = "pick cheaper"
            elif current == (False, True):
                if random.random() < PrSacrificeWifi:
                    return True
                else:
                    return False
            else:
                return True
        elif new == (False, True):
            if current == (False, False):
                return True
            elif current == (False, True):
                decision = "pick cheaper"
            elif current == (True, False):
                if random.random() < PrSacrificeWifi:
                    return True
                else:
                    return False
            else:
                return False
        else:
            if current == (False, False):
                decision = "pick better value"
            else:
                return False
    
    #always pick complete bundle over a singular plan
    elif new_mqm != None and new_mqw != None:
        return True
    elif current_mqm != None and current_mqw != None:
        return False
    
    #matricies for complaring singular plans
    else:
        if new_mqm == None:
            if current_mqm != None:
                if random.random() < PrSacrificeWifi:
                    return False
                else:
                    return True 
            if new_mqw == True:
                if current_mqw == True:
                    decision = "pick cheaper"
                else:
                    return True
            else:
                if current_mqw == True:
                    return False
                else:
                    decision = "pick better value"
        else:
            if current_mqw != None:
                if random.random() < PrSacrificeWifi:
                    return True
                else:
                    return False
            if new_mqm == True:
                if current_mqm == True:
                    decision = "pick cheaper"
                else:
                    return True
            else:
                if current_mqm == True:
                    return False
                else:
                    decision = "pick better value"
    
    if decision == "pick cheaper":
        if new_bundle[0] <= current_best[0]:
            return True
        else:
            return False
    else:
        if new_bundle[1] >= current_best[1]:
            return True
        else:
            return False
    print('got to end somehow')
    return False





'''
----------------------------------------------- GRID INITIALISATION FUNCTIONS --------------------------------------------
'''








def decide_if_populated(location: tuple, Seed:int):
    '''
    function which randomly decides if a grid-square is populated (1) 
    or empty (0), with probability depending on location, to simulate city 
    vs rural population density.
    '''
    global add_to_seed
    y = location[0]
    x = location[1]
    random.seed(Seed + add_to_seed)
    add_to_seed += 23
    num = random.random()     
    
    if x < 50 and y < 50: #urban
        if num < 0.8:
                return True
    elif x >= 50 and y >= 50: #remote
        if num < 0.07:
                return True
    else: #regional
        if num < 0.15: 
                return True
    return False
            

def initialise_income(location: tuple, Seed:int):
    '''
    Randomly samples income based on location by assigning agents to a quartile (based on average LGA 
    income quartile data across different remoteness areas), and using national quartile ranges from ABS 
    to sample the income from within a quartile's range
    '''
    global add_to_seed
    y = location[0]
    x = location[1]
    
    if x < 50 and y < 50: #urban
        probabilities = [0.238, 0.235, 0.239, 0.288] #see the determined avg income per remoteness area file
    elif x >= 50 and y >= 50: #remote
        probabilities = [0.294, 0.246, 0.237, 0.223]
    else: #regional
        probabilities = [0.287, 0.268, 0.246, 0.199]
    quartiles = [1, 2, 3, 4]
    random.seed(Seed + add_to_seed)
    add_to_seed += 23
    quartile = random.choices(quartiles, weights=probabilities, k=1)[0]
    
    random.seed(Seed + add_to_seed)
    add_to_seed += 23
    if quartile == 1:
        income = random.uniform(381, 2594) #lowerbound taken as the centrelink JobSeeker amount for single, no children people
    elif quartile == 2:
        income = random.uniform(2595, 3838)
    elif quartile == 3:
        income = random.uniform(3839, 5602)
    elif quartile == 4:
        income = random.uniform(5603, 15000) #upperbound is just above the 95% percentile for taxable income in 2019
    
    return income


def decide_expenditure(bundle: tuple, income: int):
    '''simple little function determing the percentage a person is spending on internet based on thier bundle'''
    if bundle == (None, None): #no connection
        return None 
    elif bundle[0] == None: #wifi only
        return bundle[1][4] / income * 100 
    elif bundle[1] == None: #mobile only
        return bundle[0][4] / income * 100
    else: 
        return (bundle[0][4] + bundle[1][4]) / income * 100
    
    
    
def initialise_grid(TimeBudget:int, IncomeBudget:float, MarketingBudget:float, PrSacrificeWifi:float, PrPickBetterValue:float, Seed:int):  
    '''function to create an initial grid of 100x100 dimension, where each (filled) 
    cell is an agent that with atrributes:
        
        [0: location: tuple, 
        1: populated status: bool, 
        2: monthly income: int ($), 
        3: internet bundle: tuple (mobile plan, wifi plan) 
        4: percentage income spent on bundle: float%]
    
    Time complexity: O(width x height x TimeBudget^2 x max_plans_per_provider_per_location) ~= 50000 * timexc.p-0
    '''
    global add_to_seed
    grid = np.zeros((100, 100, 6), dtype=object) #init the grid as a 3D np array
    
    # Populating the grid
    for row in tqdm(range(100)):
        for cell in range(100):
            location = (row, cell)
            is_populated = decide_if_populated(location, Seed)
            grid[row, cell, 0] = location
            grid[row, cell, 1] = is_populated
            
            if is_populated:
                income = initialise_income(location, Seed)
                complete_bundles, mobile_plans, wifi_plans = prep_bundles([location, True, income, (None, None), None], ISPs, TimeBudget, MarketingBudget, operator_locations, Seed)
                bundle = decide_bundle([location, True, income, (None, None), None], complete_bundles, mobile_plans, wifi_plans, PrSacrificeWifi, PrPickBetterValue, IncomeBudget, Seed, True)
                percent_spent_on_bundle = decide_expenditure(bundle, income)
                
                grid[row, cell, 2] = income
                grid[row, cell, 3] = bundle
                grid[row, cell, 4] = percent_spent_on_bundle
            
    return grid



def plotting_func(colouring_desired):
    fig, ax = plt.subplots()
    ax.imshow(np.zeros((100, 100)), cmap='gray')  # Initialising grid with grey
    colours_for_later = []
    
    if colouring_desired == "income":
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 2] <= 2594:
                        color = 'orangered'
                    elif grid[row, cell, 2] <= 3838:
                        color = 'lightpink'
                    elif grid[row, cell, 2] <= 5602:
                        color = 'lightsteelblue'
                    elif grid[row, cell, 2] > 5602:
                        color = 'blue'
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by income quartile")
        legend = "red = quartile 1 ($1525 - $2594)\npink = quartile 2 ($2595 - $3838)\nlight blue = quartile 3 ($3839 - $5602)\ndark blue = quartile 4 ($5603-$12000)"
        
    elif colouring_desired == "affordability_stress_status":
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 4] == None:
                        color = "red"
                    elif grid[row, cell, 4] >= 5:
                        color = 'orange'
                    elif grid[row, cell, 4] < 5:
                        color = 'lightgreen'
                    else:
                        print("ERROR: unmatched percent spent -", grid[row, cell, 4])
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by affordability stress status")
        legend = "green = no stress\norange = affordability stress\nred = internet poverty (no connection)"
    
    elif colouring_desired == "wifi_tech_type":
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 3][1] == None:
                        if grid[row, cell, 3][0] == None:
                            color = 'red'
                        else:
                            color = 'lightsalmon'
                    elif grid[row, cell, 3][1][3] == 'urban':
                        color = 'lightskyblue'
                    elif grid[row, cell, 3][1][3] == 'regional':
                        color = 'blue'
                    elif grid[row, cell, 3][1][3] == 'remote':
                        color = 'blueviolet'
                    else:
                        print("ERROR: unmatched tech type - '", grid[row, cell, 3][1][3])
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by NBN home broadband tech type")
        legend = "LEGEND:\nlight blue = wired\ndark blue = fixed wireless\npurple = satellite\nsalmon = mobile only\nred = no connection"
        
    elif colouring_desired == "bundle_type":
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 3] == (None, None):
                        color = "red"
                    elif grid[row, cell, 3][1] == None:
                        color = "fuchsia"
                    elif grid[row, cell, 3][0] == None:
                        color = "aqua"
                    else:
                        color = "greenyellow"
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by bundle type")
        legend = "LEGEND:\ngreen = both mobile and home wifi\naqua = wifi only\nfuchsia = mobile only\nred = no connection"
        
    elif colouring_desired == "mobile_ISP":
        colours = ["lightblue", "gold", "yellow", "red", "blueviolet", "green", "lightsalmon", "fuchsia", "blue", "orange", "crimson", "lime", "brown", "aqua", "grey", "peru"]
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 3][0] == None:
                        color = "white"
                    else:
                        for i in range(len(ISPs)):
                            if ISPs[i][0] == grid[row, cell, 3][0][0]:
                                color = colours[i]
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by mobile provider")
        legend = "LEGEND:\nlight blue = Telstra\ngold = TPG\nyellow = Optus\nred = Vodafone\npurple = Dodo\ngreen = Aussie Broadband\nsalmon = iiNet\norange = Tangerine\ncrimson = Kogan\nlight green = Exetel\ndark brown = Bendigo Telco\naqua = Superloop\nlight brown = Moose Mobile\nwhite = no connection"
        
    elif colouring_desired == "home_wifi_ISP":
        colours = ["lightblue", "gold", "yellow", "red", "blueviolet", "green", "lightsalmon", "fuchsia", "blue", "orange", "crimson", "lime", "brown", "aqua", "grey", "peru"]
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 3][1] == None:
                        color = "white"
                    else:
                        for i in range(len(ISPs)):
                            if ISPs[i][0] == grid[row, cell, 3][1][0]:
                                color = colours[i]
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by home wifi provider")
        legend = "LEGEND:\nlight blue = Telstra\ngold = TPG\nyellow = Optus\nred = Vodafone\npurple = Dodo\ngreen = Aussie Broadband\nsalmon = iiNet\nfuchsia = SkyMesh\ndark blue = Activ8me\norange = Tangerine\ncrimson = Kogan\nlight green = Exetel\ndark brown = Bendigo Telco\naqua = Superloop\ngrey = IPstar\nwhite = no connection"
        
    elif colouring_desired == "home_internet_speed":
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 3][1] == None:
                        color = "red"
                    elif grid[row, cell, 3][1][2] <= 12:
                        color = "blue"
                    elif grid[row, cell, 3][1][2] <= 25:
                        color = "dodgerblue"
                    elif grid[row, cell, 3][1][2] <= 50:
                        color = "aqua"
                    elif grid[row, cell, 3][1][2] <= 100:
                        color = "lime"
                    else:
                        color = "green"
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by home internet speed")
        legend = "LEGEND:\ndark blue: up to 12 Mbps\nmid blue: up to 25 Mbps\naqua: up to 50 Mbps\nlime: up to 100 Mbps\ndark green: 230+ Mbps\nred = no connection"

    
    elif colouring_desired == "percent_income_spent":
        for row in tqdm(range(100)):
            for cell in range(100):
                if grid[row, cell, 1]:
                    if grid[row, cell, 4] == None:
                        color = 'red'
                    elif grid[row, cell, 4] <= 2:
                        color = 'lightgreen'
                    elif grid[row, cell, 4] < 5:
                        color = 'yellow'
                    elif grid[row, cell, 4] < 15:
                        color = 'orange'
                    else:
                        print("ERROR ", grid[row, cell])
                    ax.plot(cell, row, 'o', color=color, markersize=2)
                    colours_for_later.append(color)
        ax.set_title("coloured by percentage income spent on plan")
        legend = "green = up to 2%\nyellow = between 2-5%\norange = over 5%\nred = internet poverty (no plan exists under 15% of income)"

    ax.set_xlim([0, 100])
    ax.set_ylim([0, 100])
    plt.show()
    print(legend)
    colours_for_later.append(colouring_desired)
    return colours_for_later


def bar_chart_plotting_func(colours):
    
    if colours[-1] == "income":
        x = ["Q1", "Q2", "Q3", "Q4"]
        y = np.array([0, 0, 0, 0])
        colour_names = ["orangered", "lightpink", "lightsteelblue", "blue"]
        
    if colours[-1] == "affordability_stress_status":
        x = ["no stress", "stress", "internet poverty"]
        y = np.array([0, 0, 0])
        colour_names = ["lightgreen", "orange", "red"]
    
    if colours[-1] == "wifi_tech_type":
        x = ["fixed line", "fixed wireless", "satellite", "mobile only", "no connection"]
        y = np.array([0, 0, 0, 0, 0])
        colour_names = ["lightskyblue", "blue", "blueviolet", "lightsalmon", "red"]
        
    if colours[-1] == "bundle_type":
        x = ["mobile and wifi", "wifi only", "mobile only", "no connection"]
        y = np.array([0, 0, 0, 0])
        colour_names = ["greenyellow", "aqua", "fuchsia", "red"]
        
    if colours[-1] == "mobile_ISP":
        x = ["Telstra", "TPG", "Optus", "Vodafone", "Dodo", "Aussie Broadband", "iiNet", "Tangerine", "Kogan", "Exetel", "Bendigo Telco", "Superloop", "Moose Mobile"]
        y = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        colour_names = ["lightblue", "gold", "yellow", "red", "blueviolet", "green", "lightsalmon", "orange", "crimson", "lime", "brown", "aqua", "peru"]
        
    if colours[-1] == "home_wifi_ISP":
        x = ["Telstra", "TPG", "Optus", "Vodafone", "Dodo", "Aussie Broadband", "iiNet", "SkyMesh", "Activ8me", "Tangerine", "Kogan", "Exetel", "Bendigo Telco", "Superloop", "IPstar"]
        y = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        colour_names = ["lightblue", "gold", "yellow", "red", "blueviolet", "green", "lightsalmon", "fuchsia", "blue", "orange", "crimson", "lime", "brown", "aqua", "grey"]
    
    if colours[-1] == "home_internet_speed":
        x = ["<=12Mbps", "<=25Mbps", "<=50Mbps", "<=100Mbps", ">=230Mbps", "no home connection"]
        y = np.array([0, 0, 0, 0, 0, 0])
        colour_names = ["blue", "dodgerblue", "aqua", "lime", "green", "red"]
    
    if colours[-1] == "percent_income_spent":
        x = ["<=2%", ">2% but <5%", ">=5% but <15%", "disconnected"]
        y = np.array([0, 0, 0, 0])
        colour_names = ["lightgreen", "yellow", "orange", "red"]
    
    for c1 in colours:
        for c2 in range(len(colour_names)):
            if c1 == colour_names[c2]:
                y[c2] += 1
    y = y/len(colours)*100

    plt.bar(x, y, color=colour_names)
    plt.ylim(0,100)
    plt.xticks(rotation=45, ha="right")
    plt.title("% proportion of colours on grid")
    plt.show()
    

def income_per_remoteness_stacked(grid, colours):
    x = ["urban", "regional", "remote", "total"]
    under_2 = np.array([0, 0, 0, 0])
    under_5 = np.array([0, 0, 0, 0])
    under_10 = np.array([0, 0, 0, 0])
    over_10 = np.array([0, 0, 0, 0])
    no_connection = np.array([0, 0, 0, 0])
    
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                
                if row < 50 and cell < 50:
                    index = 0
                elif row >= 50 and cell >= 50:
                    index = 2
                else:
                    index = 1
                
                percent = grid[row, cell, 4]
                if percent == None:
                    correctlist = no_connection
                elif percent < 2:
                    correctlist = under_2
                elif percent < 5:
                    correctlist = under_5
                elif percent < 10:
                    correctlist = under_10
                else:
                    correctlist = over_10
                
                correctlist[index] += 1
                correctlist[-1] += 1 #updating total
                
    totals = [0, 0, 0, 0]
    for i in range(4):
        totals[i] = under_2[i] + under_5[i] + under_10[i] + over_10[i]
                
    for i in range(4):
        under_2[i] = under_2[i]/totals[i] * 100
        under_5[i] = under_5[i]/totals[i] * 100
        under_10[i] = under_10[i]/totals[i] * 100
        over_10[i] = over_10[i]/totals[i] * 100 
                
    plt.bar(x, under_2, label="<2", color='blue')
    plt.bar(x, under_5, bottom=under_2, label="<5", color='dodgerblue')
    plt.bar(x, under_10, bottom=under_2+under_5, label="<10", color='lime')
    plt.bar(x, over_10, bottom=under_2+under_5+under_10, label=">10", color='green')
    plt.bar(x, no_connection, bottom=under_2+under_5+under_10+over_10, label="no connection", color="red")
    plt.title("Percentage of income spent on internet, by remoteness area")
    plt.legend(bbox_to_anchor=(1.5, 1), loc="upper right")
    plt.ylim(0, 100)
    plt.show()  

    
def recreate_ADII_figure(grid, trigger=False):
    x = ["Q1", "Q2", "Q3", "Q4", "Q5", "total"]
    under_2 = np.array([0, 0, 0, 0, 0, 0])
    under_5 = np.array([0, 0, 0, 0, 0, 0])
    under_10 = np.array([0, 0, 0, 0, 0, 0])
    over_10 = np.array([0, 0, 0, 0, 0, 0])
    no_connection = np.array([0, 0, 0, 0, 0, 0])
    
    threshholds = find_the_quintiles(grid)
    
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                
                income = grid[row, cell, 2]
                for i in range(5):
                    if income < threshholds[i]:
                        index = i
                        break
                
                percent = grid[row, cell, 4]
                if percent == None:
                    if trigger:
                        correctlist = over_10
                    else:
                        correctlist = no_connection
                elif percent < 2:
                    correctlist = under_2
                elif percent < 5:
                    correctlist = under_5
                elif percent < 10:
                    correctlist = under_10
                else:
                    correctlist = over_10
                
                correctlist[index] += 1
                correctlist[-1] += 1 #updating total
    totals = [0, 0, 0, 0, 0, 0]
    for i in range(6):
        totals[i] = under_2[i] + under_5[i] + under_10[i] + over_10[i]
                
    for i in range(6):
        under_2[i] = under_2[i]/totals[i] * 100
        under_5[i] = under_5[i]/totals[i] * 100
        under_10[i] = under_10[i]/totals[i] * 100
        over_10[i] = over_10[i]/totals[i] * 100
                
    plt.bar(x, under_2, label="<2", color='orangered')
    plt.bar(x, under_5, bottom=under_2, label="<5", color='lightsalmon')
    plt.bar(x, under_10, bottom=under_2+under_5, label="<10", color='lightblue')
    plt.bar(x, over_10, bottom=under_2+under_5+under_10, label=">10", color='blue')
    plt.title("Percentage of income spent on internet, by income quintile")
    plt.legend()
    plt.show()
    
    
def check_the_quintiles(grid):
    
    threshholds = find_the_quintiles(grid)
    x = ["Q1: 0-" + str(threshholds[0]), 
         "Q2: " + str(threshholds[0]+1) + "-" + str(threshholds[1]), 
         "Q3: " + str(threshholds[1]+1) + "-" + str(threshholds[2]), 
         "Q4: " + str(threshholds[2]+1) + "-" + str(threshholds[3]),
         "Q5: " + str(threshholds[3]+1) + "-" + str(threshholds[4])]
    y = np.array([0, 0, 0, 0, 0])
    
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                
                income = grid[row, cell, 2]
                for i in range(5):
                    if income < threshholds[i]:
                        index = i
                        break
                y[index] += 1
    plt.bar(x, y)
    plt.xticks(rotation=45, ha="right")
    plt.title("Ranges for the $ per month income quintiles")


def find_the_quintiles(grid):
    num_agents = 0
    incomes = []
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                num_agents += 1
                incomes.append(grid[row, cell, 2])
    incomes = sorted(incomes)
    num_per_quintile = num_agents//5
    threshholds = []
    for i in range(4):
        threshholds.append(int(incomes[num_per_quintile * (i + 1)]))
    threshholds.append(int(incomes[-1]))
    return threshholds






'''
------------------------------------------------ MAIN SIMULATION FUNCTIONS -----------------------------------------
'''









def update_ISP_profits_and_moneypool(ISPs, grid, LargeMarkup, SmallMarkup, ResellerOperatingFee, WholesalerOperatingFee, MarketingBudget, profit_changes, nbn_co_revenue_changes):
    '''This function determines how much money is being made per ISP with current user base'''
    profits = [0 for _ in range(len(ISPs))]
    nbn_co_revenue = 0
    
    #Step 1: calculate the amount each ISP gains from sales (sales - variable costs)
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1] == True: #if non-empty
                mobile_plan = grid[row, cell, 3][0]
                wifi_plan = grid[row, cell, 3][1]
                
                if mobile_plan == None:
                    mobile_isp = None
                    mobile_index = None
                else:
                    mobile_isp = mobile_plan[0]
                
                if wifi_plan == None:
                    wifi_isp = None
                    wifi_index = None
                else:
                    wifi_isp = wifi_plan[0]
                
                for idx in range(len(ISPs)):
                    if ISPs[idx][0] == mobile_isp:
                        mobile_index = idx
                    if ISPs[idx][0] == wifi_isp:
                        wifi_index = idx
                
                #add mobile revenue
                if mobile_index != None:
                    
                    #add profits from retail
                    if mobile_index == 0 or mobile_index == 1 or mobile_index == 2 or mobile_index == 3:
                        markup = LargeMarkup
                    else:
                        markup = SmallMarkup
                    mobile_wholesale_expense = mobile_plan[4]/(markup/100)
                    profits[mobile_index] += (mobile_plan[4] - mobile_wholesale_expense)
                    
                    #add profits from wholesale
                    supplier = mobile_plan[5]
                    if supplier == "Telstra":
                        profits[0] += mobile_wholesale_expense
                    elif supplier == "Optus":
                        profits[2] += mobile_wholesale_expense
                    elif supplier == "TPG":
                        profits[1] += 0.5*mobile_wholesale_expense
                        profits[3] += 0.5*mobile_wholesale_expense #TPG and Vodafone are merged
                
                #add wifi revenue
                if wifi_index != None:
                    wifi_wholesale_expense = wifi_wholesale_cost(wifi_plan[2])
                    profits[wifi_index] += (wifi_plan[4] - wifi_wholesale_expense) #deducts nbn flat fee per connection
                    if wifi_plan[5] == "NBN Co":
                        nbn_co_revenue += wifi_wholesale_expense
                        
    #step 2: determine how much money is being lost to fixed costs (operating fees)
    for isp in range(len(ISPs)):
        
        #caluclate expenses proportional to operations (staff, website, stores)
        locations_operational = 0
        if ISPs[isp][2]:
            locations_operational += len(ISPs[isp][3])
        if ISPs[isp][4]:
            locations_operational += len(ISPs[isp][5])
        reseller_operation_cost = ResellerOperatingFee * locations_operational
        
        #calculate expenses from marketing
        if ISPs[isp][8] == 0:
            marketing_expenditure = MarketingBudget * ISPs[isp][9] #paid marketing out of savings
        else:
            marketing_expenditure = MarketingBudget * ISPs[isp][8] #paid marketing out of profit
            
        total_expenditure = reseller_operation_cost + marketing_expenditure
        #if mobile wholesaler, deduct wholesale operation fee
        if isp == 0 or isp == 2:
            total_expenditure += (WholesalerOperatingFee * len(ISPs[isp][3]))
        elif isp == 1 or isp == 3:
            total_expenditure += (0.5 * WholesalerOperatingFee * len(ISPs[isp][3]))
        
        profits[isp] -= total_expenditure

    #step 3: update the ISPs's profits and savings
    for isp in range(len(ISPs)):
        profit = profits[isp]
        savings = 0.05 * profit
        ISPs[isp][8] = profit
        ISPs[isp][9] += savings
    
    return profits, nbn_co_revenue

        
def wifi_wholesale_cost(speed):
    '''Function which takes a wifi speed in Mbps and outputs the wholesale cost NBN Co charges for that speed'''
    speeds = [12, 25, 50, 100, 250, 1000]
    prices = [12, 26, 50, 55, 60, 70]
    for tier in range(len(speeds)):
        if speed <= speeds[tier]:
            return prices[tier]
                          

def check_for_bankruptcy(ISPs, operator_locations):
    '''Function which handles how the simulation responds to bankruptcy (when moneypool of a firm is <= 0)'''
    
    for firm in range(len(ISPs)):
        if ISPs[firm][9] <= 0: #firm has reached bankruptcy
            
            #remove firm as a choice from all operator locations
            for quad in range(len(operator_locations)):
                for operator in range(len(operator_locations[quad])): 
                    if operator_locations[quad][operator] == firm:
                        operator_locations[quad] = operator_locations[quad][:operator] + operator_locations[quad][operator+1:]
                        break                       

        
def review_price_experiments(ISPs, PrPriceExp, LenPriceExp, PercentPriceChange, Seed):
    '''Function to review pricing experiments. 
    pricing_experiments are of the form either False or [plan, change, months_left, prev_profit]
    '''
    global add_to_seed
    
    for isp in range(len(ISPs)):
        if ISPs[isp][9] > 0: #don't bother with all this computation if the firm is dead

            if ISPs[isp][6] != False: #is ISP currently engaged in a price experiment?
                price_exp = ISPs[isp][6]
                if price_exp[2] == 0: #if its time for review
                    if ISPs[isp][8] <= price_exp[3]: #if profits post-exp are worse than profits pre-exp
                        ISPs[isp][1][price_exp[0][1]][4] = ISPs[isp][1][price_exp[0][1]][4]/(1 + price_exp[1]) #revert price
                    ISPs[isp][6] = False #terminate the experiment
                else:
                    price_exp[2] -= 1 #reduce number months left of the experiment
                    ISPs[isp][6] = price_exp

            elif (not ISPs[isp][6]) and (not ISPs[isp][7]): #not currently engaged in price or location exp
                random.seed(Seed + add_to_seed)
                add_to_seed += 23
                if random.random() < PrPriceExp: #with some probablity enter new price exp
                    choices = [choice for choice in range(len(ISPs[isp][1]))]
                    for choice in choices:
                        if ISPs[isp][1][choice][0] == 'PLAN GONE':
                            choices = choices[:choice] + choices[choice+1:]
                    random.seed(Seed + add_to_seed)
                    add_to_seed += 23
                    targeted_plan = random.choice(choices)
                    current_price = ISPs[isp][1][targeted_plan][4]
                    
                    random.seed(Seed + add_to_seed)
                    add_to_seed += 23
                    if random.random() < 0.5:
                        change = -1 * PercentPriceChange
                        if current_price + change*current_price < min_price_allowed(ISPs[isp][1], ISPs[isp][1][targeted_plan]):
                            change = None
                    else:
                        change = PercentPriceChange
                    
                    if change != None:
                        new_price = current_price + change*current_price
                        ISPs[isp][1][targeted_plan][4] = new_price
                        price_exp = [(ISPs[isp][1][targeted_plan], targeted_plan), change, LenPriceExp, copy.deepcopy(ISPs[isp][8])] #create new experiment of LenPriceExp duration
                        ISPs[isp][6] = price_exp
                    
                    
def min_price_allowed(plans, target):
    '''setting a lowerbound realistic price an ISP can experiment with'''
    
    if target[1] == 'wifi':
        tiers = [15, 25, 50, 100, 250, 1000]
        speed = target[2]
        for speed2 in range(len(tiers)):
            if tiers[speed2] >= speed:
                tier = speed2
                break
        wholesale_prices = [12, 26, 50, 55, 60, 70]
        min_price_based_on_wholesale = wholesale_prices[tier] + 1
        
        location = target[3]
        min_price_based_on_lowers = 0
        for plan in plans:
            if plan[0] != "PLAN GONE" and plan[1] == "wifi" and plan[3] == location:
                if plan[2] < speed:
                    if plan[4] > min_price_based_on_lowers:
                        min_price_based_on_lowers = plan[4] + 1
        if min_price_based_on_wholesale >= min_price_based_on_lowers:
            return min_price_based_on_wholesale
        else:
            return min_price_based_on_lowers
        
    else:
        gb = target[2]
        min_price_based_on_lowers = 0
        for plan in plans:
            if plan[0] != "PLAN GONE" and plan[1] == "mobile":
                if plan[2] < gb:
                    if plan[4] > min_price_based_on_lowers:
                        min_price_based_on_lowers = plan[4] + 1
        return min_price_based_on_lowers

            
def review_plan_experiments(ISPs, PrPlanExp, LenPlanExp, Seed):
    '''Fucntion to review plan experiments.
    plan experiments are of the form either False or [(plan, index), 0 or 1, months left, prev profit]
    '''
    global add_to_seed
    
    replacements = []
    for isp in range(len(ISPs)):
        if ISPs[isp][9] > 0:

            if ISPs[isp][7] != False: #is ISP currently engaged in a plan experiment?
                plan_exp = ISPs[isp][7]
                
                if plan_exp[2] == 0: #if its time for review
                    if ISPs[isp][8] <= plan_exp[3]: #if profits post-exp are worse than profits pre-exp
                        
                        if plan_exp[1] == 1: #if the experiment added a plan
                            ISPs[isp][1] = ISPs[isp][1][:-1] #revert by taking the plan away 
                        
                        else: #if the experiment took a plan away
                            ISPs[isp][1][plan_exp[0][1]][0] = plan_exp[0][0][0] #put plan back in original location
                            ISPs[isp][1][plan_exp[0][1]][1] = "wifi"

                    ISPs[isp][7] = False #terminate the experiment
               
                else:
                    plan_exp[2] -= 1 #reduce number months left of the experiment
                    ISPs[isp][7] = plan_exp

            elif (not ISPs[isp][6]) and (not ISPs[isp][7]): #not currently engaged in price or plan exp
                random.seed(Seed + add_to_seed)
                add_to_seed += 23
                if random.random() < PrPlanExp and ISPs[isp][4]: #with some probablity enter new location exp
                    
                    #plan experiment is to remove a plan
                    random.seed(Seed + add_to_seed)
                    add_to_seed += 23
                    if random.random() > 0.5:
                        plan_exp, replacement = choose_plan_to_remove(ISPs[isp], LenPlanExp, Seed)
                        if plan_exp != None:
                            targeted_plan = plan_exp[0][1]
                            ISPs[isp][1][targeted_plan][0] = "PLAN GONE" #remove plan
                            ISPs[isp][7] = plan_exp
                            replacements.append((isp, replacement)) #keep track of which plans users must replace
                            ISPs[isp][1][targeted_plan][1] = len(replacements) - 1 #set 1st elem to the position of the replacement plan in the replacements array

                    #plan experiment is to add a plan 
                    else:
                        plan_exp = None
                        while_loop_iterations = 0
                        while plan_exp == None and while_loop_iterations < 50:
                            while_loop_iterations += 1
                            plan_exp = choose_plan_to_add(ISPs, ISPs[isp], LenPlanExp, Seed)
                        if plan_exp != None:
                            ISPs[isp][1].append(plan_exp[0][0])
                            ISPs[isp][7] = plan_exp
    return replacements
                            
                            
def choose_plan_to_remove(isp, LenPlanExp, Seed):
    '''function to pick which plan will be experimented with (via removal), and identifies a plan to push 
    current users onto, with preference to the next most expensive plan'''
    
    global add_to_seed
    
    #choose experiment
    choices = []
    for plan in range(len(isp[1])):
        if isp[1][plan][1] == "wifi":
            choices.append(plan)
    random.seed(Seed + add_to_seed)
    add_to_seed += 23
    if len(choices) == 0:
        return None, None
    experiment = random.choice(choices)
    
    #choose a plan for the users currently on the old plan to switch to 
    replacements = []
    for choice in choices:
        if choice != experiment:
            if isp[1][choice][3] == isp[1][experiment][3]: #must be available in same area 
                replacements.append(choice)
    current_best = ["dummy", "dummy", "dummy", "dummy", -1, "dummy"]
    current_best_index = -1
    exp_price = isp[1][experiment][4]
    
    for replacement in replacements:
        best_price = current_best[4]
        new_price = isp[1][replacement][4]
        
        if best_price > exp_price:
            if new_price < best_price and new_price > exp_price:
                current_best_index = replacement
                current_best = isp[1][current_best_index]
        else:
            if new_price > best_price:
                current_best_index = replacement
                current_best = isp[1][current_best_index]
    if current_best_index == -1:
        current_best = None
        current_best_index = None
        
    return [(copy.deepcopy(isp[1][experiment]), experiment), 0, LenPlanExp, isp[8]], current_best_index
    

def choose_plan_to_add(ISPs, isp, LenPlanExp, Seed):
    '''Function which randomly chooses a plan for an isp to experiment by stealing an idea off a competitor.'''
    
    global add_to_seed
    
    competitor = [isp[0]]
    while competitor[0] == isp[0] or competitor[9] <= 0: #don't steal idea off urself or a dead firm
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        competitor = random.choice(ISPs)
    possibilities = copy.deepcopy(competitor[1])
    plans = isp[1]
    
    for p1 in range(len(plans)):
        p2 = 0
        while p2 < len(possibilities):
            add_one_to_p2 = True
            
            #remove any dead plans as possibilities
            if possibilities[p2][0] == "PLAN GONE":
                possibilities = possibilities[:p2] + possibilities[p2+1:]
                add_one_to_p2 = False
            
            #remove any mobile plans as possibilities
            elif possibilities[p2][1] == "mobile":
                possibilities = possibilities[:p2] + possibilities[p2+1:]
                add_one_to_p2 = False
                
            #remove any similar wifi plans as possibilities 
            elif plans[p1][1] == "wifi" and possibilities[p2][1] == "wifi":
                speed = possibilities[p2][2]
                if speed - 0.4*speed < plans[p1][2] and plans[p1][2] < speed + 0.4*speed:
                    if plans[p1][3] == possibilities[p2][3]:
                        possibilities = possibilities[:p2] + possibilities[p2+1:]
                        add_one_to_p2 = False
            
            if add_one_to_p2:
                p2 += 1
    
    if len(possibilities) != 0:
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        index = random.randint(0, len(possibilities)-1)
        experiment = possibilities[index]
        experiment[0] = isp[0]
        return [(experiment, index), 1, LenPlanExp, isp[8]]
    else:
        return None
    
    
def choose_plan_to_add_mobile_allowed(ISPs, isp, LenPlanExp, Seed):
    '''Function which randomly chooses a plan for an isp to experiment by stealing an idea off a competitor.'''
    
    global add_to_seed
    
    competitor = [isp[0]]
    while competitor[0] == isp[0] or competitor[9] <= 0: #don't steal idea off urself or a dead firm
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        competitor = random.choice(ISPs)
    possibilities = copy.deepcopy(competitor[1])
    plans = isp[1]
    
    for p1 in range(len(plans)):
        if plans[p1][0] != "PLAN GONE":
            p2 = 0
            while p2 < len(possibilities):
                add_one_to_p2 = True

                #remove any dead plans as possibilities
                if possibilities[p2][0] == "PLAN GONE":
                    possibilities = possibilities[:p2] + possibilities[p2+1:]
                    add_one_to_p2 = False

                #remove any mobile plans as possibilities
                elif possibilities[p2][1] == "mobile":
                    gb = possibilities[p2][2]
                    if gb < 50:
                        if gb - 4 < plans[p1][2] and plans[p1][2] < gb + 4:
                            possibilities = possibilities[:p2] + possibilities[p2+1:]
                            add_one_to_p2 = False
                    elif gb < 120:
                        if gb - 19 < plans[p1][2] and plans[p1][2] < gb + 19:
                            possibilities = possibilities[:p2] + possibilities[p2+1:]
                            add_one_to_p2 = False
                    else:
                        if gb - 49 < plans[p1][2] and plans[p1][2] < gb + 49:
                            possibilities = possibilities[:p2] + possibilities[p2+1:]
                            add_one_to_p2 = False

                #remove any similar wifi plans as possibilities 
                elif plans[p1][1] == "wifi" and possibilities[p2][1] == "wifi":
                    speed = possibilities[p2][2]
                    if speed - 0.4*speed < plans[p1][2] and plans[p1][2] < speed + 0.4*speed:
                        if plans[p1][3] == possibilities[p2][3]:
                            possibilities = possibilities[:p2] + possibilities[p2+1:]
                            add_one_to_p2 = False
                if add_one_to_p2:
                    p2 += 1
    
    #randomly pick plan to steal
    if len(possibilities) != 0:
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        index = random.randint(0, len(possibilities)-1)
        chosen = possibilities[index]
        
        #change plan to thier own branding
        location, supplier = None, None
        for p in plans:
            if p[1] == chosen[1]:
                location = p[3]
                supplier = p[5]
                break
        if location == None:
            location = chosen[3]
            supplier = chosen[5]
        experiment = [None, None, None, None, None, None]
        experiment[0] = isp[0]
        experiment[1] = chosen[1]
        experiment[2] = chosen[2]
        experiment[3] = location
        experiment[4] = chosen[4]
        experiment[5] = supplier
        return [(experiment, index), 1, LenPlanExp, isp[8]]
    else:
        return None

    
def all_agents_updates(grid, ISPs, replacements, dynamic_switching_costs, switchers, SwitchingCostIncrease, IncomeBudget, TimeBudget, MarketingBudget, PrSacrificeWifi, PrPickBetterValue, Seed):
    '''This function prompts those experiencing a "real problem" (paying over their budget on a plan or 
    completely getting their plan erased from price and plan experiments), to immeadiately reassess their plan,
    and simultaneously collects affordability info across the grid for later graphing
    '''
    global add_to_seed
    
    num_real_problems = 0
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1] == True:
                
                #update switching costs
                if switchers[row, cell] == 0:
                    if dynamic_switching_costs[row, cell] < 1:
                        dynamic_switching_costs[row, cell] += SwitchingCostIncrease
                else:
                    dynamic_switching_costs[row, cell] = 0
                switchers[row, cell] = 0 #reset switchers array
                
                bundle = grid[row, cell, 3]
                bundle_update_trigger = False
                if bundle != (None, None): #checking to see if they're connected
                    
                    if bundle[1] != None and bundle[1][0] == "PLAN GONE":
                        replacement = replacements[bundle[1][1]]
                        if replacement[1] == None:
                            grid[row, cell, 3] = (bundle[0], None)
                            bundle_update_trigger = True
                        else:
                            isp = replacement[0]
                            plan = replacement[1]
                            grid[row, cell, 3] = (bundle[0], ISPs[isp][1][plan])
                                
                    #for anyone suddenly paying over their budget, find a new plan immeadiately
                    bundle = grid[row, cell, 3]
                    income = grid[row, cell, 2]
                    percent_spent_on_bundle = decide_expenditure(bundle, income)
                    if percent_spent_on_bundle == None or percent_spent_on_bundle >= IncomeBudget * 100:
                        bundle_update_trigger = True
                
                else: 
                    bundle_update_trigger = True #if disconnected, search for a plan
                    
                if bundle_update_trigger:
                    complete_bundles, mobile_plans, wifi_plans = prep_bundles(grid[row, cell], ISPs, TimeBudget, MarketingBudget, operator_locations, Seed)
                    new_bundle = decide_bundle(grid[row, cell], complete_bundles, mobile_plans, wifi_plans, PrSacrificeWifi, PrPickBetterValue, IncomeBudget, Seed)
                    percent_spent_on_new_bundle = decide_expenditure(new_bundle, income)
                    #perform updates
                    grid[row, cell, 3] = new_bundle
                    grid[row, cell, 4] = percent_spent_on_new_bundle
                    switchers[row, cell] = 1
                    num_real_problems += 1 #only want to perform a certain number of plan-reassessments per iteration to keep things faster and realistic
                else:
                    grid[row, cell, 4] = decide_expenditure(grid[row, cell, 3], income)
                   
    return num_real_problems, dynamic_switching_costs, switchers



def choose_contemplators(num_imaginary_problems, grid, Seed):
    '''Function which chooses a random unique subset of the population to experience an "imaginary problem" 
    which makes them contemplate switching bundles
    '''
    global add_to_seed
    
    contemplators = []
    rows = [(y, []) for y in range(100)]
    cols = [(x, []) for x in range(100)]
    iteration = 0
    
    if num_imaginary_problems < 0:
        return []
        
    if num_imaginary_problems > len(rows)*len(cols):
        num_imaginary_problems = len(rows)*len(cols)
        
    num_iteration_repeats = 0 #if num_iteration_repeats > 50 I'm taking this to mean that their are no more unique people to choose therefore early stopping condition
    while (len(contemplators) < num_imaginary_problems) and (num_iteration_repeats < 50): 
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        y = random.choice(rows)
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        x = random.choice(cols)
        
        if grid[y[0], x[0], 1]: #if the randomly generated cell isn't empty
            duplicate = False
            for t1 in y[1]:
                for t2 in x[1]:
                    if t1 == t2:
                        duplicate = True
                        num_iteration_repeats += 1
            if not duplicate:
                contemplators.append((x[0], y[0]))
                y[1].append(iteration)
                x[1].append(iteration)
                rows[y[0]] = (y)
                cols[x[0]] = (x)
                iteration += 1
    
    return contemplators


def choose_preperators(contemplators, dynamic_switching_costs, switchers, Seed):
    '''simple function to randomly select a subset of the contemplating agents to go through with stage 3 
    of the decision making process based on the concept of overcoming a "switching cost"
    '''
    global add_to_seed
    
    preparators = []
    for person in contemplators:
        row = person[0]
        cell = person[1]
        random.seed(Seed + add_to_seed)
        add_to_seed += 23
        if random.random() > dynamic_switching_costs[row, cell]:
            preparators.append(person)
    return preparators


def perform_grid_cleaning(grid):
    '''cleaning up the all the grid[row, cell, 4]s at the end of a simulation run
    as grid[row, cell, 4] needs updating only when a user is randomly chosen until very end'''
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1] == True:
                final_bundle = grid[row, cell, 3]
                percent_spent_on_final_bundle = decide_expenditure(final_bundle, grid[row, cell, 2])
                grid[row, cell, 4] = percent_spent_on_final_bundle
                
                
                
                
                
                
                
                
                
'''
--------------------------------- FUNCTIONS TO TRACK OUTPUT DATA POINTS ---------------------------------
'''                
                
                
                
                
                
                
                
                
                
                
                

def initialise_quintile_structures(grid):
    
    total_population = 0
    quintile_structure = np.zeros((100, 100), dtype=object)
    threshholds = find_the_quintiles(grid)
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                total_population += 1
            
            #find the correct quintile
                income = grid[row, cell, 2]
                if income < threshholds[0]:
                    quintile = 1
                elif income < threshholds[1]:
                    quintile = 2
                elif income < threshholds[2]:
                    quintile = 3
                elif income < threshholds[3]:
                    quintile = 4
                else:
                    quintile = 5
                quintile_structure[row, cell] = quintile

    populations = [0]*len(threshholds)
    for row in range(100):
        for cell in range(100):
            q = quintile_structure[row, cell]
            if q != 0:
                populations[q - 1] +=1

    return quintile_structure, populations, total_population


def initialise_RA_structures(grid):
    
    RA_structure = np.zeros((100, 100), dtype=object)
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                #determine correct RA
                if row < 50 and cell < 50: #urban
                    RA_structure[row, cell] = 1
                elif row >= 50 and cell >= 50: #remote
                    RA_structure[row, cell] = 3
                else: #regional
                    RA_structure[row, cell] = 2
    
    populations = [0, 0, 0]
    for row in range(100):
        for cell in range(100):
            RA = RA_structure[row, cell]
            if RA != 0:
                populations[RA - 1] += 1
    
    return RA_structure, populations


def update_data_stores(ISPs, grid, total_population, affordability_by_quintile, affordability_by_RA, bundle_types_by_quintile, bundle_types_by_RA, subs_per_service, RA_wifi_prices, RA_mobile_prices, quintile_mobile_prices, HHIs, quintiles, pop_by_quintile, RAs, pop_by_RA):
    
    min_good_mobile_price = [999999999, 999999999, 999999999] 
    min_good_wifi_price = [999999999, 999999999, 999999999]
    for isp in ISPs:
        for plan in isp[1]:
            if plan[1] == "mobile":
                if plan[2] > 61:
                    if plan_available_in_my_area(plan, 0): 
                        if plan[4] < min_good_mobile_price[0]:
                            min_good_mobile_price[0] = plan[4]
                    if plan_available_in_my_area(plan, 1):
                        if plan[4] < min_good_mobile_price[1]:
                            min_good_mobile_price[1] = plan[4]
                    if plan_available_in_my_area(plan, 3):
                        if plan[4] < min_good_mobile_price[2]:
                            min_good_mobile_price[2] = plan[4]
            elif plan[1] == "wifi":
                if plan[2] >= 50:
                    if plan_available_in_my_area(plan, 0): 
                        if plan[4] < min_good_wifi_price[0]:
                            min_good_wifi_price[0] = plan[4]
                    if plan_available_in_my_area(plan, 1):
                        if plan[4] < min_good_wifi_price[1]:
                            min_good_wifi_price[1] = plan[4]
                    if plan_available_in_my_area(plan, 3):
                        if plan[4] < min_good_wifi_price[2]:
                            min_good_wifi_price[2] = plan[4]
    min_good_bundle_price = []
    for ra in range(3):
        min_good_bundle_price.append(min_good_mobile_price[ra] + min_good_wifi_price[ra])
    
    #quintiles [<2, <5, <10, >=10, non-complete connection, no_connection]
    quintiles_this_timestep = [
        np.array([0, 0, 0, 0, 0, 0]), #q1
        np.array([0, 0, 0, 0, 0, 0]), #q2
        np.array([0, 0, 0, 0, 0, 0]), #q3
        np.array([0, 0, 0, 0, 0, 0]), #q4
        np.array([0, 0, 0, 0, 0, 0])] #q5
    
    #RAs [<2, <5, <10, >=10, one only, no_connection]
    RAs_this_timestep = [
        np.array([0, 0, 0, 0, 0, 0]), #urban
        np.array([0, 0, 0, 0, 0, 0]), #regional
        np.array([0, 0, 0, 0, 0, 0])] #remote
    
    #bundle types
    bundles_quint_this_timestep = [
        np.array([0, 0, 0, 0]), # [complete, mobile-only, wifi-only, disconnected]
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0])]
    
    bundles_ra_this_timestep = [
        np.array([0, 0, 0, 0]), # [complete, mobile-only, wifi-only, disconnected]
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0])]
    
    #subs and prices per service
    speeds = [12, 25, 50, 100, 250, 1000]
    subs_this_timestep = [0, 0, 0, 0, 0, 0]
    wifi_price_ra_this_timestep = [
        np.array([0, 0, 0, 0, 0, 0]), #urban
        np.array([0, 0, 0, 0, 0, 0]), #regional
        np.array([0, 0, 0, 0, 0, 0])] #remote
    totals_wifi_price_ra = [
        np.array([0, 0, 0, 0, 0, 0]), #urban
        np.array([0, 0, 0, 0, 0, 0]), #regional
        np.array([0, 0, 0, 0, 0, 0])] #remote
    
    #mobile subs
    mobile_price_ra_this_timestep = np.array([0, 0, 0])
    totals_mobile_price_ra = [0, 0, 0]
    mobile_price_quint_this_timestep = np.array([0, 0, 0, 0, 0])
    totals_mobile_price_quint = [0, 0, 0, 0, 0]
    
    #HHIs
    mobile_totals = [0]*len(ISPs)
    wifi_totals = [0]*len(ISPs)
    
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                
                #update affordabilities
                quintile = quintiles[row, cell]
                RA = RAs[row, cell]
                percent = min_good_bundle_price[RA - 1]/grid[row, cell, 2] * 100
                
                if percent == None:
                    index = 5
                    bundle_type = 3
                else:
                    mplan = grid[row, cell, 3][0]
                    wplan = grid[row, cell, 3][1]
                    if mplan == None or wplan == None:
                        bundle_type = 1
                        index = 4
                        if mplan == None:
                            bundle_type = 2
                    elif percent < 2:
                        index = 0
                        bundle_type = 0
                    elif percent < 5:
                        index = 1
                        bundle_type = 0
                    elif percent < 10:
                        index = 2
                        bundle_type = 0
                    else:
                        index = 3
                        bundle_type = 0
                quintiles_this_timestep[quintile - 1][index] += 1
                bundles_quint_this_timestep[quintile - 1][bundle_type] += 1
                RAs_this_timestep[RA - 1][index] += 1
                bundles_ra_this_timestep[RA - 1][bundle_type] += 1
                        
                #update subscribers and prices per service for wifi 
                if wplan != None:
                    s2 = wplan[2]
                    for s1 in range(len(speeds)):
                        if speeds[s1] >= s2:
                            speed = s1
                            break
                    subs_this_timestep[speed] += 1
                    wifi_price_ra_this_timestep[RA - 1][speed] += wplan[4]
                    totals_wifi_price_ra[RA - 1][speed] += 1
                
                #update price and subs per service mobile
                if mplan != None:
                    mobile_price_ra_this_timestep[RA - 1] += mplan[4]
                    totals_mobile_price_ra[RA - 1] += 1
                    mobile_price_quint_this_timestep[quintile - 1] += mplan[4]
                    totals_mobile_price_quint[quintile - 1] += 1
                
                #update market shares
                if mplan != None:
                    isp_name = mplan[0]
                    for potential_isp in range(len(ISPs)):
                        if ISPs[potential_isp][0] == isp_name:
                            isp_index = potential_isp
                            break
                    mobile_totals[isp_index] += 1
                if wplan != None:
                    isp_name = wplan[0]
                    for potential_isp in range(len(ISPs)):
                        if ISPs[potential_isp][0] == isp_name:
                            isp_index = potential_isp
                            break
                    wifi_totals[isp_index] += 1
    
    # perform calculations needed
    for RA in range(3):
        for speed in range(6):
            if wifi_price_ra_this_timestep[RA][speed] != 0:
                wifi_price_ra_this_timestep[RA][speed] = wifi_price_ra_this_timestep[RA][speed]/totals_wifi_price_ra[RA][speed]
    for ra in range(3):
        mobile_price_ra_this_timestep[ra] = mobile_price_ra_this_timestep[ra]/totals_mobile_price_ra[ra]
    for q in range(5):
        mobile_price_quint_this_timestep[q] = mobile_price_quint_this_timestep[q]/totals_mobile_price_quint[q]
    
    mobile_squares = np.array(mobile_totals)^2
    wifi_squares = np.array(wifi_totals)^2

    #perform updates
    affordability_by_quintile.append(quintiles_this_timestep)
    affordability_by_RA.append(RAs_this_timestep)
    bundle_types_by_quintile.append(bundles_quint_this_timestep)
    bundle_types_by_RA.append(bundles_ra_this_timestep)
    subs_per_service.append(subs_this_timestep)
    RA_wifi_prices.append(wifi_price_ra_this_timestep)
    RA_mobile_prices.append(mobile_price_ra_this_timestep)
    quintile_mobile_prices.append(mobile_price_quint_this_timestep)
    HHIs.append((sum(mobile_squares), sum(wifi_squares)))
    
def update_data_stores_under_hood(ISPs, grid, total_population, affordability_by_quintile, affordability_by_RA, bundle_types_by_quintile, bundle_types_by_RA, subs_per_service, RA_wifi_prices, RA_mobile_prices, quintile_mobile_prices, HHIs, quintiles, pop_by_quintile, RAs, pop_by_RA):
    
    speeds = [12, 25, 50, 100, 250, 1000]
    avg_prices_urb = [0, 0, 0, 0, 0, 0]
    avg_prices_reg = [0, 0, 0, 0, 0, 0]
    avg_prices_rem = [0, 0, 0, 0, 0, 0]
    nums_urb = [0, 0, 0, 0, 0, 0]
    nums_reg = [0, 0, 0, 0, 0, 0]
    nums_rem = [0, 0, 0, 0, 0, 0]
    for isp in ISPs:
        for plan in isp[1]:
            if plan[1] == "wifi":
                for speed in range(len(speeds)):
                    if plan[2] <= speeds[speed]:
                        if plan[3] == "urban":
                            avg_prices_urb[speed] += plan[4]
                            nums_urb[speed] += 1
                        elif plan[3] == "regional":
                            avg_prices_reg[speed] += plan[4]
                            nums_reg[speed] += 1
                        else:
                            avg_prices_rem[speed] += plan[4]
                            nums_rem[speed] += 1
                        break
    for speed in range(6):
        if nums_urb[speed] > 0:
            avg_prices_urb[speed] = avg_prices_urb[speed]/nums_urb[speed]
        if nums_reg[speed] > 0:
            avg_prices_reg[speed] = avg_prices_reg[speed]/nums_reg[speed]
        if nums_rem[speed] > 0:
            avg_prices_rem[speed] = avg_prices_rem[speed]/nums_rem[speed]
    wifi_price_ra_this_timestep = [avg_prices_urb, avg_prices_reg, avg_prices_rem]
    
    
    #quintiles [<2, <5, <10, >=10, non-complete connection, no_connection]
    quintiles_this_timestep = [
        np.array([0, 0, 0, 0, 0, 0]), #q1
        np.array([0, 0, 0, 0, 0, 0]), #q2
        np.array([0, 0, 0, 0, 0, 0]), #q3
        np.array([0, 0, 0, 0, 0, 0]), #q4
        np.array([0, 0, 0, 0, 0, 0])] #q5
    
    #RAs [<2, <5, <10, >=10, one only, no_connection]
    RAs_this_timestep = [
        np.array([0, 0, 0, 0, 0, 0]), #urban
        np.array([0, 0, 0, 0, 0, 0]), #regional
        np.array([0, 0, 0, 0, 0, 0])] #remote
    
    #bundle types
    bundles_quint_this_timestep = [
        np.array([0, 0, 0, 0]), # [complete, mobile-only, wifi-only, disconnected]
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0])]
    
    bundles_ra_this_timestep = [
        np.array([0, 0, 0, 0]), # [complete, mobile-only, wifi-only, disconnected]
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 0, 0])]
    
    
    #HHIs
    mobile_totals = [0]*len(ISPs)
    wifi_totals = [0]*len(ISPs)
    
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                
                #update affordabilities
                quintile = quintiles[row, cell]
                RA = RAs[row, cell]
                percent = grid[row, cell, 4]
                if percent == None:
                    index = 5
                    bundle_type = 3
                else:
                    mplan = grid[row, cell, 3][0]
                    wplan = grid[row, cell, 3][1]
                    if mplan == None or wplan == None:
                        index = 4
                        bundle_type = 1
                        if mplan == None:
                            bundle_type = 2
                    elif percent < 2:
                        index = 0
                        bundle_type = 0
                    elif percent < 5:
                        index = 1
                        bundle_type = 0
                    elif percent < 10:
                        index = 2
                        bundle_type = 0
                    else:
                        index = 3
                        bundle_type = 0
                quintiles_this_timestep[quintile - 1][index] += 1
                bundles_quint_this_timestep[quintile - 1][bundle_type] += 1
                RAs_this_timestep[RA - 1][index] += 1
                bundles_ra_this_timestep[RA - 1][bundle_type] += 1
                        
                
                #update market shares
                if mplan != None:
                    isp_name = mplan[0]
                    for potential_isp in range(len(ISPs)):
                        if ISPs[potential_isp][0] == isp_name:
                            isp_index = potential_isp
                            break
                    mobile_totals[isp_index] += 1
                if wplan != None:
                    isp_name = wplan[0]
                    for potential_isp in range(len(ISPs)):
                        if ISPs[potential_isp][0] == isp_name:
                            isp_index = potential_isp
                            break
                    wifi_totals[isp_index] += 1
    
    
    mobile_squares = np.array(mobile_totals)^2
    wifi_squares = np.array(wifi_totals)^2

    #perform updates
    affordability_by_quintile.append(quintiles_this_timestep)
    affordability_by_RA.append(RAs_this_timestep)
    bundle_types_by_quintile.append(bundles_quint_this_timestep)
    bundle_types_by_RA.append(bundles_ra_this_timestep)
    RA_wifi_prices.append(wifi_price_ra_this_timestep)
    HHIs.append((sum(mobile_squares), sum(wifi_squares)))
    
    
def update_data_stores3(ISPs, grid, total_population, affordability_by_quintile, affordability_by_RA, bundle_types_by_quintile, bundle_types_by_RA, subs_per_service, RA_wifi_prices, RA_mobile_prices, quintile_mobile_prices, HHIs, quintiles, pop_by_quintile, RAs, pop_by_RA, per_GBs):
    
    mobile_subs = np.array([0 for _ in range(len(ISPs))])
    wifi_subs = np.array([0 for _ in range(len(ISPs))])
    
    for row in range(100):
        for cell in range(100):
            if grid[row, cell, 1]:
                mplan = grid[row, cell, 3][0]
                wplan = grid[row, cell, 3][1]
                
                #update subs
                if mplan != None:
                    isp_name = mplan[0]
                    for potential_isp in range(len(ISPs)):
                        if ISPs[potential_isp][0] == isp_name:
                            isp_index = potential_isp
                            break
                    mobile_subs[isp_index] += 1
                if wplan != None:
                    isp_name = wplan[0]
                    for potential_isp in range(len(ISPs)):
                        if ISPs[potential_isp][0] == isp_name:
                            isp_index = potential_isp
                            break
                    wifi_subs[isp_index] += 1
    
    prices_per_GB = []
    for isp in ISPs:
        for plan in isp[1]:
            if plan[1] == "mobile":
                prices_per_GB.append(plan[4]/plan[2])
    price_per_GB = sum(prices_per_GB)/len(prices_per_GB)
    
    total_m_users = sum(mobile_subs)
    total_w_users = sum(wifi_subs)
    m_market_shares = []
    w_market_shares = []
    for i in range(len(mobile_subs)):
        m_market_shares.append(mobile_subs[i] / total_m_users * 100)
        w_market_shares.append(wifi_subs[i] / total_w_users * 100)
    mobile_squares = np.array(m_market_shares)**2
    wifi_squares = np.array(w_market_shares)**2 
    
    HHIs.append((sum(mobile_squares), sum(wifi_squares)))
    per_GBs.append(price_per_GB)
    
    
    
    
    
    
'''
--------------------------------- FINAL SIMULATION FUNCTION AND SIMULATION-RUNNING FUNCTION ---------------------------------
'''  
    
    
    
    
    
    
    
    
    
    
    
def simulate_market_dynamics(LargeMarkup, SmallMarkup, ResellerOperatingFee, WholesalerOperatingFee, MarketingBudget, PrPriceExp, LenPriceExp, PercentPriceChange, PrPlanExp, LenPlanExp, NumDissatisfied, SwitchingCostIncrease, TimeBudget, IncomeBudget, PrSacrificeWifi, PrPickBetterValue, Seed, MaxIter):
    '''Main simulation function designed to simulate how internet prices change over time.'''
    
    #initialise data storage for later graphing
    affordability_by_quintile = []
    affordability_by_RA = []
    bundle_types_by_quintile = []
    bundle_types_by_RA = []
    subs_per_service = []
    RA_wifi_prices = []
    RA_mobile_prices = []
    quintile_mobile_prices = []
    real_probs = []
    HHIs = []
    switching_cost_changes = []
    per_GBs = []
    
    nbn_co_revenue_changes = []
    profit_changes = [[] for _ in range(len(ISPs))]
    
    #initialise quick-referencable data structures
    dynamic_switching_costs = np.zeros((100, 100), dtype=object) #initialise an grid with switching costs that will change
    switchers = np.zeros((100, 100), dtype=object) #initialise an grid to keep track of who should reset their switching cost next iteration
    quintiles, pop_by_quintile, total_population = initialise_quintile_structures(grid)
    RAs, pop_by_RA = initialise_RA_structures(grid)
    global add_to_seed
    
    for i in tqdm(range(MaxIter)):
        
        Seed = Seed + 10*i
        
        if i%25 == 0:
            update_data_stores3(ISPs, grid, total_population, affordability_by_quintile, affordability_by_RA, bundle_types_by_quintile, bundle_types_by_RA, subs_per_service, RA_wifi_prices, RA_mobile_prices, quintile_mobile_prices, HHIs, quintiles, pop_by_quintile, RAs, pop_by_RA, per_GBs)
            total_sc = 0
            for row in range(100):
                for cell in range(100):
                    total_sc += dynamic_switching_costs[row, cell]
            switching_cost_changes.append(total_sc/total_population)   
                
        #ISP stuff
        profits, nbn_revenue = update_ISP_profits_and_moneypool(ISPs, grid, LargeMarkup, SmallMarkup, ResellerOperatingFee, WholesalerOperatingFee, MarketingBudget, profit_changes, nbn_co_revenue_changes)
        #if i%25 == 0:
            #for p in range(len(profits)):
                #profit_changes[p].append(profits[p])
            #nbn_co_revenue_changes.append(nbn_revenue)
        check_for_bankruptcy(ISPs, operator_locations) 
        review_price_experiments(ISPs, PrPriceExp, LenPriceExp, PercentPriceChange, Seed)
        replacements = review_plan_experiments(ISPs, PrPlanExp, LenPlanExp, Seed)
        
        #user stuff
        
        #1: update switching costs and bundles for those who's plans got affected by experiments
        num_real_problems, dynamic_switching_costs, switchers = all_agents_updates(grid, ISPs, replacements, dynamic_switching_costs, switchers, SwitchingCostIncrease, IncomeBudget, TimeBudget, MarketingBudget, PrSacrificeWifi, PrPickBetterValue, Seed)
        #if i%25 == 0:
            #real_probs.append(num_real_problems)
            #print(num_real_problems)

        #2: push random person agents through the 4 stage decision making process
        
        #choose agents to enter stage 2 (pre-contemplation -> contemplation)
        if num_real_problems < NumDissatisfied:
            num_imaginary_problems = NumDissatisfied - num_real_problems
            contemplators = choose_contemplators(num_imaginary_problems, grid, Seed)

            #perform stage 2 (choosing agents to enter stage 3 (contemplating change -> preparing for change))
            preparators = choose_preperators(contemplators, dynamic_switching_costs, switchers, Seed)

            #perform stage 3 (preparation)
            for person in preparators:
                row = person[1]
                cell = person[0]
                complete_bundles, mobile_plans, wifi_plans = prep_bundles(grid[row, cell], ISPs, TimeBudget, MarketingBudget, operator_locations, Seed)

                #peform stage 4 (action)
                new_bundle = decide_bundle(grid[row, cell], complete_bundles, mobile_plans, wifi_plans, PrSacrificeWifi, PrPickBetterValue, IncomeBudget, Seed)
                percent_spent_on_new_bundle = decide_expenditure(new_bundle, grid[row, cell, 2])
                #perform updates
                grid[row, cell, 3] = new_bundle
                grid[row, cell, 4] = percent_spent_on_new_bundle
                switchers[row, cell] = 1
    
    #cleaning data, returning it
    perform_grid_cleaning(grid)
    #return [real_probs, affordability_by_quintile, affordability_by_RA, bundle_types_by_quintile, bundle_types_by_RA, subs_per_service, RA_wifi_prices, RA_mobile_prices, quintile_mobile_prices, HHIs, nbn_co_revenue_changes, total_population, switching_cost_changes]
    return [HHIs, per_GBs]





def run_simulation(StartingMarket, InitialMoneyPool, LargeMarkup, SmallMarkup, ResellerOperatingFee, WholesalerOperatingFee, MarketingBudget, PrPriceExp, LenPriceExp, PercentPriceChange, PrPlanExp, LenPlanExp, NumDissatisfied, SwitchingCostIncrease, TimeBudget, IncomeBudget, PrSacrificeWifi, PrPickBetterValue, Seed, MaxIter):
    
    #itialisation
    global add_to_seed
    add_to_seed = 0
    global ISPs
    global operator_locations
    global grid
    ISPs, operator_locations = initialise_ISPs(StartingMarket, InitialMoneyPool)
    grid = initialise_grid(TimeBudget, IncomeBudget, MarketingBudget, PrSacrificeWifi, PrPickBetterValue, Seed)
    initial_grid = copy.deepcopy(grid)
    
    #simulation
    data = simulate_market_dynamics(LargeMarkup, SmallMarkup, ResellerOperatingFee, WholesalerOperatingFee, MarketingBudget, PrPriceExp, LenPriceExp, PercentPriceChange, PrPlanExp, LenPlanExp, NumDissatisfied, SwitchingCostIncrease, TimeBudget, IncomeBudget, PrSacrificeWifi, PrPickBetterValue, Seed, MaxIter)
    final_grid = copy.deepcopy(grid)
    
    return data







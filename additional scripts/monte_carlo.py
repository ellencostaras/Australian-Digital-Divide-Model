import multiprocessing
from ADD_model_python import run_simulation
import gc

def run_single_simulation(params_seed_MaxIter):
    '''Function to run a single instance of the simulation'''

    params, seed, MaxIter = params_seed_MaxIter
    params['Seed'] = seed
    params['MaxIter'] = MaxIter

    try:
        data = run_simulation(**params)
        return data
    except Exception as e:
        print(f"Run {seed} with params {params} failed: {e}")
        return None

    gc.collect()
    
    return data

def monte_carlo_parallel(runs, params, MaxIter):
    '''Function to run monte carlo simulation in parallel'''

    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

    params_seed_MaxIter = [(params.copy(), run, MaxIter) for run in range(runs)]
    results = pool.map(run_single_simulation, params_seed_MaxIter)

    pool.close()
    pool.join()

    results = [result for result in results if result is not None] #None result means simulation failed
    return results








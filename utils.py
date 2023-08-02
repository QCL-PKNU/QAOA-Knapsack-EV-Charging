import numpy as np

from functools import partial
from qiskit import transpile, Aer, execute, IBMQ
from scipy.optimize import shgo
from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer import AerSimulator
from qiskit.quantum_info import SparsePauliOp 

# Fake Backend
from qiskit.providers.fake_provider import FakeManilaV2

from qiskit_ibm_runtime import Session, Sampler, Estimator, QiskitRuntimeService

from EV_knapsack import EV

provider = IBMQ.load_account()
bk = provider.get_backend('ibm_perth')
noise_model = NoiseModel.from_backend(bk)

backend = Aer.get_backend("aer_simulator_statevector")
# backend = AerSimulator.from_backend(bk)

# Real Backend
real_qc_backend = provider.get_backend('ibm_nairobi')

# Fake Backend
# real_qc_backend = FakeManilaV2()


is_adding_noise_model = False


def bitstring_to_selection_choices(bitstring, ev: EV):
    bits = np.array(list(map(int, list(bitstring))))[::-1]
    selection = np.array(bits[:ev.number_of_evs])
    return selection


def objective_function(bitstring, ev: EV, a):
    """The objective function of the linear penalty based approach."""
    selection = bitstring_to_selection_choices(bitstring, ev)
    time_required = selection.dot(ev.time_required)
    power_required = selection.dot(ev.power_required)
    if power_required > ev.max_power:
        penalty = a * (power_required - ev.max_power)
    else:
        penalty = 0
    return time_required - penalty


def to_parameter_dict(angles, a, circuit):
    """Create a circuit specific parameter dict from given parameters.
    angles = np.array([gamma0, beta0, gamma1, beta1, ...])"""
    gammas = angles[0::2]
    betas = angles[1::2]
    parameters = {}
    for parameter, value in zip(circuit.betas, betas):
        parameters[parameter] = value
    for parameter, value in zip(circuit.gammas, gammas):
        parameters[parameter] = value
    parameters[circuit.a] = float(a)
    return parameters


def get_probs_dict(circuit, ev, angles, a):
    """Simulate circuit for given parameters and return probability dict."""
    transpiled_circuit = transpile(circuit, backend)
    parameter_dict = to_parameter_dict(angles, a, circuit)
    statevector = get_statevector(transpiled_circuit, parameter_dict)
    probs_dict = statevector.probabilities_dict(range(ev.number_of_evs))
    return probs_dict


def find_optimal_angles(circuit, ev, a):
    """Optimize the parameters beta, gamma for given circuit and parameters."""
    circuit.save_statevector()
    circuit.measure_all()

    transpiled_circuit = transpile(circuit, backend)
    obj = partial(objective_function, ev=ev, a=a)
    angles_to_parameters = partial(to_parameter_dict, circuit=circuit, a=a)

    def angles_to_value(angles):
        parameter_dict = angles_to_parameters(angles)
        statevector = get_statevector(transpiled_circuit, parameter_dict)
        probs_dict = statevector.probabilities_dict()
        value = - average_value(probs_dict, obj)
        return value

    return optimize_angles(circuit.p, angles_to_value,
                        circuit.gamma_range(a),
                        circuit.beta_range())


def get_statevector(transpiled_circuit, parameter_dict):
    bound_circuit = transpiled_circuit.bind_parameters(parameter_dict)
    if is_adding_noise_model:
        job = execute(bound_circuit, backend, shots=1, noise_model=noise_model)
    else:
        job = execute(bound_circuit, backend, shots=1)
    result = job.result()
    statevector = result.get_statevector()
    return statevector


def average_value(probs_dict, func):
    bitstrings = list(probs_dict.keys())
    values = np.array(list(map(func, bitstrings)))
    probs = np.array(list(probs_dict.values()))
    return sum(values * probs)


def optimize_angles(p, angles_to_value, gamma_range, beta_range):
    bounds = np.array([gamma_range, beta_range] * p)
    result = shgo(angles_to_value, bounds, iters=3)
    return result.x


def approximation_ratio(circuit, ev: EV, p, a):
    """Calculate the approximation ratio of the linqaoa approach for given ev and parameters."""
    expectation = comparable_expectation_value(circuit, ev, p, a)
    best = best_known_solutions(ev)
    choice = best[0]
    best_value = value(choice, ev)
    ratio = expectation / best_value
    return ratio


def comparable_objective_function(bitstring, ev):
    """An approach independent objective function"""
    choice = bitstring_to_selection_choices(bitstring, ev)
    if is_choice_feasible(choice, ev):
        return value(choice, ev)
    return 0


def comparable_expectation_value(circuit, ev: EV, p, a):
    """Calculate the expectation value of the approach independent objective function for given parameters."""
    angles = find_optimal_angles(circuit, ev, a)
    probs = get_probs_dict(circuit, ev, angles, a)
    obj = partial(comparable_objective_function, ev=ev)
    expectation = average_value(probs, obj)
    return expectation


def value(choice, ev: EV):
    """Return the value of an item choice."""
    return choice.dot(ev.time_required)
    

def power_required(choice, ev):
    return choice.dot(ev.power_required)


def time_required(choice, ev):
    return choice.dot(ev.time_required)


def is_choice_feasible(choice, ev):
    return power_required(choice, ev) <= ev.max_power


def best_known_solutions(ev: EV):
    def choices_from_number(ev, number):
        return np.array(list(map(int, list(reversed(bin(number)[2:])))) + [0] * (ev.number_of_evs - len(bin(number)[2:])))
    best = 0
    solutions = []
    for i in range(2**ev.number_of_evs):
        choice = choices_from_number(ev, i)
        value = choice.dot(ev.time_required)
        weight = choice.dot(ev.power_required)
        is_legal = weight <= ev.max_power
        if is_legal and value > best:
            best = value
            solutions = [choice]
        elif is_legal and value == best:
            solutions.append(choice)
    return np.array(solutions)


# Due to the real device doesn't have statevector, we need to use the counts simulator
def approximation_ratio_on_real_device(circuit, problem, angles, p, a):
    circuit.measure_all()
    probs = get_probs_dict_on_real_device(circuit, problem, angles, a)
    
    prob_dist = {}
    for key, v in probs.items():
        prefix = key[:problem.number_of_evs]
        if prefix not in prob_dist:
            prob_dist[prefix] = 0
        prob_dist[prefix] += (v / 2048)

    obj = partial(comparable_objective_function, ev=problem)
    expectation = average_value(prob_dist, obj)
    best = best_known_solutions(problem)
    choice = best[0]
    best_value = value(choice, problem)
    ratio = expectation / best_value
    return ratio


def get_probs_dict_on_real_device(circuit, ev, angles, a):
    transpiled_circuit = transpile(circuit, backend)
    parameter_dict = to_parameter_dict(angles, a, circuit)
    bound_circuit = transpiled_circuit.bind_parameters(parameter_dict)
    job = real_qc_backend.run(bound_circuit, shots=2048)
    result = job.result()
    counts = result.get_counts()
    return counts
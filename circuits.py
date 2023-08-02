import math
from fractions import Fraction
from functools import partial

import numpy as np
from EV_knapsack import EV

from qiskit import (QuantumCircuit, QuantumRegister)
from qiskit.circuit import Parameter


class Add(QuantumCircuit):
    def __init__(self, register, n, control=None):
        """Initialize the Circuit."""
        self.register = register
        self.control = control
        qubits = [*register, *control] if control is not None else register
        super().__init__(qubits, name=f"Add {n}")
        binary = list(map(int, reversed(bin(n)[2:])))
        for idx, value in enumerate(binary):
            if value:
                self._add_power_of_two(idx)

    def _add_power_of_two(self, k):
        phase_gate = super().p
        if self.control is not None:
            phase_gate = partial(super().cp, target_qubit=self.control)
        for idx, qubit in enumerate(self.register):
            l = idx + 1
            if l > k:
                m = l - k
                phase_gate(2 * np.pi / 2**m, qubit)


class TotalPowerComputation(QuantumCircuit):
    def __init__(self, choice_reg, power_req_reg, flag_qubit, ev: EV, clean_up=True):
        c = math.floor(math.log2(ev.max_power)) + 1
        power_0 = 2**c - ev.max_power - 1

        subcirc = QuantumCircuit(choice_reg, power_req_reg, name="")
        for qubit, power in zip(choice_reg, ev.power_required):
            adder = Add(power_req_reg, power, control=[qubit]).to_instruction()
            subcirc.append(adder, [*power_req_reg, qubit])
        adder = Add(power_req_reg, power_0)
        subcirc.append(adder.to_instruction(), power_req_reg)

        super().__init__(choice_reg, power_req_reg, flag_qubit, name="U_v")
        super().append(subcirc.to_instruction(), [*choice_reg, *power_req_reg])
        super().x(power_req_reg[c:])
        super().mcx(power_req_reg[c:], flag_qubit)
        super().x(power_req_reg[c:])
        if clean_up:
            super().append(subcirc.inverse().to_instruction(), [*choice_reg, *power_req_reg])


class TimeComputation(QuantumCircuit):
    """Time computation of an picked EV."""
    def __init__(self, choice_reg, ev):
        """Initialize the circuit."""
        self.gamma = Parameter("gamma")
        super().__init__(choice_reg, name="Time Computation")
        for qubit, value in zip(choice_reg, ev.time_required):
            super().p(- self.gamma * value, qubit)


class PhaseOperator(QuantumCircuit):
    """Phase seperation circuit for QAOA with linear soft constraints."""
    def __init__(self, choice_reg, power_req_reg, flag_reg, ev: EV):
        """Initialize the circuit."""
        c = math.floor(math.log2(ev.max_power)) + 1
        
        self.a = Parameter("a")
        self.gamma = Parameter("gamma")
        super().__init__(choice_reg, power_req_reg, flag_reg, name="UPhase")
        # initialize flag qubit
        super().x(flag_reg)
        
        value_circ = TimeComputation(choice_reg, ev)
        super().append(value_circ.to_instruction({value_circ.gamma: self.gamma}),
                       choice_reg)
        ev_power_computation = TotalPowerComputation(choice_reg, power_req_reg, flag_reg, ev, clean_up=True)
        super().append(ev_power_computation.to_instruction(),
                       [*choice_reg, *power_req_reg, flag_reg])
        for idx, qubit in enumerate(power_req_reg):
            super().cp(2**idx * self.a * self.gamma, flag_reg, qubit)
        super().p(-2**c * self.a * self.gamma, flag_reg)
        super().append(ev_power_computation.inverse().to_instruction(),
                       [*choice_reg, *power_req_reg, flag_reg])


class MixingOperator(QuantumCircuit):
    """Default Mixing Circuit for QAOA."""
    def __init__(self, register):
        """Initialize the circuit."""
        self.beta = Parameter("beta")
        super().__init__(register, name="UMix")
        super().rx(2 * self.beta, register)

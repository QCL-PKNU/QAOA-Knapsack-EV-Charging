import math
import matplotlib.pyplot as plt

from qiskit import QuantumRegister, QuantumCircuit
from qiskit.circuit import Parameter

import os
import utils
from EV_knapsack import EV
from plots import *
from fractions import Fraction

from circuits import PhaseOperator, MixingOperator

import time
import datetime


class QAOA(QuantumCircuit):
    """QAOA Circuit for Knapsack ev with linear soft constraints."""

    def __init__(self, ev: EV, p: int, verbose=True):
        """Initialize the circuit."""
        """
        Args:
            ev: Knapsack ev to be solved
            p: number of QAOA steps
        """
        self.p = p
        self.betas = [Parameter(f"beta{i}") for i in range(p)]
        self.gammas = [Parameter(f"gamma{i}") for i in range(p)]
        self.a = Parameter("a")

        # determine number of qubits needed for weight register
        n = math.floor(math.log2(ev.total_power)) + 1
        c = math.floor(math.log2(ev.max_power)) + 1
        if c == n:
            n += 1

        choice_reg = QuantumRegister(ev.number_of_evs, name="choice_reg")
        power_req_reg = QuantumRegister(n, name="power_req")
        flag_reg = QuantumRegister(1, name="flag")

        if verbose:
            print("Number of qubits: ", n + ev.number_of_evs + 1)

        super().__init__(choice_reg, power_req_reg, flag_reg, name=f"QAOA {p=}")

        phase_circ = PhaseOperator(choice_reg, power_req_reg, flag_reg, ev)
        mix_circ = MixingOperator(choice_reg)

        # initial state
        super().h(choice_reg)

        # alternatingly apply phase seperation circuits and mixers
        for gamma, beta in zip(self.gammas, self.betas):
            # apply phase seperation circuit
            phase_params = {
                phase_circ.gamma: gamma,
                phase_circ.a: self.a,
            }
            super().append(phase_circ.to_instruction(phase_params),
                           [*choice_reg, *power_req_reg, flag_reg])

            # apply mixer
            super().append(mix_circ.to_instruction({mix_circ.beta: beta}),
                           choice_reg)

        # measurement
        # super().save_statevector()
        # super().measure_all()


    @staticmethod
    def beta_range():
        return 0, math.pi

    @staticmethod
    def gamma_range(a):
        denominator = Fraction(a).denominator
        return 0, denominator * 2 * math.pi



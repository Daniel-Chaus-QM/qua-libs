"""
        ACTIVE RESET (Work in progress, use with care)

"""

from qm.qua import *
from qm import SimulationConfig
from qualang_tools.results import fetching_tool
from qualang_tools.units import unit
from qualang_tools.analysis.discriminator import two_state_discriminator

import matplotlib.pyplot as plt
import numpy as np

from components import QuAM, Transmon
from macros import qua_declaration, multiplexed_readout, node_save

###################################################
#  Load QuAM and open Communication with the QOP  #
###################################################
# Class containing tools to help handling units and conversions.
u = unit(coerce_to_integer=True)
# Instantiate the QuAM class from the state file
machine = QuAM.load("state.json")
# Generate the OPX and Octave configurations
config = machine.generate_config()
octave_config = machine.octave.get_octave_config()
# Open Communication with the QOP
qmm = machine.connect()

# Get the relevant QuAM components
q1 = machine.active_qubits[0]
q2 = machine.active_qubits[1]


def active_reset(qubit):
    count = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    assign(count, 0)
    cont_condition = declare(bool)
    assign(cont_condition, ((I > qubit.resonator.operations["readout"].threshold) & (count < 3)))
    with while_(cont_condition):
        qubit.xy.play("x180")
        qubit.xy.align(qubit.resonator.name)
        qubit.resonator.measure("readout", qua_vars=(I, Q))
        assign(count, count + 1)
        assign(cont_condition, ((I > qubit.resonator.operations["readout"].threshold) & (count < 3)))
    return I, Q


def apply_initialize_active(qubit: Transmon, pi_operation_name="x180"):
    I = declare(fixed)
    Q = declare(fixed)
    state = declare(bool)
    attempts = declare(int, value=1)
    assign(attempts, 1)
    operation = qubit.resonator.operations["readout"]
    qubit.xy.align(qubit.resonator.name)
    # First measurement
    qubit.resonator.measure("readout", qua_vars=(I, Q))
    # Single shot state discrimination
    assign(state, I > operation.threshold)
    # Wait for the resonator to deplete
    wait(qubit.resonator.depletion_time // 4, qubit.xy.name)
    # Conditional play to actively reset the qubit to ground
    qubit.xy.play(pi_operation_name, condition=state)
    qubit.xy.align(qubit.resonator.name)
    # Repeat until the qubit is in the ground state  with high probability (rus_exit_threshold)
    with while_(I > operation.rus_exit_threshold):
        qubit.xy.align(qubit.resonator.name)
        qubit.resonator.measure("readout", qua_vars=(I, Q))
        assign(state, I > operation.threshold)
        wait(qubit.resonator.depletion_time // 4, qubit.xy.name)
        qubit.xy.play(pi_operation_name, condition=state)
        qubit.xy.align(qubit.resonator.name)
        assign(attempts, attempts + 1)


###################
# The QUA program #
###################
n_runs = 10000  # Number of runs


with program() as iq_blobs:
    I_g, I_g_st, Q_g, Q_g_st, n, _ = qua_declaration(nb_of_qubits=2)
    I_e, I_e_st, Q_e, Q_e_st, _, _ = qua_declaration(nb_of_qubits=2)

    # Bring the active qubits to the minimum frequency point
    machine.apply_all_flux_to_min()

    with for_(n, 0, n < n_runs, n + 1):
        # ground iq blobs
        apply_initialize_active(q1)
        # wait(machine.get_thermalization_time * u.ns)
        align()
        multiplexed_readout([q1, q2], I_g, I_g_st, Q_g, Q_g_st)

        # excited iq blobs
        apply_initialize_active(q1)
        # wait(machine.get_thermalization_time * u.ns)
        align()
        q1.xy.play("x180")
        q2.xy.play("x180")
        align()
        multiplexed_readout([q1, q2], I_e, I_e_st, Q_e, Q_e_st)

    with stream_processing():
        for i in range(2):
            I_g_st[i].save_all(f"I_g_q{i}")
            Q_g_st[i].save_all(f"Q_g_q{i}")
            I_e_st[i].save_all(f"I_e_q{i}")
            Q_e_st[i].save_all(f"Q_e_q{i}")


###########################
# Run or Simulate Program #
###########################
simulate = False

if simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=10_000)  # In clock cycles = 4ns
    job = qmm.simulate(config, iq_blobs, simulation_config)
    job.get_simulated_samples().con1.plot()

else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Calibrate the active qubits
    # machine.calibrate_octave_ports(qm)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(iq_blobs)
    # fetch data
    results = fetching_tool(job, ["I_g_q0", "Q_g_q0", "I_e_q0", "Q_e_q0", "I_g_q1", "Q_g_q1", "I_e_q1", "Q_e_q1"])
    I_g_q1, Q_g_q1, I_e_q1, Q_e_q1, I_g_q2, Q_g_q2, I_e_q2, Q_e_q2 = results.fetch_all()
    # Plot the IQ blobs, rotate them to get the separation along the 'I' quadrature, estimate a threshold between them
    # for state discrimination and derive the fidelity matrix
    two_state_discriminator(I_g_q1, Q_g_q1, I_e_q1, Q_e_q1, True, True)
    plt.suptitle(f"{q1.name}")
    two_state_discriminator(I_g_q2, Q_g_q2, I_e_q2, Q_e_q2, True, True)
    plt.suptitle(f"{q2.name}")

    # Close the quantum machines at the end in order to put all flux biases to 0 so that the fridge doesn't heat-up
    qm.close()
from quam.components import pulses
from qualang_tools.units import unit

# Class containing tools to help handling units and conversions.
u = unit(coerce_to_integer=True)


def add_default_transmon_pulses(transmon):
    # TODO: make sigma=length/5
    # TODO: Make gates amplitude a reference to x180 amplitude
    transmon.xy.operations["x180_DragGaussian"] = pulses.DragPulse(
        amplitude=0.1,
        sigma=7,
        alpha=1.0,
        anharmonicity=f"#/qubits/{transmon.name}/anharmonicity",
        length=40,
        axis_angle=0,
        digital_marker="ON",
    )
    transmon.xy.operations["x90_DragGaussian"] = pulses.DragPulse(
        amplitude=0.1 / 2,
        sigma="#../x180_DragGaussian/sigma",
        alpha="#../x180_DragGaussian/alpha",
        anharmonicity="#../x180_DragGaussian/anharmonicity",
        length="#../x180_DragGaussian/length",
        axis_angle=0,
        digital_marker="ON",
    )
    transmon.xy.operations["-x90_DragGaussian"] = pulses.DragPulse(
        amplitude=-0.1 / 2,
        sigma="#../x180_DragGaussian/sigma",
        alpha="#../x180_DragGaussian/alpha",
        anharmonicity="#../x180_DragGaussian/anharmonicity",
        length="#../x180_DragGaussian/length",
        axis_angle=0,
        digital_marker="ON",
    )
    transmon.xy.operations["y180_DragGaussian"] = pulses.DragPulse(
        amplitude="#../x180_DragGaussian/amplitude",
        sigma="#../x180_DragGaussian/sigma",
        alpha="#../x180_DragGaussian/alpha",
        anharmonicity="#../x180_DragGaussian/anharmonicity",
        length="#../x180_DragGaussian/length",
        axis_angle=90,
        digital_marker="ON",
    )
    transmon.xy.operations["y90_DragGaussian"] = pulses.DragPulse(
        amplitude=0.1 / 2,
        sigma="#../x180_DragGaussian/sigma",
        alpha="#../x180_DragGaussian/alpha",
        anharmonicity="#../x180_DragGaussian/anharmonicity",
        length="#../x180_DragGaussian/length",
        axis_angle=90,
        digital_marker="ON",
    )
    transmon.xy.operations["-y90_DragGaussian"] = pulses.DragPulse(
        amplitude=-0.1 / 2,
        sigma="#../x180_DragGaussian/sigma",
        alpha="#../x180_DragGaussian/alpha",
        anharmonicity="#../x180_DragGaussian/anharmonicity",
        length="#../x180_DragGaussian/length",
        axis_angle=90,
        digital_marker="ON",
    )
    transmon.xy.operations["x180_Square"] = pulses.SquarePulse(
        amplitude=0.25, length=100, axis_angle=0, digital_marker="ON"
    )
    transmon.xy.operations["x90_Square"] = pulses.SquarePulse(
        amplitude=0.25 / 2, length="#../x180_Square/length", axis_angle=0, digital_marker="ON"
    )
    transmon.xy.operations["-x90_Square"] = pulses.SquarePulse(
        amplitude=-0.25 / 2, length="#../x180_Square/length", axis_angle=0, digital_marker="ON"
    )
    transmon.xy.operations["y180_Square"] = pulses.SquarePulse(
        amplitude=0.25, length="#../x180_Square/length", axis_angle=90, digital_marker="ON"
    )
    transmon.xy.operations["y90_Square"] = pulses.SquarePulse(
        amplitude=0.25 / 2, length="#../x180_Square/length", axis_angle=90, digital_marker="ON"
    )
    transmon.xy.operations["-y90_Square"] = pulses.SquarePulse(
        amplitude=-0.25 / 2, length="#../x180_Square/length", axis_angle=90, digital_marker="ON"
    )
    transmon.set_gate_shape("DragGaussian")

    transmon.xy.operations["saturation"] = pulses.SquarePulse(
        amplitude=0.25, length=10 * u.us, axis_angle=0, digital_marker="ON"
    )
    transmon.z.operations["const"] = pulses.SquarePulse(amplitude=0.1, length=100)
    transmon.resonator.operations["readout"] = pulses.SquareReadoutPulse(
        length=1 * u.us, amplitude=0.00123, threshold=0.0, digital_marker="ON"
    )


def add_default_coupler_pulses(coupler):
    coupler.operations["const"] = pulses.SquarePulse(amplitude=0.1, length=100)


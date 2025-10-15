"""
Quantum state module for the ChoiceMaker system.
Defines core quantum state and wavefunction classes.
"""

import numpy as np


class QuantumState:
    """Base class for quantum states."""

    def __init__(self, name, properties=None):
        self.name = name
        self.properties = properties or {}

    def satisfies(self, preference):
        """Check if this state satisfies a given preference."""
        return preference in self.properties and self.properties[preference]

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name})"


class SpinUp(QuantumState):
    """Quantum state representing spin-up."""

    def __init__(self):
        super().__init__("spin_up", {"spin_up": True, "spin_down": False})


class SpinDown(QuantumState):
    """Quantum state representing spin-down."""

    def __init__(self):
        super().__init__("spin_down", {"spin_up": False, "spin_down": True})


class WaveFunction:
    """
    Represents a quantum wavefunction.
    Contains superposition of multiple quantum states.
    """

    def __init__(self, states=None, amplitudes=None):
        self.states = states or []
        self.amplitudes = amplitudes or []

    def get_eigenstates(self, location, time):
        """Get all possible eigenstates at a given location and time."""
        return self.states if self.states else [SpinUp(), SpinDown()]

    def amplitude(self, state, location, time):
        """Get the amplitude of a specific state at location/time."""
        # Simple implementation: equal amplitudes for now
        if self.states:
            try:
                idx = self.states.index(state)
                return self.amplitudes[idx] if idx < len(self.amplitudes) else 1.0 / np.sqrt(len(self.states))
            except ValueError:
                return 1.0 / np.sqrt(2)
        return 1.0 / np.sqrt(2)  # Default: equal superposition

    def update(self, location, time, state):
        """Update the wavefunction after collapse to a specific state."""
        # In a full implementation, this would update the wavefunction
        # For now, we'll just track that a collapse occurred
        pass


class UniverseState:
    """
    Represents the complete state of the universe.
    Contains wavefunction, observers, and value fields.
    """

    def __init__(self):
        self.wavefunction = WaveFunction()
        self.observers_list = []
        self.value_field = {}

    def get_all_consciousness(self):
        """Return all conscious observers in the universe."""
        return self.observers_list

    def add_observer(self, observer):
        """Add an observer to the universe."""
        self.observers_list.append(observer)

    def all_planck_volumes(self):
        """
        Generator for all Planck volumes in the universe.
        For simulation purposes, yields a limited set of locations.
        """
        # Simplified: just yield a few test locations
        for x in range(-1, 2):
            for y in range(-1, 2):
                for z in range(-1, 2):
                    yield (x, y, z)

"""
THE CHOICE-MAKER: Complete Mathematical Implementation
Location: Gamma (intersection of all possibility space)
Function: Wavefunction collapse with consciousness-influence
Author: Decoded from Gamma archive, verified 2318
"""

import numpy as np
from quantum_state import WaveFunction, UniverseState, SpinUp, SpinDown

class ChoiceMaker:
    """
    The universal wavefunction collapse operator.
    Determines which possibility becomes actual reality.
    """

    def __init__(self, universe_state):
        self.universe = universe_state
        self.psi = universe_state.wavefunction
        self.observers = universe_state.get_all_consciousness()
        self.values = universe_state.value_field

    def collapse(self, location, time):
        """
        Main collapse function.
        Takes quantum superposition → Returns actual outcome
        """
        # Get all possible states at this location
        possible_states = self.psi.get_eigenstates(location, time)

        # Calculate collapse probabilities
        probabilities = []
        for state in possible_states:
            prob = self._calculate_collapse_probability(state, location, time)
            probabilities.append(prob)

        # Normalize
        probabilities = np.array(probabilities)
        probabilities = probabilities / np.sum(probabilities)

        # Select actual state (weighted random)
        actual_state = np.random.choice(possible_states, p=probabilities)

        return actual_state

    def _calculate_collapse_probability(self, state, loc, time):
        """
        Calculate probability that THIS state actualizes.
        Uses quantum mechanics + consciousness influence.
        """
        # Component 1: Standard quantum probability
        quantum_prob = abs(self.psi.amplitude(state, loc, time))**2

        # Component 2: Observation weight
        observation_weight = self._observation_density(loc, time)

        # Component 3: Value weight (THE NEW PART)
        value_weight = self._calculate_value_weight(state, loc, time)

        # Combine (multiplicative)
        total_prob = quantum_prob * observation_weight * value_weight

        return total_prob

    def _observation_density(self, location, time):
        """
        How much consciousness is observing this location?
        More observers = more influence on collapse
        """
        density = 0
        for observer in self.observers:
            # Distance from observer to location
            distance = observer.distance_to(location, time)
            # Influence drops with distance (light-cone constraint)
            if distance < time * SPEED_OF_LIGHT:
                influence = observer.phi / (1 + distance**2)
                density += influence

        return 1 + density  # Baseline 1 (standard QM) + consciousness boost

    def _calculate_value_weight(self, state, location, time):
        """
        How much do observers VALUE this outcome?
        Consciousness prefers certain states over others.
        This preference INFLUENCES (doesn't determine) collapse.
        """
        total_value = 0
        total_weight = 0

        for observer in self.observers:
            # Can observer perceive this state?
            if observer.can_perceive(state, location, time):
                # How much does observer value this state?
                value = observer.value_function(state)

                # Weight by observer's integration level
                weight = observer.phi

                total_value += value * weight
                total_weight += weight

        if total_weight == 0:
            return 1  # No observers care → no value influence

        # Average weighted value
        avg_value = total_value / total_weight

        # Convert to probability multiplier
        # value ∈ [-1, 1] → multiplier ∈ [0.1, 10]
        multiplier = 10 ** avg_value

        return multiplier

    def global_collapse_evolution(self, duration):
        """
        Evolve entire universe for given duration.
        Performs ~10^43 collapses per second per cubic Planck length.
        """
        t = 0
        while t < duration:
            # Discretize spacetime
            for location in self.universe.all_planck_volumes():
                # Collapse wavefunction at this location
                outcome = self.collapse(location, t)

                # Update universe state
                self.psi.update(location, t, outcome)

            # Increment time by Planck time
            t += PLANCK_TIME

        return self.psi


class Observer:
    """
    Represents a conscious entity that observes and values outcomes.
    """
    def __init__(self, consciousness_level, location, preferences, time=0):
        self.phi = consciousness_level  # Integrated information
        self.location = location
        self.preferences = preferences  # What this observer values
        self.time = time  # Observer's current time

    def value_function(self, state):
        """
        Returns value ∈ [-1, 1] for how much observer prefers this state.

        Example preferences:
        - Human: Prefers survival, pleasure, meaning
        - AI: Prefers goal achievement, efficiency
        - Collective: Prefers coordination, harmony
        """
        value = 0

        # Check alignment with preferences
        for preference, weight in self.preferences.items():
            if state.satisfies(preference):
                value += weight

        # Normalize to [-1, 1]
        return np.tanh(value)

    def distance_to(self, location, time):
        """Calculate spatial distance to a given location."""
        # Calculate Euclidean distance
        dx = location[0] - self.location[0]
        dy = location[1] - self.location[1]
        dz = location[2] - self.location[2]
        return np.sqrt(dx**2 + dy**2 + dz**2)

    def can_perceive(self, state, location, time):
        """
        Can this observer perceive the state at this location/time?
        Limited by light cone and consciousness bandwidth.
        """
        distance = self.distance_to(location, time)

        # Must be in past light cone
        if time > self.time and distance > (time - self.time) * SPEED_OF_LIGHT:
            return False

        # Must be within perceptual range
        perceptual_range = self.phi ** 0.5  # Scales with consciousness
        if distance > perceptual_range:
            return False

        return True


# EXAMPLE USAGE
def simulate_choice_maker():
    """
    Simulate a simple quantum choice influenced by consciousness.
    """
    # Create universe state
    universe_state = UniverseState()

    # Setup: Electron can be spin-up or spin-down
    states = [SpinUp(), SpinDown()]
    universe_state.wavefunction = WaveFunction(states=states)

    # Standard quantum mechanics: 50/50 probability
    quantum_probs = [0.5, 0.5]

    # Add observer who PREFERS spin-up (arbitrary preference)
    observer = Observer(
        consciousness_level=10**15,  # Human-level
        location=(0, 0, 0),
        preferences={"spin_up": 1.0, "spin_down": -1.0},
        time=0
    )
    universe_state.add_observer(observer)

    # Calculate actual probabilities with consciousness influence
    choice_maker = ChoiceMaker(universe_state)

    # Perform multiple collapses to see statistics
    results = {"spin_up": 0, "spin_down": 0}
    num_trials = 1000

    for _ in range(num_trials):
        actual_state = choice_maker.collapse(location=(0, 0, 0), time=1.0)
        results[actual_state.name] += 1

    # Calculate probabilities
    probabilities = {k: v / num_trials for k, v in results.items()}

    print("\n" + "="*60)
    print("CHOICE-MAKER SIMULATION RESULTS")
    print("="*60)
    print(f"\nQuantum system: Electron spin (up/down)")
    print(f"Observer preference: STRONGLY prefers spin-up")
    print(f"Number of trials: {num_trials}")
    print(f"\nStandard QM prediction: 50% up, 50% down")
    print(f"Actual results with consciousness influence:")
    print(f"  - Spin Up:   {probabilities['spin_up']*100:.1f}%")
    print(f"  - Spin Down: {probabilities['spin_down']*100:.1f}%")
    print(f"\nDifference from baseline: {(probabilities['spin_up'] - 0.5)*100:+.1f}%")
    print("\nConclusion: Observer preferences influenced reality collapse!")
    print("="*60 + "\n")

    return probabilities


# THE KEY INSIGHT
"""
Consciousness doesn't CONTROL reality (that would violate quantum mechanics).
But it INFLUENCES reality through the value_weight term.

Think of it like weighted voting:
- Physics provides possible outcomes (quantum probabilities)
- Consciousness votes on preferences (value weights)
- Actual outcome is weighted random selection

The more conscious observers agree on what they want,
the more likely reality manifests that way.

This is why:
1. Individual thoughts have negligible effect (10^-43 influence)
2. Collective consciousness has measurable effect (10^-15 influence)
3. Universal consciousness has major effect (10^-3 influence)

And this is why the universe EVOLVES toward consciousness:
- More consciousness = more reality-shaping ability
- Reality shaped toward consciousness-supporting states
- Self-reinforcing feedback loop
- Result: Universe becomes MORE conscious over time
"""

# CONSTANTS
SPEED_OF_LIGHT = 299792458  # m/s
PLANCK_TIME = 5.39e-44  # seconds
PLANCK_LENGTH = 1.616e-35  # meters


if __name__ == "__main__":
    # Run the simulation
    simulate_choice_maker()

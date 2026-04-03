# numpy_orbit.py
"""
NumPy-based replacement for PyKEP for the Autonomous Constellation Manager (ACM)
Provides dummy TLE objects, orbit propagation, and plotting for testing and simulation
without PyKEP.
"""

import numpy as np
import matplotlib.pyplot as plt

# -------------------------
# Dummy TLE and Planet
# -------------------------

class DummyTLE:
    """TLE object replacement with PyKEP-like attributes"""
    def __init__(self):
        # Position and velocity vectors (km, km/s)
        self.r = np.zeros(3)
        self.v = np.zeros(3)

        # Epoch in MJD2000
        self.ref_mjd2000 = 0.0

        # Gravitational parameters
        self.mu_central_body = 398600.4418  # km^3/s^2
        self.mu_self = 0.0  # negligible for satellites

        # Satellite geometry
        self.radius = 1.0  # km
        self.safe_radius = 2.0  # km

        # Mass / propellant
        self.mass = 500.0  # kg
        self.fuel_mass = 100.0  # kg

        # Optional: add more attributes if SpaceObject requires

    def osculating_elements(self, epoch):
        return (7000000.0, 0.001, 1.0, 0.0, 0.0, 0.0)

class DummyKeplerian:
    def __init__(self, name):
        self.name = name
        self.mu_central_body = 398600.4418
        self.mu_self = 0.0
        self.radius = 1.0
        self.safe_radius = 2.0
        self.orbital_elements = (7000000.0, 0.001, 1.0, 0.0, 0.0, 0.0)
    
    def eph(self, epoch):
        import math
        # deterministic circular orbit kinematics for LEO rendering
        r = 6800000.0  # 6800 km orbit size
        
        # Random-like offset properties directly based on object name
        seed_val = float(hash(self.name) % 10000) / 10000.0
        phase = seed_val * 2 * math.pi
        
        # epoch is in mjd2000 (days). Convert to seconds for calculation.
        t_sec = float(epoch) * 86400.0
        
        # Typical LEO angular velocity (~0.00116 rad/s) + minor variation per object
        w = 0.00116 + (seed_val * 0.0001)
        
        theta = w * t_sec + phase
        tilt = theta / 2.0  # artificial inclination 
        
        # Position
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        z = r * math.sin(tilt)
        
        # Velocity (derivative)
        vx = -r * w * math.sin(theta)
        vy = r * w * math.cos(theta)
        vz = r * w * 0.5 * math.cos(tilt)
        
        return ((x, y, z), (vx, vy, vz))
        
    def osculating_elements(self, epoch):
        return self.orbital_elements

class planet:
    @staticmethod
    def tle(line1, line2):
        """Return a DummyTLE object instead of real PyKEP TLE"""
        return DummyTLE()
        
    @staticmethod
    def keplerian(*args):
        name = args[-1] if isinstance(args[-1], str) else "dummy"
        return DummyKeplerian(name)

SEC2DAY = 1.0 / 86400.0
MU_EARTH = 398600.4418 * 1e9

# -------------------------
# Epoch replacement
# -------------------------

class DummyEpoch:
    def __init__(self, t):
        self.mjd2000 = t
    
    def __float__(self):
        return float(self.mjd2000)
    
    def __add__(self, other):
        return DummyEpoch(self.mjd2000 + getattr(other, 'mjd2000', other))

def epoch(time_value, time_type="mjd2000"):
    """Dummy epoch function replacement for pk.epoch"""
    if hasattr(time_value, 'mjd2000'):
        return time_value
    return DummyEpoch(float(time_value))

# -------------------------
# Orbit propagation
# -------------------------

def propagate_rk4(r0, v0, dt, mu=398600.4418):
    """
    Simple 3D orbit propagation using RK4 integration
    r0: initial position vector (km)
    v0: initial velocity vector (km/s)
    dt: time step (s)
    mu: gravitational parameter (km^3/s^2)
    Returns: r, v after dt seconds
    """
    def acceleration(r):
        norm_r = np.linalg.norm(r)
        return -mu * r / norm_r**3

    k1v = acceleration(r0) * dt
    k1r = v0 * dt

    k2v = acceleration(r0 + 0.5*k1r) * dt
    k2r = (v0 + 0.5*k1v) * dt

    k3v = acceleration(r0 + 0.5*k2r) * dt
    k3r = (v0 + 0.5*k2v) * dt

    k4v = acceleration(r0 + k3r) * dt
    k4r = (v0 + k3v) * dt

    r_new = r0 + (k1r + 2*k2r + 2*k3r + k4r)/6
    v_new = v0 + (k1v + 2*k2v + 2*k3v + k4v)/6

    return r_new, v_new

# -------------------------
# Orbit plotting
# -------------------------

def plot_orbit_3d(r_array, title="Orbit Plot", ax=None, t0=None, s=None, legend=False, color='black', **kwargs):
    """
    Simple 3D orbit plot.
    Note: When called from simulator.py, r_array is actually the satellite object itself.
    """
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    
    # Calculate scale so the dots look realistic (matpotlib plot uses linear markersize)
    marker_size = (s / 30) if s else 5
    marker_size = min(marker_size, 10)  # caps the visual size

    # Calculate live location
    try:
        r, v = r_array.eph(t0 if t0 else DummyEpoch(0))
    except:
        r = [0, 0, 0]

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot([r[0]], [r[1]], [r[2]], marker='o', markersize=marker_size, color=color, label="Satellite")
        ax.set_xlabel("X (km)")
        ax.set_ylabel("Y (km)")
        ax.set_zlabel("Z (km)")
        ax.set_title(title)
        if legend:
            ax.legend()
        plt.show()
    else:
        # Plot the dynamically calculated true coordinate point!
        ax.plot([r[0]], [r[1]], [r[2]], marker='o', markersize=marker_size, color=color, label=r_array.name if hasattr(r_array, 'name') else "Satellite")


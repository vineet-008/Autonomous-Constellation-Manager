# Example 1 runs simulator with provided parameteres.
# We use data from https://www.celestrak.com/NORAD/elements/stations.txt
# to provide ISS - protected object and other stellites as debris.

import argparse
import sys

import numpy_orbit as pk


from space_navigator.simulator import Simulator
from space_navigator.api import Environment
from space_navigator.agent import TableAgent
from space_navigator.utils import read_space_objects
import requests
import os

# Fetch live Celestrak API data for real-time telemetry demonstration
try:
    print("Fetching live Real-Time Telemetry from Celestrak API...")
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        os.makedirs("data/environments", exist_ok=True)
        with open("data/environments/live_stations.tle", "w") as f:
            f.write(response.text)
        print("Success! Live data pipeline online.")
    else:
        print("Using cached station data...")
except Exception as e:
    print(f"API fetch failed, falling back to cached file. Error: {e}")

try:
    if not os.path.exists("data/environments/earth.jpg"):
        print("Fetching high-fidelity Earth texture for visual mapping...")
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Land_ocean_ice_2048.jpg/1024px-Land_ocean_ice_2048.jpg"
        response = requests.get(url, timeout=10)
        with open("data/environments/earth.jpg", "wb") as f:
            f.write(response.content)
except Exception as e:
    print(f"Earth texture fetch failed: {e}")

START_TIME = 6000
SIMULATION_STEP = 0.0001
END_TIME = 6000.1
# Number of TLE satellites to read from file.
DEBRIS_NUM = 3


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--visualize", type=str,
                        default="True", required=False)
    parser.add_argument("-start", "--start_time", type=float,
                        default=START_TIME, required=False)
    parser.add_argument("-end", "--end_time", type=float,
                        default=END_TIME, required=False)
    parser.add_argument("-s", "--step", type=float,
                        default=SIMULATION_STEP, required=False)
    parser.add_argument("-n_v", "--n_steps_vis", type=int,
                        default=5, required=False,
                        help="the number of propagation steps in one step of visualization")
    parser.add_argument("-p", "--print_out", type=str,
                        default="False", required=False)

    args = parser.parse_args(args)

    visualize = args.visualize.lower() == "true"
    print_out = args.print_out.lower() == "true"
    start_time, end_time = args.start_time, args.end_time
    step, n_steps_vis = args.step, args.n_steps_vis

    from space_navigator.agent import BaseAgent
    import numpy as np

    class HackathonAgent(BaseAgent):
        def get_action(self, state):
            # Basic Autonomous Collision Avoidance
            st_pos = state["coord"]["st"][0][:3]
            debr_pos = state["coord"]["debr"][:, :3]
            if len(debr_pos) > 0:
                dist = np.linalg.norm(debr_pos - st_pos, axis=1)
                # Setting threshold extremely high (1500 km) forces the agent to frequently 
                # demonstrate its collision protection and evasive delta-V firing!
                if np.min(dist) < 1500000:
                    # Fire evasive Delta-V
                    return np.array([50.0, 50.0, 50.0, np.nan])
            return np.array([0.0, 0.0, 0.0, np.nan])
            
        def get_action_table(self):
            return np.array([])

        def copy(self):
            return HackathonAgent()
            
    # Load Real-Time SpaceObjects API parameters.
    # Fallback to local if live fetch failed
    tle_path = "data/environments/live_stations.tle" if os.path.exists("data/environments/live_stations.tle") else "data/environments/stations.tle"
    satellites = read_space_objects(tle_path, "tle")

    # Extra debris
    extra_debris = []
    eph = read_space_objects("data/environments/space_objects.eph", "eph")
    osc = read_space_objects("data/environments/space_objects.osc", "osc")
    for obj in eph + osc:
        extra_debris.append(obj)

    agent = HackathonAgent()

    start_time_val = pk.epoch(start_time, "mjd2000")
    end_time_val = pk.epoch(end_time, "mjd2000")
    
    # Evaluate a mini-constellation (5 active payloads) to keep processing times reasonable
    fleet_size = min(5, len(satellites))
    
    for i in range(fleet_size):
        payload = satellites[i]
        # Treat other immediate satellites and extra space objects as debris threats
        fleet_debris = [s for j, s in enumerate(satellites) if j != i][:DEBRIS_NUM] + extra_debris
        
        print(f"\n--- Protecting Fleet Payload {i+1}/{fleet_size} ---")
        env = Environment(payload, fleet_debris, start_time_val, end_time_val)
        simulator = Simulator(agent, env, step)
        
        # Only trigger visualization on the final payload so we don't open 10 popup windows
        do_vis = visualize and (i == fleet_size - 1)
        
        simulator.run(visualize=do_vis,
                      n_steps_vis=n_steps_vis, print_out=print_out)

        # Block the window only at the end of the full constellation iteration
        if do_vis:
            import matplotlib.pyplot as plt
            plt.ioff()
            plt.show()

    return


if __name__ == "__main__":
    main(sys.argv[1:])

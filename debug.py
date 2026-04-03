import sys
import traceback

def run():
    print("starting test flight")
    try:
        from examples import test_flight
        test_flight.main(["-v", "False", "-p", "True"])
    except Exception as e:
        print("EXCEPTION CAUGHT")
        traceback.print_exc()

if __name__ == "__main__":
    run()

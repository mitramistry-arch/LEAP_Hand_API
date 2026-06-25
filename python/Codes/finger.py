import argparse
import sys
from pathlib import Path
import time

import numpy as np

# Ensure the parent python package folder is importable when running from python/Codes
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_PYTHON_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_PYTHON_DIR))

from leap_hand_utils.dynamixel_client import DynamixelClient


def parse_args():
    parser = argparse.ArgumentParser(
        description='Quick LEAP Hand connectivity and motor test script.')
    parser.add_argument('--port', default='COM10', help='Serial port for the LEAP Hand.')
    parser.add_argument('--baud', default=4000000, type=int, help='Baudrate for the Dynamixel connection.')
    parser.add_argument('--motor-ids', default='0', help='Comma-separated list of motor IDs to test.')
    parser.add_argument('--move-rad', default=0.2, type=float, help='Small movement in radians for the test motor.')
    parser.add_argument('--wait-seconds', default=2.0, type=float, help='Seconds to wait after commanding movement.')
    return parser.parse_args()


def parse_motor_ids(raw_ids: str):
    return [int(item.strip()) for item in raw_ids.split(',') if item.strip()]


def main():
    args = parse_args()
    motor_ids = parse_motor_ids(args.motor_ids)
    if not motor_ids:
        raise ValueError('At least one motor ID must be provided.')

    print(f'Connecting to LEAP Hand on port {args.port} at {args.baud} baud...')
    client = DynamixelClient(motor_ids, args.port, args.baud)

    try:
        client.connect()
        print('Connected successfully.')

        print('Enabling torque for motors:', motor_ids)
        client.set_torque_enabled(motor_ids, True)

        print('Reading current positions...')
        current_positions = client.read_pos()
        print('Current positions:', current_positions.tolist())

        test_motor = motor_ids[0]
        original_position = float(current_positions[0])
        target_position = original_position + args.move_rad
        print(f'Commanding motor {test_motor} from {original_position:.4f} to {target_position:.4f} radians...')

        client.write_desired_pos([test_motor], np.array([target_position], dtype=np.float32))
        time.sleep(args.wait_seconds)

        print('Reading back position after movement...')
        new_positions = client.read_pos()
        new_position = float(new_positions[0])
        print('New position:', new_position)

        moved = abs(new_position - original_position) >= max(0.01, abs(args.move_rad) * 0.5)
        if moved:
            print('Movement detected: PASS')
        else:
            print('Movement detected: FAIL')

        print(f'Returning motor {test_motor} to original position...')
        client.write_desired_pos([test_motor], np.array([original_position], dtype=np.float32))
        time.sleep(1.0)

    except Exception as exc:
        print('ERROR:', exc)
        print('Check that the hand is powered, connected, and the port is correct.')
    finally:
        try:
            print('Disabling torque and disconnecting...')
            client.set_torque_enabled(motor_ids, False)
        except Exception:
            pass
        client.disconnect()
        print('Done.')


if __name__ == '__main__':
    main()
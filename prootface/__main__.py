import argparse
from .server import serve


def main():
    parser = argparse.ArgumentParser(description="Prootface character model and local preview")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--udp-host", default="127.0.0.1")
    parser.add_argument("--udp-port", type=int, default=11573)
    parser.add_argument("--face-id", type=int, default=0)
    parser.add_argument("--profile", default="local/calibration.json")
    args = parser.parse_args()
    serve(args)


if __name__ == "__main__":
    main()

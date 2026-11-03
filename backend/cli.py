"""
cli.py - The lab's terminal app, upgraded: colors, a table, unit choice.
Run: GRAPHHOPPER_KEY=your_key python cli.py      (type q or quit to exit)
"""
import os
import gh_client as gh

C = {"h": "\033[1;36m", "g": "\033[32m", "y": "\033[33m", "r": "\033[31m", "0": "\033[0m"}
BAR = "=" * 60


def render(res, units):
    """Build the printable text for one result."""
    out = [BAR, f"{C['h']}Directions: {res['origin']['label']} -> {res['destination']['label']} "
                f"by {res['profile']}{C['0']}", BAR]
    d = {"metric": f"{res['distance_km']:.1f} km", "imperial": f"{res['distance_mi']:.1f} miles",
         "both": f"{res['distance_mi']:.1f} miles / {res['distance_km']:.1f} km"}[units]
    out += [f"{C['g']}Distance:{C['0']} {d}", f"{C['g']}Duration:{C['0']} {res['duration']}", BAR]
    out.append(f"{'#':>3}  {'Instruction':<50} {'Distance':>12}")
    for n, i in enumerate(res["instructions"], 1):
        dist = {"metric": f"{i['distance_km']:.2f} km", "imperial": f"{i['distance_mi']:.2f} mi",
                "both": f"{i['distance_km']:.2f}km/{i['distance_mi']:.2f}mi"}[units]
        out.append(f"{n:>3}  {i['text'][:50]:<50} {dist:>12}")
    out.append(BAR)
    return "\n".join(out)


def main():
    key = os.environ.get("GRAPHHOPPER_KEY", "").strip() or input("Graphhopper API key: ").strip()
    units = "both"
    while True:
        print(f"\n{C['h']}Vehicle profiles: {', '.join(gh.PROFILES)}   (units: {units}; type 'units' to change){C['0']}")
        prof = input("Vehicle profile [car]: ").strip().lower() or "car"
        if prof in ("q", "quit"):
            break
        if prof == "units":
            units = input("metric / imperial / both: ").strip().lower()
            units = units if units in ("metric", "imperial", "both") else "both"
            continue
        start = input("Starting Location: ").strip()
        if start.lower() in ("q", "quit"):
            break
        end = input("Destination: ").strip()
        if end.lower() in ("q", "quit"):
            break
        try:
            print(render(gh.get_directions(start, end, key, prof), units))
        except gh.GraphhopperError as e:       # lab Part 5 step 7: report API errors
            print(f"{C['r']}Error ({e.status}): {e.message}{C['0']}")


if __name__ == "__main__":
    main()

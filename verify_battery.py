"""Live battery control verification for GW8000M-ES-C10.

Read-only checks: reads current settings and verifies they can be round-tripped
(write the same value back) without changing anything on the inverter.
"""

import asyncio
import sys
import goodwe
from goodwe.const import GOODWE_TCP_PORT
from goodwe.inverter import OperationMode, EMSMode

HOST = "192.168.18.8"
PORT = GOODWE_TCP_PORT

ok = True


def check(label, value, expected=None):
    global ok
    if expected is not None and value != expected:
        print(f"  [FAIL] {label}: got {value!r}, expected {expected!r}")
        ok = False
    else:
        print(f"  [OK]   {label}: {value!r}")


async def main():
    global ok
    print(f"Connecting to {HOST}:{PORT} ...")
    inv = await goodwe.connect(HOST, PORT, family="ET")
    print(f"  Connected: {inv.model_name}, {inv.rated_power}W\n")

    # --- Operation mode ---
    print("=== Operation mode ===")
    mode = await inv.get_operation_mode()
    print(f"  Current: {mode} ({mode.name if mode else 'N/A'})")

    supported = await inv.get_operation_modes(True)
    print(f"  Supported modes: {[m.name for m in supported]}")

    # Round-trip: write current value back unchanged
    if mode is not None:
        await inv.set_operation_mode(mode)
        mode2 = await inv.get_operation_mode()
        check("round-trip operation_mode", mode2, mode)

    # --- EMS mode ---
    print("\n=== EMS mode ===")
    ems = await inv.get_ems_mode()
    print(f"  Current: {ems} ({ems.name if ems else 'N/A'})")
    await inv.set_ems_mode(ems)
    ems2 = await inv.get_ems_mode()
    check("round-trip ems_mode", ems2, ems)

    # --- Grid export limit ---
    print("\n=== Grid export limit ===")
    export = await inv.get_grid_export_limit()
    print(f"  Current: {export} W")
    await inv.set_grid_export_limit(export)
    export2 = await inv.get_grid_export_limit()
    check("round-trip grid_export_limit", export2, export)

    # --- Battery DoD ---
    print("\n=== Battery depth of discharge (on-grid) ===")
    dod = await inv.get_ongrid_battery_dod()
    print(f"  Current DoD: {dod}%")
    await inv.set_ongrid_battery_dod(dod)
    dod2 = await inv.get_ongrid_battery_dod()
    check("round-trip ongrid_battery_dod", dod2, dod)

    # --- Individual settings ---
    print("\n=== Battery charge/discharge settings ===")
    for sid in (
        "battery_charge_voltage",
        "battery_charge_current",
        "battery_discharge_voltage",
        "battery_discharge_current",
        "battery_discharge_depth",
        "battery_discharge_voltage_offline",
        "battery_discharge_depth_offline",
    ):
        try:
            val = await inv.read_setting(sid)
            print(f"  {sid}: {val}")
        except Exception as e:
            print(f"  {sid}: ERROR — {e}")

    print(f"\n{'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

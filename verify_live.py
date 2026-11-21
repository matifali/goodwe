"""Live verification script for GW8000M-ES-C10 sensor filtering."""

import asyncio
import sys
import goodwe
from goodwe.const import GOODWE_TCP_PORT

HOST = "192.168.18.8"
PORT = GOODWE_TCP_PORT  # 502

MUST_HAVE = [
    # Basic PV strings (all 4, since 745 LV has 2 MPPTs with 2+1 or 2+2 strings)
    "vpv1", "ipv1", "ppv1",
    "vpv2", "ipv2", "ppv2",
    "vpv3", "ipv3", "ppv3",
    "vpv4", "ipv4", "ppv4",
    # PV mode labels
    "pv1_mode", "pv2_mode", "pv3_mode", "pv4_mode",
    # Both MPPT channels
    "pmppt1", "pmppt2",
    "imppt1", "imppt2",
    # Single-phase grid
    "vgrid", "igrid", "fgrid", "pgrid",
    # Backup / load
    "backup_v1", "backup_i1", "backup_p1",
]

MUST_NOT_HAVE = [
    # L2/L3 ghost sensors (single-phase inverter)
    "vgrid2", "vgrid3",
    "igrid2", "igrid3",
    "backup_v2", "backup_v3",
    "reactive_power2", "reactive_power3",
    "apparent_power2", "apparent_power3",
    # Ghost PV strings (745 LV has max 4)
    "vpv5", "vpv6", "vpv7", "vpv8",
    "vpv9", "vpv10", "vpv11", "vpv12",
    "vpv13", "vpv14", "vpv15", "vpv16",
    # Ghost MPPT channels (745 LV has 2 MPPTs)
    "pmppt3", "pmppt4", "pmppt5", "pmppt6", "pmppt7", "pmppt8",
    "imppt3", "imppt4", "imppt5", "imppt6", "imppt7", "imppt8",
]


async def main():
    print(f"Connecting to {HOST}:{PORT} ...")
    inv = await goodwe.connect(HOST, PORT, family="ET")

    print(f"\nDevice info:")
    print(f"  model_name   : {inv.model_name}")
    print(f"  rated_power  : {inv.rated_power} W")
    print(f"  firmware     : {inv.firmware}")
    print(f"  arm_firmware : {inv.arm_firmware}")

    print("\nReading runtime data ...")
    data = await inv.read_runtime_data()

    print(f"\nTotal sensors: {len(data)}\n")

    ok = True

    print("=== MUST HAVE ===")
    for key in MUST_HAVE:
        val = data.get(key, "MISSING")
        status = "OK" if key in data else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  [{status}] {key} = {val}")

    print("\n=== MUST NOT HAVE ===")
    for key in MUST_NOT_HAVE:
        present = key in data
        status = "FAIL" if present else "OK"
        if present:
            ok = False
        print(f"  [{status}] {key}{' = ' + str(data[key]) if present else ''}")

    print("\n=== ALL SENSOR VALUES ===")
    for key, val in sorted(data.items()):
        print(f"  {key}: {val}")

    print(f"\n{'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

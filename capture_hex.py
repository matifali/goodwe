"""Capture live hex responses from the inverter and write test fixture files.

The inverter speaks Modbus TCP on port 502. The test framework (EtMock) initialises
with port 8899 which creates ModbusRTU commands whose validator expects AA55-framed
RTU responses.  This script captures Modbus TCP, then converts each response to the
AA55/ModbusRTU wire format so the hex files work with the existing test harness.

ModbusRTU (AA55) response layout:
  AA 55  comm_addr  func_code  byte_count  <data…>  CRC16_lo  CRC16_hi
"""

import asyncio
import sys
import goodwe
from goodwe.const import GOODWE_TCP_PORT
from goodwe.modbus import _modbus_checksum

HOST = "192.168.18.8"
PORT = GOODWE_TCP_PORT  # 502 — inverter only responds on TCP
SAMPLE_DIR = "/Users/matifali/repos/matifali/goodwe/tests/sample/et"
PREFIX = "GW8000M-ES-C10"

FILES = {
    "device_info":  "_READ_DEVICE_VERSION_INFO",
    "running_data": "_READ_RUNNING_DATA",
    "meter_data":   "_READ_METER_DATA_EXTENDED2",
    "battery_info": "_READ_BATTERY_INFO",
    "mppt_data":    "_READ_MPPT_DATA",
}


def modbus_tcp_to_rtu_aa55(tcp_frame: bytes) -> bytes:
    """Convert a Modbus TCP response frame to ModbusRTU AA55 format.

    Modbus TCP layout: [TxID 2B] [ProtocolID 2B] [Length 2B] [UnitID] [FuncCode] [ByteCount] [Data…]
    AA55 RTU layout  : AA 55 [UnitID] [FuncCode] [ByteCount] [Data…] [CRC16 little-endian]
    """
    # Strip the 6-byte Modbus TCP header; what remains is UnitID + FuncCode + ByteCount + Data
    rtu_payload = tcp_frame[6:]
    # CRC is computed over rtu_payload only (data[2:] in the final AA55 frame, i.e. without AA55)
    crc = _modbus_checksum(rtu_payload)
    return b"\xaa\x55" + rtu_payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


async def main():
    print(f"Connecting to {HOST}:{PORT} ...")
    inv = await goodwe.connect(HOST, PORT, family="ET")
    print(f"  {inv.model_name}  {inv.rated_power}W  s/n:{inv.serial_number}\n")

    for label, cmd_attr in FILES.items():
        cmd = getattr(inv, cmd_attr)
        response = await inv._read_from_socket(cmd)
        aa55_frame = modbus_tcp_to_rtu_aa55(response.raw_data)
        path = f"{SAMPLE_DIR}/{PREFIX}_{label}.hex"
        with open(path, "w") as f:
            f.write(aa55_frame.hex())
        print(f"  [{label:15s}] {len(aa55_frame):4d} bytes → {path}")

    print("\nDone. Run tests to verify:")
    print("  python3 -m pytest tests/test_et.py::GW8000M_ES_C10_Test -v")


if __name__ == "__main__":
    asyncio.run(main())

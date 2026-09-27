from pathlib import Path
import struct
from types import MappingProxyType
import unittest

from tool.auto_define_config.contracts import ProbeContext
from tool.auto_define_config.errors import ConfigError
from tool.auto_define_config.providers.cpu import cpu_facts, decode_cpu
from tool.auto_define_config.providers.memory import memory_facts, parse_meminfo
from tool.auto_define_config.providers.platform import platform_facts


def registers(
    *,
    os_state=0xE6,
    leaf1=(1 << 26) | (1 << 27) | (1 << 28),
    leaf7=(1 << 5) | (1 << 16) | (1 << 30),
    vendor=b"GenuineIntel",
):
    return {
        "vendor": list(struct.unpack("<III", vendor)),
        "leaf1_ecx": leaf1,
        "leaf7_ebx": leaf7,
        "xcr0_low": os_state,
        "target_bits": 64,
    }


class HardwareTests(unittest.TestCase):
    def test_instruction_bits_require_operating_system_state(self):
        full = decode_cpu(registers())
        self.assertTrue(full["cpuIntel"])
        self.assertFalse(full["cpuAMD"])
        self.assertTrue(all(full[name] for name in ("avx2", "avx512f", "avx512bw")))
        ymm = decode_cpu(registers(os_state=6))
        self.assertTrue(ymm["avx2"])
        self.assertFalse(ymm["avx512f"])
        no_osxsave = decode_cpu(registers(leaf1=(1 << 26) | (1 << 28)))
        self.assertFalse(no_osxsave["avx2"])
        no_foundation = decode_cpu(registers(leaf7=(1 << 30)))
        self.assertFalse(no_foundation["avx512bw"])

    def test_vendor_is_independent_of_instruction_availability(self):
        result = decode_cpu(registers(vendor=b"AuthenticAMD"))
        self.assertTrue(result["cpuAMD"])
        self.assertFalse(result["cpuIntel"])
        self.assertTrue(result["avx512f"])

    def test_malformed_native_data_is_a_programming_error(self):
        for data in ({}, dict(registers(), leaf1_ecx=-1), dict(registers(), vendor=[1])):
            with self.assertRaises(ConfigError):
                decode_cpu(data)

    def test_target_architecture_does_not_follow_python_bitness(self):
        context = ProbeContext(
            Path.cwd(),
            "define/platform",
            (),
            MappingProxyType({"system": "Linux", "pointer_bytes": "4"}),
        )
        result = platform_facts(context)
        self.assertTrue(result["linux"].value)
        self.assertTrue(result["x86"].value)
        self.assertFalse(result["windows"].value)
        self.assertFalse(result["x64"].value)
        missing = platform_facts(ProbeContext(Path.cwd(), "define/platform", ()))
        self.assertEqual(missing["x64"].status, "unsupported")

    def test_linux_memory_is_os_visible_bytes(self):
        self.assertEqual(parse_meminfo("MemTotal:       32768 kB\nMemFree: 123 kB\n"), 32768 * 1024)
        result = memory_facts(system="Linux", read_text=lambda path: "MemTotal: 1024 kB\n")
        self.assertEqual(result["memory.total_bytes"].value, 1024 * 1024)
        with self.assertRaises(ConfigError):
            parse_meminfo("MemTotal: 1024 MB")

    def test_permission_denied_memory_is_not_a_zero_measurement(self):
        def denied(path):
            raise PermissionError("denied by system")

        result = memory_facts(system="Linux", read_text=denied)["memory.total_bytes"]
        self.assertEqual(result.status, "denied")
        self.assertIsNone(result.value)
        result = memory_facts(system="Windows", windows_total=lambda: 2**35)["memory.total_bytes"]
        self.assertEqual(result.value, 2**35)

    def test_cpu_without_target_context_is_unavailable_not_guessed(self):
        result = cpu_facts(ProbeContext(Path.cwd(), "define/cpu", ()))
        self.assertTrue(all(value.status == "unsupported" for value in result.values()))

    def test_macos_sysctl_adapter_uses_bytes_and_stays_unprivileged(self):
        from unittest.mock import patch
        from tool.build_support.process import Result

        with patch(
            "tool.auto_define_config.providers.memory.run_command",
            return_value=Result(0, "17179869184\n", ""),
        ) as run:
            facts = memory_facts(system="Darwin")
        self.assertEqual(facts["memory.total_bytes"].value, 17179869184)
        self.assertEqual(run.call_args.args[0], ["/usr/sbin/sysctl", "-n", "hw.memsize"])
        with patch(
            "tool.auto_define_config.providers.memory.run_command",
            return_value=Result(0, "unknown", ""),
        ):
            with self.assertRaises(ConfigError):
                memory_facts(system="Darwin")

    def test_macos_platform_and_x64_target_are_distinct(self):
        context = ProbeContext(
            Path.cwd(),
            "define/platform",
            (),
            MappingProxyType({"system": "Darwin", "pointer_bytes": "8"}),
        )
        facts = platform_facts(context)
        self.assertTrue(facts["macos"].value)
        self.assertTrue(facts["x64"].value)
        self.assertFalse(facts["x86"].value)

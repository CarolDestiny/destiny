import unittest
from dataclasses import replace

from tool.auto_define_config.contracts import Declaration, Field, Observation, validate_declarations
from tool.auto_define_config.errors import ConfigError


def definition(**overrides):
    data = {
        "id": "cpu.intel",
        "type": "boolean",
        "macro": "DESTINY_DEFINE_CMAKE_CPU_INTEL",
        "alias": "DESTINY_DEFINE_CPU_INTEL",
        "description": "Intel CPU vendor",
    }
    data.update(overrides)
    return Field.from_data(data)


class ContractTests(unittest.TestCase):
    def test_boolean_observation_roundtrip(self):
        result = Observation.available(False, provider="fixture").to_data(definition())
        self.assertIs(result["value"], False)
        self.assertEqual(result["status"], "available")

    def test_unavailable_is_not_a_fabricated_observation(self):
        result = Observation.unavailable("Access denied", status="denied").to_data(definition())
        self.assertIsNone(result["value"])
        self.assertEqual(result["status"], "denied")

    def test_integer_precision_survives_json_boundary(self):
        item = definition(id="memory.bytes", type="integer", unit="bytes")
        result = Observation.available(2**63 - 1, provider="fixture").to_data(item)
        self.assertEqual(result["value"], str(2**63 - 1))
        with self.assertRaises(ConfigError):
            Observation.available(True, provider="fixture").to_data(item)
        with self.assertRaises(ConfigError):
            Observation.available(2**63, provider="fixture").to_data(item)

    def test_declarations_reject_unknown_and_wrong_types(self):
        for data in (
            {"surprise": True},
            {"type": "float"},
            {"unit": "bytes"},
            {"macro": "BAD"},
            {"id": "bad;execute"},
            {"default": False},
            {"kind": "option"},
        ):
            with self.subTest(data=data), self.assertRaises(ConfigError):
                definition(**data)

    def test_options_require_typed_defaults(self):
        self.assertIs(definition(kind="option", default=False).default, False)
        with self.assertRaises(ConfigError):
            definition(kind="option", default=0)

    def test_collision_checks_include_availability_macros(self):
        first = definition()
        second = replace(first, id="cpu.other", macro=first.macro + "_AVAILABLE", alias=None)
        with self.assertRaisesRegex(ConfigError, "Duplicate generated macro"):
            validate_declarations((Declaration("define/cpu", (first, second)),))

    def test_schema_and_module_identity_are_strict(self):
        for data in (
            {"schema_version": True, "module": "define/cpu", "fields": []},
            {"schema_version": 1, "module": "define/other", "fields": []},
        ):
            with self.assertRaises(ConfigError):
                Declaration.from_data(data, module="define/cpu")

    def test_provider_bugs_are_errors(self):
        for observation in (
            Observation("nonsense"),
            Observation.available(1, provider="fixture"),
            Observation("denied", value=False, reason="denied", provider="fixture"),
        ):
            with self.assertRaises(ConfigError):
                observation.to_data(definition())

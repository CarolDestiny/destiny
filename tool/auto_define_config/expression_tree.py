"""Editing operations and display for condition trees; no condition evaluation."""

from __future__ import annotations
import copy
import json
from typing import Any
from .errors import ConfigError
from .rules import validate_expression


def expression_text(expression: Any) -> str:
    if type(expression) is bool:
        return "TRUE" if expression else "FALSE"
    operation, value = next(iter(expression.items()))
    if operation == "ref":
        return value
    if operation == "not":
        return f"NOT ({expression_text(value)})"
    if operation in ("all", "any"):
        separator = " AND " if operation == "all" else " OR "
        return "(" + separator.join(expression_text(child) for child in value) + ")"
    symbols = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}
    suffix = f" {value['unit']}" if value.get("unit") else ""
    return f"{value['field']} {symbols[value['op']]} {json.dumps(value['value'])}{suffix}"


def children(expression: Any) -> list:
    if isinstance(expression, dict):
        if "all" in expression:
            return expression["all"]
        if "any" in expression:
            return expression["any"]
        if "not" in expression:
            return [expression["not"]]
    return []


class ExpressionTree:
    def __init__(self, expression: Any):
        validate_expression(expression)
        self.root = copy.deepcopy(expression)

    def get(self, path: tuple[int, ...]):
        current = self.root
        for index in path:
            nodes = children(current)
            if index < 0 or index >= len(nodes):
                raise ConfigError("Condition selection no longer exists")
            current = nodes[index]
        return current

    def replace(self, path: tuple[int, ...], expression: Any):
        validate_expression(expression)
        if not path:
            self.root = copy.deepcopy(expression)
            return
        parent = self.get(path[:-1])
        index = path[-1]
        if isinstance(parent, dict) and "not" in parent:
            if index != 0:
                raise ConfigError("NOT has exactly one child")
            parent["not"] = copy.deepcopy(expression)
        else:
            nodes = children(parent)
            if index < 0 or index >= len(nodes):
                raise ConfigError("Invalid condition path")
            nodes[index] = copy.deepcopy(expression)

    def append(self, path: tuple[int, ...], expression: Any = True):
        parent = self.get(path)
        if not isinstance(parent, dict) or not ("all" in parent or "any" in parent):
            raise ConfigError("Add child requires an ALL or ANY node")
        validate_expression(expression)
        children(parent).append(copy.deepcopy(expression))

    def remove(self, path: tuple[int, ...]):
        if not path:
            raise ConfigError("Replace the root; it cannot be removed")
        parent = self.get(path[:-1])
        nodes = children(parent)
        if "not" in parent or len(nodes) == 1:
            raise ConfigError("This operator needs at least one child")
        del nodes[path[-1]]

    def move(self, path: tuple[int, ...], delta: int):
        if not path:
            raise ConfigError("Root cannot be reordered")
        nodes = children(self.get(path[:-1]))
        index = path[-1]
        target = index + delta
        if target < 0 or target >= len(nodes):
            return
        nodes[index], nodes[target] = nodes[target], nodes[index]

import pytest
from app.services.workflow_engine import WorkflowEngine


def test_valid_transition():
    engine = WorkflowEngine(
        states=["设计中", "审核中", "已发布"],
        transitions=[
            {"from": "设计中", "to": "审核中", "roles": ["designer", "manager"]},
            {"from": "审核中", "to": "已发布", "roles": ["manager"]},
            {"from": "审核中", "to": "设计中", "roles": ["manager"]},
        ]
    )
    assert engine.can_transition("设计中", "审核中", "designer") is True
    assert engine.can_transition("审核中", "已发布", "manager") is True


def test_invalid_transition():
    engine = WorkflowEngine(
        states=["设计中", "审核中", "已发布"],
        transitions=[
            {"from": "设计中", "to": "审核中", "roles": ["designer"]},
            {"from": "审核中", "to": "已发布", "roles": ["manager"]},
        ]
    )
    assert engine.can_transition("设计中", "已发布", "designer") is False
    assert engine.can_transition("设计中", "审核中", "viewer") is False


def test_no_matching_transition():
    engine = WorkflowEngine(
        states=["设计中", "审核中", "已发布"],
        transitions=[
            {"from": "设计中", "to": "审核中", "roles": ["designer"]},
        ]
    )
    assert engine.can_transition("已发布", "设计中", "admin") is False


def test_empty_transitions():
    engine = WorkflowEngine(states=["设计中", "审核中"], transitions=[])
    assert engine.can_transition("设计中", "审核中", "designer") is False


def test_from_template():
    class MockTemplate:
        states = ["设计中", "审核中", "已发布"]
        transitions = [
            {"from": "设计中", "to": "审核中", "roles": ["designer"]},
        ]

    engine = WorkflowEngine.from_template(MockTemplate())
    assert engine.states == ["设计中", "审核中", "已发布"]
    assert engine.can_transition("设计中", "审核中", "designer") is True

"""
Tests for BKT (Bayesian Knowledge Tracing) service.
"""

import pytest
from app.services.bkt import BKTModel, update_progress, get_student_skills


def test_bkt_model_initialization():
    """Test BKT model initialization with default parameters."""
    model = BKTModel()
    assert model.p_initial == 0.5
    assert model.p_learn == 0.3
    assert model.p_guess == 0.2
    assert model.p_slip == 0.1
    assert model.mastery_threshold == 0.95


def test_bkt_model_custom_params():
    """Test BKT model initialization with custom parameters."""
    model = BKTModel(
        p_initial=0.3,
        p_learn=0.5,
        p_guess=0.15,
        p_slip=0.05,
        mastery_threshold=0.9
    )
    assert model.p_initial == 0.3
    assert model.p_learn == 0.5
    assert model.p_guess == 0.15
    assert model.p_slip == 0.05
    assert model.mastery_threshold == 0.9


def test_update_mastery_correct():
    """Test mastery update after correct answer."""
    model = BKTModel()
    current = 0.5

    # Correct answer should increase mastery
    updated = model.update_mastery(current, is_correct=True)
    assert updated > current
    assert 0 <= updated <= 1


def test_update_mastery_incorrect():
    """Test mastery update after incorrect answer."""
    model = BKTModel()
    current = 0.7

    # Incorrect answer should decrease mastery (but can still learn)
    updated = model.update_mastery(current, is_correct=False)
    assert 0 <= updated <= 1


def test_consecutive_correct_answers():
    """Test mastery improvement with consecutive correct answers."""
    model = BKTModel()
    mastery = 0.5

    for _ in range(5):
        mastery = model.update_mastery(mastery, is_correct=True)

    # Should have increased significantly
    assert mastery > 0.6


def test_consecutive_incorrect_answers():
    """Test mastery decrease with consecutive incorrect answers."""
    model = BKTModel()
    mastery = 0.7

    for _ in range(5):
        mastery = model.update_mastery(mastery, is_correct=False)

    # Should have decreased
    assert mastery < 0.7


def test_mastery_threshold():
    """Test mastery threshold detection."""
    model = BKTModel(mastery_threshold=0.95)

    assert not model.is_mastered(0.94)
    assert model.is_mastered(0.95)
    assert model.is_mastered(1.0)


def test_boundary_values():
    """Test mastery update at boundary values."""
    model = BKTModel()

    # Test at 0
    mastery = model.update_mastery(0.0, is_correct=True)
    assert 0 <= mastery <= 1

    # Test at 1
    mastery = model.update_mastery(1.0, is_correct=False)
    assert 0 <= mastery <= 1

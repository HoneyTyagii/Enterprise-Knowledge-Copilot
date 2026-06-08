from __future__ import annotations

import pytest

from app.rag.answer_verification import apply_abstain_policy


def test_abstain_when_ungrounded():
    res = apply_abstain_policy(
        verification_result={"grounded": False},
        answer="draft answer",
    )
    assert res["verdict"] == "ungrounded"


def test_no_abstain_when_grounded():
    res = apply_abstain_policy(
        verification_result={"grounded": True},
        answer="draft answer",
    )
    assert res["verdict"] == "grounded"
    assert res["final_answer"] == "draft answer"


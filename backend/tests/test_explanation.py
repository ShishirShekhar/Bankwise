from app.ai import explanation
from app.ai.explanation import build_facts, explain, format_inr, is_grounded
from app.ai.extraction import Requirements
from app.ai.pipeline import Option

REQ = Requirements(category="FD", amount=500000, duration_months=24, liquidity_need="HIGH")
OPTIONS = [
    Option(bank="alpha", rate_percent=7.25, maturity_amount=577269.77, interest_earned=77269.77,
           early_exit_months=12, early_exit_amount=526000.0, penalty_pp=1.5, lock_in_months=6),
    Option(bank="bravo", rate_percent=7.0, maturity_amount=574440.89, interest_earned=74440.89,
           early_exit_months=12, early_exit_amount=532000.0, penalty_pp=0.5, lock_in_months=0),
]


def test_indian_grouping():
    assert format_inr(577269.77) == "₹5,77,270"
    assert format_inr(100000) == "₹1,00,000"


def test_grounded_text_passes():
    facts = build_facts(REQ, OPTIONS, "bravo")
    assert is_grounded("alpha gives ₹5,77,270 at 7.25% while bravo penalty is 0.5%", facts)


def test_invented_number_fails():
    facts = build_facts(REQ, OPTIONS, "bravo")
    assert not is_grounded("alpha gives ₹6,50,000 at maturity", facts)
    assert not is_grounded("alpha pays 9.5% interest", facts)


def test_bad_gemini_text_falls_back_to_template(monkeypatch):
    monkeypatch.setattr(explanation, "_generate", lambda _f: "You will get ₹9,99,999 guaranteed.")
    text = explain(REQ, OPTIONS, "bravo")
    assert "9,99,999" not in text and "alpha" in text and "bravo" in text


def test_good_gemini_text_is_used(monkeypatch):
    good = "Alpha reaches ₹5,77,270, while bravo pays more if you leave early."
    monkeypatch.setattr(explanation, "_generate", lambda _f: good)
    assert explain(REQ, OPTIONS, "bravo") == good
    
def test_plain_numbers_are_checked_too():
    facts = build_facts(REQ, OPTIONS, "bravo")
    assert is_grounded("Alpha offers 7.25 percent, maturing at 577269.77 rupees", facts)
    assert not is_grounded("Alpha offers 7.5 percent", facts)
    assert not is_grounded("Bravo gives 570000 rupees", facts)


def test_your_real_gemini_output_passes():
    options = [
        Option(bank="alpha", rate_percent=7.25, maturity_amount=577269.77, interest_earned=77269.77,
               early_exit_months=12, early_exit_amount=529375.88, penalty_pp=1.5, lock_in_months=6),
        Option(bank="bravo", rate_percent=7.0, maturity_amount=574440.89, interest_earned=74440.89,
               early_exit_months=12, early_exit_amount=533300.8, penalty_pp=0.5, lock_in_months=0),
        Option(bank="charlie", rate_percent=6.9, maturity_amount=573312.74, interest_earned=73312.74,
               early_exit_months=12, early_exit_amount=530159.13, penalty_pp=1.0, lock_in_months=0),
    ]
    text = ("If you need funds early, Bravo is best. At 12 months, you'd get 533300.8 rupees with a 0.5 "
            "percentage point penalty. Alpha, with a 6-month lock-in, gives 529375.88 rupees "
            "(1.5 percentage point penalty). Alpha offers 7.25 percent, maturing at 577269.77 rupees.")
    assert is_grounded(text, build_facts(REQ, options, "bravo"))
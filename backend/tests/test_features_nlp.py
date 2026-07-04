"""Tests for ML feature engineering and NLP helpers/pipeline."""
import db
import features as F
import nlp
from config import RISK_FEATURES


def test_build_panel_has_features(dataset):
    panel = F.build_panel(db.load_cases())
    for col in RISK_FEATURES + ["target_count", "week_idx"]:
        assert col in panel.columns
    train = F.training_frame(panel)
    assert len(train) > 0
    assert not train[RISK_FEATURES].isna().any().any()   # no NaNs after training_frame


def test_latest_frame_one_row_per_district(dataset):
    panel = F.build_panel(db.load_cases())
    latest = F.latest_frame(panel)
    assert latest["DistrictID"].is_unique


def test_clean_text_drops_digits_and_stopwords():
    out = nlp.clean_text("The accused stole Rs 50,000 and a MOBILE phone!!!")
    assert "50" not in out and "rs" not in out.split()
    assert "the" not in out.split()
    assert "mobile" in out and "phone" in out


def test_entity_extraction():
    ents = nlp.extract_entities(
        "Accused threatened with a knife and fled on a motorcycle with gold ornaments worth Rs 20,000")
    assert "knife" in ents.get("weapon", [])
    assert "motorcycle" in ents.get("vehicle", [])
    assert "gold ornaments" in ents.get("stolen_item", [])
    assert ents.get("amount")


def test_candidate_models_build():
    cand = nlp.candidates()
    assert len(cand) >= 15            # the bake-off is large
    assert "multinomial_nb" in cand and "mlp" in cand


def test_one_nlp_pipeline_fits(dataset):
    """Fit a single fast classifier end-to-end (proves the NLP pipeline works)."""
    dfc = db.load_cases()[["BriefFacts", "CrimeHead"]].dropna()
    dfc = dfc.assign(clean=dfc["BriefFacts"].map(nlp.clean_text))
    pipe = nlp.candidates()["multinomial_nb"]
    pipe.fit(dfc["clean"], dfc["CrimeHead"])
    pred = pipe.predict(dfc["clean"].head(5))
    assert len(pred) == 5

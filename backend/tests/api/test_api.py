#zetten hier alle testen voor api in (import alles voor app, dus denk alles backend

#?? from fastapi.testclient import TestClient
#?? client = TestClient(app)
# test eit data filteren

import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))  # dit heeft copilot voor me gedaan, zodat de backend map wordt toegevoegd aan sys.path en de imports van de app werken

from app.services.signal_processing import extract_minmax_breath_frames 

# test voor EIT data filteren en pieken detecteren
def make_test_data(num_frames=15): #  maakt een test EIT data set, 15 frames van 2x2 pixels die hier wordt gebruikt
    eit_data = np.zeros((num_frames, 2, 2), dtype=float)
    for i in range(num_frames):
        eit_data[i] = i
    return eit_data


def mock_peak_detection(monkeypatch, inspiration, expiration): # deze test controleert of de code zelfstandig lokale maxima (inspiratiepieken) en lokale minima (expiratiepieken) kan detecteren in een testsignaal met bekende waarden
    calls = {"count": 0}
    def test_find_peaks(data, distance): 
        calls["count"] += 1
        if calls["count"] == 1:
            return np.array(inspiration), {}
        else:
            return np.array(expiration), {}

    monkeypatch.setattr("app.services.signal_processing.find_peaks", test_find_peaks)


def test_output_shapes_and_types(monkeypatch): # deze test controleert of de functie een inspiratieframe en expiratieframe van 2 × 2 pixels en een dictionary met aanvullende informatie teruggeeft
    eit_data = make_test_data()
    time_data = np.linspace(0, 1.5, 15) # komt uit op 15 tijdstippen, van 0 tot 1.5 seconden, dus een sample rate van 10 Hz
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12]) 

    insp, exp, indices = extract_minmax_breath_frames(eit_data, time_data, 0.6, 2) # lowpass cutoff van 0.6 Hz en gemiddelde van de laatste 2 ademhalingen

    assert insp.shape == (2, 2)
    assert exp.shape == (2, 2)
    assert isinstance(indices, dict)


def test_selected_frames_are_averaged(monkeypatch): # controleert of de functie de juiste piekjes pakt en de juiste frame gemiddelde teruggeeft
    eit_data = make_test_data()
    time_data = np.linspace(0, 1.5, 15)
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12])

    insp, exp, _ = extract_minmax_breath_frames(eit_data, time_data, 0.6, 2)

    assert np.allclose(insp, 8.0)
    assert np.allclose(exp, 10.0)


def test_returns_correct_peak_indices(monkeypatch): # controleer of de functie de juiste piek indices geeft
    eit_data = make_test_data()
    time_data = np.linspace(0, 1.5, 15)
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12])

    _, _, indices = extract_minmax_breath_frames(eit_data, time_data, 0.6, 2)

    np.testing.assert_array_equal(indices["insp_indices"], [6, 10])
    np.testing.assert_array_equal(indices["exp_indices"], [8, 12])


def test_global_impedance_is_sum_of_pixels(monkeypatch): # deze test controleert of de globale impedantie correct wordt berekend als de som van alle pixels in elk frame
    eit_data = make_test_data()
    time_data = np.linspace(0, 1.5, 15)
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12])

    _, _, indices = extract_minmax_breath_frames(eit_data, time_data, 0.6, 2)

    expected = np.arange(15) * 4
    np.testing.assert_allclose(indices["global_impedance_raw"], expected)


def test_raises_error_when_not_enough_breaths(monkeypatch): # deze test controleert of de functie van ValueError een foutmelding geeft wanneer er niet genoeg complete ademhalingen in de inputdata aanwezig zijn
    eit_data = make_test_data()
    time_data = np.linspace(0, 1.5, 15)
    mock_peak_detection(monkeypatch, inspiration=[2, 6], expiration=[4])

    with pytest.raises(ValueError, match="Not enough complete breaths found"):
        extract_minmax_breath_frames(eit_data, time_data, 0.6, 2)
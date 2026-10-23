#zetten hier alle testen voor api in (import alles voor app, dus denk alles backend)
from app.main import app, extract_minmax_breath_frames, compliance_matrix, collapse_berekenen

#?? from fastapi.testclient import TestClient
#?? client = TestClient(app)
# test eit data filteren
import numpy as np
import pytest

# extract_minmax_breath_frames tests
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
    monkeypatch.setattr("find_peaks", test_find_peaks)

def test_output_shapes_and_types(monkeypatch): # deze test controleert of de functie een inspiratieframe en expiratieframe van 2 × 2 pixels en een dictionary met aanvullende informatie teruggeeft
    eit_data = make_test_data()
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12])
    insp, exp, indices= extract_minmax_breath_frames(eit_data, sampling_freq=10, num_breaths_to_average=2)

    assert insp.shape == (2, 2)
    assert exp.shape == (2, 2)
    assert isinstance(indices, dict)

def test_selected_frames_are_averaged(monkeypatch): # controleert of de functie de juiste piekjes pakt en de juiste frame gemiddelde teruggeeft
    eit_data = make_test_data() 
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12])
    insp, exp = extract_minmax_breath_frames(eit_data, sampling_freq=10, num_breaths_to_average=2)

    assert np.allclose(insp, 8.0)
    assert np.allclose(exp, 10.0)

def test_returns_correct_peak_indices(monkeypatch): # controleer of de functie de juiste piek indices geeft
    eit_data = make_test_data()
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12])
    indices = extract_minmax_breath_frames(eit_data, sampling_freq=10, num_breaths_to_average=2)
    
    np.testing.assert_array_equal(indices["insp_indices"], [6, 10])
    np.testing.assert_array_equal(indices["exp_indices"], [8, 12])

def test_global_impedance_is_sum_of_pixels(monkeypatch): # deze test controleert of de globale impedantie correct wordt berekend als de som van alle pixels in elk frame
    eit_data = make_test_data()
    mock_peak_detection(monkeypatch, inspiration=[2, 6, 10], expiration=[4, 8, 12])
    indices = extract_minmax_breath_frames(eit_data, sampling_freq=10, num_breaths_to_average=2)
    
    expected = np.arange(15) * 4
    np.testing.assert_allclose(indices["global_impedance_raw"], expected)

def test_raises_error_when_not_enough_breaths(monkeypatch): # deze test controleert of de functie van ValueError een foutmelding geeft wanneer er niet genoeg complete ademhalingen in de inputdata aanwezig zijn 
    eit_data = make_test_data()
    mock_peak_detection(monkeypatch, inspiration=[2, 6], expiration=[4])

    with pytest.raises(ValueError, match="Not enough complete breaths found"):
        extract_minmax_breath_frames(eit_data,sampling_freq=10,num_breaths_to_average=2)

# test for compliance_matrix
def test_compliance_matrix_basic():
    matrix1 = np.array([[10, 20], [30, 40]])
    matrix2 = np.array([[2, 5], [10, 15]])
    Pplat = 20
    PEEP = 5

    result = compliance_matrix(matrix1, matrix2, Pplat, PEEP)

    expected = np.array([
        [8 / 15, 1],
        [4 / 3, 5 / 3]
    ])

    np.testing.assert_allclose(result, expected)

def test_compliance_matrix_zero_difference():
    matrix1 = np.array([[5, 10], [15, 20]])
    matrix2 = np.array([[5, 10], [15, 20]])

    result = compliance_matrix(matrix1, matrix2, 20, 5)

    expected = np.zeros((2, 2))
    np.testing.assert_array_equal(result, expected)

def test_compliance_matrix_negative_values():
    matrix1 = np.array([[1, 2], [3, 4]])
    matrix2 = np.array([[2, 4], [6, 8]])

    result = compliance_matrix(matrix1, matrix2, 15, 5)

    expected = np.array([
        [-0.1, -0.2],
        [-0.3, -0.4]
    ])

    np.testing.assert_allclose(result, expected)

def test_compliance_matrix_zero_division():
    matrix1 = np.array([[10, 20]])
    matrix2 = np.array([[2, 5]])

    with pytest.raises(ZeroDivisionError):
        compliance_matrix(matrix1, matrix2, 5, 5)

def test_collapse_berekenen_overdistention_collapse(): # check if the collapse and overdistion are calculated correctly

    list_of_errors = [] # empty lsit of a errrors to check both overdistention and collapse

    compliance_array = [[[1,1,1],[2,2,2],[3,3,3]],[[1,2,3],[1,2,3],[1,2,3]]]
    overdistention = [[[0, 50.0, 66.66666666666667], [0, 0, 33.333333333333336], [0, 0, 0]], [[0, 0, 0], [0, 0, 0], [0, 0, 0]]] 
    collapse = [[[0.0, 0, 0], [0.0, 0.0, 0], [0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0], [50.0, 0.0, 0.0], [66.66666666666667, 33.333333333333336, 0.0]]]

    result_collapse, result_overdistention = collapse_berekenen(compliance_array)

    if not np.allclose(result_collapse, collapse):
        list_of_errors.append("Collapse calculation error")

    if not np.allclose(result_overdistention, overdistention):
        list_of_errors.append("Overdistention calculation error")

    assert not list_of_errors, "Errors occurred:\n{}".format("\n".join(list_of_errors))



def test_collapse_berekenen_zero_division(): # check if it raises an error when best compliance = 0
    compliance_array = [
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    ]

    with pytest.raises(ZeroDivisionError):
        collapse_berekenen(compliance_array)


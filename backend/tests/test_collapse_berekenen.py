import pytest
import numpy as np

from app.model.collapse_berekenen import collapse_berekenen

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


	


import numpy as np
from scipy.io import savemat

# Replace this import with the actual location of your script
from backend.app.EIDORS import load_eit_data


def test_load_eit_data(tmp_path):
    # Arrange: create a small example MATLAB file
    mat_file = tmp_path / "test_data.mat"

    expected_imgs = np.zeros((32, 32, 3))
    expected_time = np.array([0.0, 0.2, 0.4])

    savemat(mat_file,{"imgs": expected_imgs, "time": expected_time.reshape(-1, 1)})

    # Act: load the data
    imgs, time = load_eit_data(str(mat_file))

    # Assert: check the results
    assert imgs.shape == (32, 32, 3)
    np.testing.assert_array_equal(imgs, expected_imgs)
    np.testing.assert_array_equal(time, expected_time)

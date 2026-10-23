![GitHub License](https://img.shields.io/github/license/computational-biology-tue/digital-twin-demo)
[![Static Badge](https://img.shields.io/badge/Powered_by-Pixi-%23facc15)](https://pixi.prefix.dev/latest/)
[![Static Badge](https://img.shields.io/badge/Built_with-Lit-%23334eff?logo=lit&logoColor=%23334eff&labelColor=white)](https://lit.dev/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Backend Tests](https://github.com/Computational-Biology-TUe/digital-twin-demo/actions/workflows/test.yml/badge.svg)](https://github.com/Computational-Biology-TUe/digital-twin-demo/actions/workflows/test.yml)

This is a repository of a digital twin used to optimize ventilator PEEP based on EIT data. It is made by lung group 1 of the TU/E digital twin course. 

In order to use the digital twin you need to have downloaded and set up EIDORS, a free software algorithm for analysing EIT data. https://eidors3d.sourceforge.net/

Furthermore the following imports are needed:

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.bmi import router as bmi_router
import subprocess
import os
from time import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
from scipy.signal import butter, filtfilt, find_peaks

By running the file backend.app.app_interface.py in python a seperate window with our user interface will open. Currently our frontend is not yet linked with our backend, but it is usable to see what it will look like.

import sys
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "doorstep_verifier")
sys.path.insert(0, BASE_DIR)

from run import app as application
import sys
import os

directory = os.path.dirname(os.path.realpath(__file__))

sys.path.append("{}/../".format(directory))

from autolens.cli import main

main()

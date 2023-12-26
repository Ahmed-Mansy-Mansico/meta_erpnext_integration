# read from meta_integraion copy.py and save to string
# read from meta_integraion.py and save to string
import os
current_path = os.path.dirname(os.path.abspath(__file__))
strr = open(current_path + "/meta_integraion.py", 'r').read()

import yaml
import csv


with open("seminars.csv", 'r') as f:
    reader = csv.DictReader(f)
    data = [row for row in reader]

with open("seminars.yaml", "w") as f:
    yaml.dump(data, f, default_flow_style = False, indent = 2)


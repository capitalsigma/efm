import csv

#see: "elliot wave theory"

spyprice = []
with open("INDEX_GSPC.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        for k, v in row.items():
            spyprice += [float(v)] if k == "Adjusted Close" else []

print(spyprice)

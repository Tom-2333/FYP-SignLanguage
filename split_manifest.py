import csv
import random

with open("data/manifest.csv", encoding="utf-8") as f:
    header = next(f)
    rows = list(csv.reader(f))

random.seed(42)
random.shuffle(rows)

split = int(0.9 * len(rows))
train_rows = rows[:split]
val_rows = rows[split:]

for name, data in [("train", train_rows), ("val", val_rows)]:
    with open(f"data/{name}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "target", "input_lengths", "english_gloss", "chinese_gloss", "cantonese_gloss"])
        writer.writerows(data)
    print(f"{name}.csv: {len(data)} samples")
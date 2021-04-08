import csv

all_articles = []

with open("articles.csv", encoding="UTF-8") as f:
  reader = csv.reader(f)
  data = list(reader)
  all_articles = data[1:]
param(
  [string]$Input = "data/raw/news_sample.jsonl",
  [string]$OutDir = "data/processed"
)
python -m bot.data_ingest --input $Input --out-dir $OutDir

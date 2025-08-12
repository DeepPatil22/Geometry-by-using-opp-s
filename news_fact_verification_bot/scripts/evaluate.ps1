param(
  [string]$Pred = "results/output.jsonl",
  [string]$Gold = "data/eval/claims_labeled.jsonl",
  [string]$Report = "results/report.json"
)
python -m bot.evaluation --pred $Pred --gold $Gold --report $Report

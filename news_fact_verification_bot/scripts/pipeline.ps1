param(
  [string]$Topics = "economy,health,technology",
  [int]$Pages = 1,
  [int]$DaysBack = 7,
  [int]$K = 8,
  [string]$RawOut = "data/raw/news_auto.jsonl",
  [string]$EvalClaims = "data/eval/claims_labeled.jsonl",
  [string]$ProcessedDir = "data/processed",
  [string]$IndexDir = "data/index",
  [string]$ResultsDir = "results",
  [switch]$ForceFetch,
  [switch]$SkipFetch
)

# Step 0: Preconditions
if (!(Test-Path $ResultsDir)) { New-Item -ItemType Directory -Path $ResultsDir | Out-Null }
if (!(Test-Path $ProcessedDir)) { New-Item -ItemType Directory -Path $ProcessedDir | Out-Null }
if (!(Test-Path $IndexDir)) { New-Item -ItemType Directory -Path $IndexDir | Out-Null }

Write-Host "[0] Starting pipeline (topics=$Topics pages=$Pages daysBack=$DaysBack)" -ForegroundColor Cyan

# Step 1: Fetch news (optional)
if ($SkipFetch) {
  Write-Host "[1] Skipping fetch (SkipFetch flag)" -ForegroundColor Yellow
} elseif ((Test-Path $RawOut) -and -not $ForceFetch) {
  Write-Host "[1] Raw file exists ($RawOut); skipping fetch (use -ForceFetch to refetch)" -ForegroundColor Yellow
} else {
  if (-not $env:NEWS_API_KEY) { throw "NEWS_API_KEY not set in environment" }
  Write-Host "[1] Fetching news -> $RawOut" -ForegroundColor Cyan
  python -m bot.fetch_news --topics $Topics --pages $Pages --days-back $DaysBack --out $RawOut
  if ($LASTEXITCODE -ne 0) { throw "fetch_news failed" }
}

# Step 2: Ingest raw -> processed
Write-Host "[2] Ingesting raw file(s) to chunks ($ProcessedDir)" -ForegroundColor Cyan
python -m bot.data_ingest --input $RawOut --out-dir $ProcessedDir
if ($LASTEXITCODE -ne 0) { throw "data_ingest failed" }

# Step 3: Build / refresh embeddings + vector store
Write-Host "[3] Building embeddings & vector store ($IndexDir)" -ForegroundColor Cyan
python -m bot.embed --input $ProcessedDir --persist-dir $IndexDir
if ($LASTEXITCODE -ne 0) { throw "embed build failed" }

# Step 4: Run BM25 baseline batch (store retrieved)
$Bm25Pred = Join-Path $ResultsDir "run_bm25.jsonl"
Write-Host "[4] Running BM25 baseline -> $Bm25Pred" -ForegroundColor Cyan
python -m bot.cli --batch $EvalClaims --baseline --processed-dir $ProcessedDir --store-retrieved --out $Bm25Pred --k $K
if ($LASTEXITCODE -ne 0) { throw "BM25 batch failed" }

# Step 5: Run RAG dense batch (store retrieved)
$RagPred = Join-Path $ResultsDir "run_rag.jsonl"
Write-Host "[5] Running RAG dense -> $RagPred" -ForegroundColor Cyan
python -m bot.cli --batch $EvalClaims --store-retrieved --out $RagPred --k $K
if ($LASTEXITCODE -ne 0) { throw "RAG batch failed" }

# Step 6: Evaluate both (extended)
$Bm25Report = Join-Path $ResultsDir "report_bm25.json"
$RagReport  = Join-Path $ResultsDir "report_rag.json"
Write-Host "[6] Evaluating BM25" -ForegroundColor Cyan
python -m bot.evaluation --pred $Bm25Pred --gold $EvalClaims --report $Bm25Report --extended
if ($LASTEXITCODE -ne 0) { throw "BM25 evaluation failed" }
Write-Host "[6] Evaluating RAG" -ForegroundColor Cyan
python -m bot.evaluation --pred $RagPred --gold $EvalClaims --report $RagReport --extended
if ($LASTEXITCODE -ne 0) { throw "RAG evaluation failed" }

# Step 7: Summarize key metrics
Write-Host "[7] Summarizing metrics" -ForegroundColor Cyan
$bm25 = Get-Content $Bm25Report | ConvertFrom-Json
$rag  = Get-Content $RagReport  | ConvertFrom-Json

$summary = [ordered]@{}
$fields = @('context_precision','answer_relevancy','faithfulness','false_positive_rate','median_latency_s')
foreach ($f in $fields) {
  $bm25Val = $bm25.extended.$f
  $ragVal  = $rag.extended.$f
  $summary[$f] = @{ bm25 = $bm25Val; rag = $ragVal; improvement = if (($bm25Val -ne $null) -and ($ragVal -ne $null) -and ($bm25Val -ne 0)) { [math]::Round((($ragVal - $bm25Val)/[math]::Abs($bm25Val))*100,2) } else { $null } }
}
$summaryObj = @{ generated_at = (Get-Date).ToString('s'); k = $K; metrics = $summary }
$SummaryPath = Join-Path $ResultsDir "summary_metrics.json"
$summaryObj | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $SummaryPath
Write-Host "[done] Summary -> $SummaryPath" -ForegroundColor Green

Write-Host "\nMetric Comparison:" -ForegroundColor Cyan
$rows = foreach ($f in $fields) {
  $bm25Val = $summary[$f].bm25
  $ragVal  = $summary[$f].rag
  $imp     = $summary[$f].improvement
  [pscustomobject]@{ Metric = $f; BM25 = $bm25Val; RAG = $ragVal; ImprovementPct = $imp }
}
$rows | Format-Table -AutoSize

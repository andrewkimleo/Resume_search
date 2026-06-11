# Antigravity Ranking System

This is the repository for the Intelligent Candidate Discovery & Ranking Challenge submission by team **Antigravity**.

## Architecture & Methodology
To comply perfectly with the strict computational constraints (≤ 5 mins wall-clock time, ≤ 16GB RAM, NO network APIs), our submission utilizes a highly optimized **Streaming Offline Heuristic Ranker**.

The pipeline stream-processes the input `.jsonl` or `.jsonl.gz` file line-by-line using Python generators, feeding the candidates into an in-memory Min-Heap configured to size 100. This ensures memory usage remains near-zero regardless of the dataset size.

### Evaluation Pillars
The ranking score is computed via a pure Python offline algorithm observing five pillars:
1. **Core Skills Match**: Scans for JD-required tools (Python, NLP, PyTorch, RAG). Applies a trust multiplier weighting skills with high endorsements and actual `years_used`.
2. **Career History**: Evaluates `current_title` and past titles.
3. **Experience Match**: Validates `years_of_experience` against the JD constraint (5+ years).
4. **Redrob Signal Modifier**: Uses the behavioral signals to multiply the candidate's base score. High response rates, high interview completion rates, and verified GitHubs act as major boosts. Inactive profiles or non-responders are penalized.
5. **Honeypot Disqualification**: Actively analyzes constraints logically. E.g. If a skill claims `expert` proficiency but `years_used == 0`, or if `notice_period_days > 180`, the candidate score is set to exactly 0.0 to prevent honeypot poisoning.

## Setup & Run Instructions

**1. Install Dependencies**
No external dependencies are required! The core ranking script is written 100% in standard Python 3 libraries (`json`, `gzip`, `heapq`, `csv`, `argparse`).

**2. Execute the Pipeline**
Run the ranking algorithm by executing the following command in your terminal. You can pass the path to the uncompressed or gzipped jsonl file directly:
```bash
python rank.py --candidates "./[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl" --out "./team_antigravity.csv"
```

**3. Validate**
After execution, validate the output using the provided hackathon validator:
```bash
python validate_submission.py team_antigravity.csv
```

import json
import gzip
import csv
import argparse
import heapq
import datetime

# --- JD Core Constraints ---
JD_CORE_SKILLS = {"python", "machine learning", "ml", "deep learning", "pytorch", "tensorflow", "nlp", "llm", "generative ai", "rag", "vector database", "pinecone", "milvus", "qdrant"}
PRODUCT_ML_KEYWORDS = {"recommendation", "search", "ranking", "retrieval", "recsys", "information retrieval"}
CONSULTING_FIRMS = {"tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"}

def get_years_diff(start_date_str, end_date_str):
    if not start_date_str: return 0
    try:
        start_year = int(start_date_str[:4])
        if end_date_str:
            end_year = int(end_date_str[:4])
        else:
            end_year = 2024 # Assumed current year
        return max(0, end_year - start_year)
    except:
        return 0

def score_candidate(candidate):
    """
    Scores a candidate based on ultra-accurate offline heuristics derived from JD.
    Returns (score: float, reasoning: str)
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    signals = candidate.get("redrob_signals", {})
    
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "").lower()
    country = profile.get("country", "").lower()
    location = profile.get("location", "").lower()
    
    # ------------------------------------------------------------------
    # 1. IMMEDIATE DISQUALIFIERS & HONEYPOTS (Score = 0.0)
    # ------------------------------------------------------------------
    
    # Honeypot: Impossible expertise
    for skill in skills:
        prof = skill.get("proficiency", "").lower()
        years_used = skill.get("years_used", 0)
        if prof in ["expert", "advanced"] and years_used == 0:
            return 0.0, "Disqualified: Honeypot trap (expert proficiency with 0 years used)."
            
    # Honeypot / Trap: Marketing Managers with AI skills
    if "marketing" in title or "sales" in title or "hr" in title or "recruiter" in title:
        return 0.0, "Disqualified: Current title severely mismatched despite skill keywords."
        
    # Trap: Pure Researchers
    if "researcher" in title and "engineer" not in title and "applied" not in title:
        return 0.0, "Disqualified: JD explicitly rejects pure research backgrounds."
        
    # Trap: Non-Coders (Architects/Managers who haven't coded recently)
    if any(x in title for x in ["architect", "director", "manager", "head", "vp"]):
        if "engineer" not in title and "developer" not in title:
            return 0.0, "Disqualified: JD explicitly rejects senior staff who moved into non-coding roles."

    # Trap: Consulting Firms Only
    # Check if they have ONLY worked at consulting firms
    worked_at_product = False
    if len(career) > 0:
        for job in career:
            company = job.get("company", "").lower()
            if not any(c in company for c in CONSULTING_FIRMS):
                worked_at_product = True
                break
        if not worked_at_product:
            return 0.0, "Disqualified: JD explicitly rejects candidates with ONLY consulting firm experience."

    # Trap: Absurd Notice Period
    if signals.get("notice_period_days", 0) > 180:
        return 0.0, "Disqualified: Notice period exceeds 180 days."

    # Trap: Vision/Speech Only (No NLP/IR)
    has_vision_speech = any(k in s.get("name", "").lower() for s in skills for k in ["computer vision", "opencv", "speech", "robotics"])
    has_nlp_ir = any(k in s.get("name", "").lower() for s in skills for k in ["nlp", "llm", "rag", "retrieval", "search", "information retrieval"])
    if has_vision_speech and not has_nlp_ir:
        return 0.0, "Disqualified: JD explicitly rejects pure Vision/Speech backgrounds without NLP/IR."

    # Trap: Fake AI (LangChain wrapper without depth)
    langchain_yrs = 0
    deep_ml_yrs = 0
    for s in skills:
        name = s.get("name", "").lower()
        yrs = s.get("years_used", 0)
        if "langchain" in name or "openai" in name:
            langchain_yrs = max(langchain_yrs, yrs)
        if name in ["pytorch", "tensorflow", "machine learning", "deep learning"]:
            deep_ml_yrs = max(deep_ml_yrs, yrs)
            
    if langchain_yrs > 0 and langchain_yrs <= 1 and deep_ml_yrs < 2:
        return 0.0, "Disqualified: JD rejects candidates with only recent LangChain experience and no deep ML background."


    # ------------------------------------------------------------------
    # 2. SCORING ENGINE
    # ------------------------------------------------------------------
    score = 0.0
    reasoning_flags = []
    
    # Pillar A: Experience (Ideal 4-8 years)
    if 4 <= yoe <= 8:
        score += 0.2
        reasoning_flags.append(f"Ideal YOE ({yoe})")
    elif 8 < yoe <= 12:
        score += 0.15
        reasoning_flags.append(f"High YOE ({yoe})")
    elif yoe >= 3:
        score += 0.1
        reasoning_flags.append(f"Adequate YOE ({yoe})")
        
    # Pillar B: Core Skills & Trust Multiplier
    skill_score = 0.0
    matched_skills = []
    for skill in skills:
        name = skill.get("name", "").lower()
        if any(k in name for k in JD_CORE_SKILLS):
            matched_skills.append(skill.get("name"))
            yrs = skill.get("years_used", 0)
            end = skill.get("endorsements", 0)
            trust = 1.0 + min(end / 50.0, 0.5) + min(yrs / 5.0, 0.5)
            skill_score += (0.05 * trust)
    
    skill_score = min(skill_score, 0.3)
    score += skill_score
    if len(matched_skills) > 4:
        reasoning_flags.append(f"Deep core ML skill overlap")
        
    # Pillar C: Product ML / Golden Keyword Match
    # Scrape career descriptions for "recommendation", "search", "ranking", etc.
    product_ml_score = 0.0
    has_product_ml = False
    for job in career:
        desc = job.get("description", "").lower()
        if any(k in desc for k in PRODUCT_ML_KEYWORDS):
            product_ml_score = 0.25
            has_product_ml = True
            break
            
    score += product_ml_score
    if has_product_ml:
        reasoning_flags.append("Proven experience building Search/Ranking/Retrieval systems")

    # Pillar D: Logistics Match
    if country != "india":
        score -= 0.1
        reasoning_flags.append("Outside India (No sponsorship)")
    elif any(loc in location for loc in ["pune", "noida", "delhi", "ncr"]):
        score += 0.05
        reasoning_flags.append("Ideal location")
        
    notice = signals.get("notice_period_days", 30)
    if notice <= 30:
        score += 0.05
    elif notice >= 60:
        score -= 0.05
        
    # Pillar E: Redrob Behavioral Signals
    # Max possible modifier is heavily influenced by JD wants (open source, responsiveness)
    modifier = 0.9 # Start slightly pessimistic
    
    if signals.get("recruiter_response_rate", 0) > 0.8:
        modifier += 0.1
    if signals.get("recruiter_response_rate", 1.0) < 0.3:
        modifier -= 0.2
        reasoning_flags.append("Poor recruiter response rate")
        
    if signals.get("interview_completion_rate", 0) > 0.8:
        modifier += 0.1
        
    github = signals.get("github_activity_score", -1)
    if github > 70:
        modifier += 0.15
        reasoning_flags.append("Strong open-source validation")
    elif github == -1 and yoe > 5:
        # JD Trap: "entirely closed source for 5+ years without validation"
        modifier -= 0.1
        
    if signals.get("last_active_date", "") == "":
        modifier -= 0.15

    # Final tally
    score = score * modifier
    score = max(0.0, min(score, 1.0))
    
    if score > 0.0:
        reasoning = ", ".join(reasoning_flags).capitalize() + f"."
    else:
        reasoning = "Does not meet core requirements."
        
    return score, reasoning

def process_candidates(input_file, output_file):
    print(f"Reading from {input_file}...")
    open_func = gzip.open if str(input_file).endswith('.gz') else open
    top_k = []
    
    count = 0
    with open_func(input_file, 'rt', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            cid = candidate.get("candidate_id")
            if not cid: continue
                
            score, reasoning = score_candidate(candidate)
            
            if len(top_k) < 100:
                heapq.heappush(top_k, (score, cid, reasoning))
            else:
                smallest_score, smallest_cid, _ = top_k[0]
                if score > smallest_score or (score == smallest_score and cid < smallest_cid):
                    heapq.heappushpop(top_k, (score, cid, reasoning))
                    
            count += 1
            if count % 10000 == 0:
                print(f"Processed {count} candidates...")
                
    print(f"Total candidates processed: {count}")
    
    results = []
    while top_k:
        score, cid, reasoning = heapq.heappop(top_k)
        # Round the score to 4 decimal places BEFORE sorting, 
        # so that floating point micro-differences don't break the CSV tie-breaker rule.
        results.append((round(score, 4), cid, reasoning))
        
    results.sort(key=lambda x: (-x[0], x[1]))
    
    print(f"Writing top {len(results)} to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (score, cid, reasoning) in enumerate(results, start=1):
            writer.writerow([cid, rank, f"{score:.4f}", reasoning[:200]])
            
    print("Ranking complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V2 Ultra-Accurate Ranker")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    process_candidates(args.candidates, args.out)

import os
from pathlib import Path

base_dir = Path(__file__).parent

files_to_delete = [
    "hackathon_runner.py",
    "clean_repo.py",
    "read_docs.py",
    "parsed_docs.txt",
    "Top_5_Candidates_Report.md",
    "backend/ai_service.py",
    "backend/models/schemas.py",
    "backend/requirements.txt"
]

for f in files_to_delete:
    p = base_dir / f
    if p.exists():
        os.remove(p)
        print(f"Deleted {f}")

# Also try to remove empty backend directory
backend_dir = base_dir / "backend" / "models"
if backend_dir.exists():
    try:
        os.rmdir(backend_dir)
    except:
        pass
        
backend_dir = base_dir / "backend"
if backend_dir.exists():
    try:
        os.rmdir(backend_dir)
        print("Deleted empty backend directory")
    except:
        pass
        
print("Final cleanup complete!")

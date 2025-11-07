from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
STATUSES = {"planned", "reading", "completed", "dropped"}
@dataclass
class Book:
    id: str; title: str; authors: List[str]
    published_date: str = ""; page_count: int = 0
    categories: List[str] = None; thumbnail: str = ""
    added_at: str = ""; status: str = "planned"
    rating: Optional[int] = None; notes: str = ""
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self); d["authors"]=self.authors or []; d["categories"]=self.categories or []
        d["added_at"]= self.added_at or datetime.utcnow().isoformat(timespec="seconds")+"Z"
        if d.get("status") not in STATUSES: d["status"]="planned"
        if d.get("rating") is not None: d["rating"]=max(1,min(5,int(d["rating"])))
        return d

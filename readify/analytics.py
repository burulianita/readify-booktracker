# readify/analytics.py (A KORRIGÁLT stats függvény)

from collections import Counter
from typing import List, Dict, Any
import pandas as pd
from readify.models import STATUSES # Új: A teljes státusz lista importálása

def to_df(items: List[Dict[str, Any]]):
    # ... (a to_df függvényed kódja változatlan)
    if not items: return pd.DataFrame(columns=["id","title","authors","published_date","page_count","categories","status","rating","notes","added_at"])
    df=pd.DataFrame(items); df["authors"]=df["authors"].apply(lambda x: x if isinstance(x,list) else [])
    df["categories"]=df["categories"].apply(lambda x: x if isinstance(x,list) else [])
    df["page_count"]=pd.to_numeric(df.get("page_count",0), errors="coerce").fillna(0).astype(int); return df

def stats(items: List[Dict[str, Any]]):
    df = to_df(items)
    
    # 1. Statisztikák kiszámítása (Ahogy eddig is volt)
    total = len(df)
    pages_completed = int(df.loc[df["status"]=="completed", "page_count"].sum())
    auths = [a for row in df["authors"] for a in (row or [])]
    top = Counter(auths).most_common(5)

    # 2. Státuszok Inicializálása (Ahogy a szépítéshez kell):
    # Biztosítjuk, hogy minden státusz benne legyen, nullával is, a diagram miatt!
    by_status = {status: 0 for status in STATUSES}
    
    # 3. Értékek hozzáadása a meglévő adatokkal
    current_status_counts = df["status"].value_counts().to_dict()
    by_status.update(current_status_counts)
    
    # 4. Visszatérési érték (Megjegyzés: A by_status most már tartalmazza az összes státuszt!)
    return {
        "total": total,
        "by_status": by_status,
        "pages_completed": pages_completed,
        "top_authors": top
    }
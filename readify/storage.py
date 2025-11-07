import json, os
from typing import List, Dict, Any, Optional
from .models import Book
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "library.json")
def ensure_storage(path: str = DEFAULT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path,"w",encoding="utf-8") as f: json.dump([], f, ensure_ascii=False, indent=2)
def load_library(path: str = DEFAULT_PATH) -> List[Dict[str, Any]]:
    ensure_storage(path); 
    with open(path,"r",encoding="utf-8") as f: return json.load(f)
def save_library(data: List[Dict[str, Any]], path: str = DEFAULT_PATH):
    with open(path,"w",encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
def delete_book(book_id: str, path: str = DEFAULT_PATH):
    """Eltávolít egy könyvet az ID alapján a tárolóból."""
    data = load_library(path)
    new_data = [b for b in data if b.get("id") != book_id]
    
    # Ellenőrizzük, hogy történt-e törlés (a régi és az új lista mérete alapján)
    if len(new_data) < len(data):
        save_library(new_data, path)
        return True # Sikeres törlés
    return False # A könyv nem volt a listában
def get_by_id(book_id: str, path: str = DEFAULT_PATH) -> Optional[Dict[str, Any]]:
    for b in load_library(path):
        if b.get("id")==book_id: return b
    return None
def upsert_book(book: Book, path: str = DEFAULT_PATH):
    data = load_library(path)
    for i,b in enumerate(data):
        if b.get("id")==book.id:
            data[i]=book.to_dict(); save_library(data,path); return
    data.append(book.to_dict()); save_library(data,path)

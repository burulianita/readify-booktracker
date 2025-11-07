import os, requests
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
def search_books(q: str, max_results: int = 5):
    p={"q":q,"maxResults":max_results}; k=os.getenv("GOOGLE_BOOKS_API_KEY"); 
    p.update({"key":k} if k else {}); r=requests.get(GOOGLE_BOOKS_URL, params=p, timeout=15); r.raise_for_status()
    items=r.json().get("items",[]); out=[]
    for it in items:
        info=it.get("volumeInfo",{}); out.append({"id":it.get("id"),"title":info.get("title",""),
        "authors":info.get("authors",[]),"publishedDate":info.get("publishedDate",""),
        "pageCount":info.get("pageCount",0),"categories":info.get("categories",[]),
        "thumbnail":(info.get("imageLinks",{}) or {}).get("thumbnail","")})
    return out
def get_book(volume_id: str):
    p={}; k=os.getenv("GOOGLE_BOOKS_API_KEY"); p.update({"key":k} if k else {})
    r=requests.get(f"{GOOGLE_BOOKS_URL}/{volume_id}", params=p, timeout=15); r.raise_for_status()
    it=r.json(); info=it.get("volumeInfo",{})
    return {"id":it.get("id"),"title":info.get("title",""),"authors":info.get("authors",[]),
    "publishedDate":info.get("publishedDate",""),"pageCount":info.get("pageCount",0),
    "categories":info.get("categories",[]),"thumbnail":(info.get("imageLinks",{}) or {}).get("thumbnail","")}

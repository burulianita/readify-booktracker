import streamlit as st, pandas as pd
from readify.storage import load_library, upsert_book, delete_book, DEFAULT_PATH
from readify.api import search_books
from readify.models import Book, STATUSES
from readify.analytics import stats

# --- Alkalmazás Beállítások ---
st.set_page_config(page_title="Readify — Book Tracker", page_icon="📚", layout="wide")
st.title("📚 Readify — Book Tracker")

# --- Adatbázis Betöltése ---
db_path = DEFAULT_PATH
items = load_library(db_path)
df = pd.DataFrame(items)

# --- Oldalsáv: Keresés és Hozzáadás ---
with st.sidebar:
    st.header("Search & Add")
    q = st.text_input("Query (title/author/ISBN)", value="")
    max_results = st.slider("Max results", 1, 20, 5)

    if st.button("Search"):
        if q:
            try:
                st.session_state["search_results"] = search_books(q, max_results=max_results)
            except Exception as e:
                # Az 400-as hibát ez már elkapja, ha a kérés üres
                st.error(f"API error: {e}")
        else:
            st.warning("Please enter a title, author, or ISBN to search!")

    for r in st.session_state.get("search_results", []):
        with st.expander(f"{r['title']} — {', '.join(r.get('authors', []))}"):
            st.write(f"ID: `{r['id']}`")
            st.write(f"Published: {r.get('publishedDate','')} • Pages: {r.get('pageCount',0)}")
            
            if st.button(f"Add to library ({r['id']})", key=r["id"]):
                b = Book(
                    id=r["id"],
                    title=r["title"],
                    authors=r.get("authors", []),
                    published_date=r.get("publishedDate",""),
                    page_count=r.get("pageCount",0),
                    categories=r.get("categories", []),
                    thumbnail=r.get("thumbnail",""),
                    status="planned"
                )
                upsert_book(b, db_path)
                st.success(f"Added: {b.title}")
                st.rerun() # Újratöltés, hogy a könyv megjelenjen

# --- Könyvtár Megjelenítése és Szerkesztése ---
st.markdown("### Library")
with st.expander("🗑️ Delete a Book from Library"):
    book_titles = {item['id']: f"{item['title']} ({', '.join(item['authors'])})" for item in items}
    
    if not book_titles:
        st.info("The library is currently empty. Add a book first!")
    else:
        # Selectbox a törölni kívánt könyv kiválasztására
        book_to_delete_id = st.selectbox(
            "Select Book to Delete", 
            options=list(book_titles.keys()), 
            format_func=lambda x: book_titles[x]
        )
        
        # Törlés gomb megerősítéssel
        if st.button(f"Confirm Delete: {book_titles[book_to_delete_id]}", type="secondary"):
            if delete_book(book_to_delete_id, db_path):
                st.success(f"Book deleted: {book_titles[book_to_delete_id]}")
            else:
                st.error("Error: Book not found for deletion.")
            
            st.rerun() # Újratöltés a törlés után
status_filter = st.multiselect("Filter by status", options=list(STATUSES))
text_filter = st.text_input("Search in title/author", value="")
sort_by = st.selectbox("Sort by", options=["title","added_at","rating"])

df_display = df.copy()

if not df_display.empty:
    if status_filter: df_display = df_display[df_display["status"].isin(status_filter)]
    if text_filter:
        mask = df_display["title"].str.contains(text_filter, case=False, na=False) | df_display["authors"].apply(lambda a: any(text_filter.lower() in (x.lower()) for x in (a or [])))
        df_display = df_display[mask]
    
    if sort_by in df_display.columns: 
        # Rendezzük a megjelenítés előtt a DataFrame-et
        df_display = df_display.sort_values(sort_by, na_position="last")


    # --- A HELYESEN JAVÍTOTT st.data_editor blokk ---
    edited_df = st.data_editor(
        df_display,
        column_config={
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=list(STATUSES),
                required=True,
            ),
            "rating": st.column_config.NumberColumn(
                "Rating",
                min_value=1,
                max_value=5,
                step=1,
                format="%d ⭐"
            )
        },
        # Ezek az oszlopok nem szerkeszthetők
        disabled=("id", "title", "authors", "published_date", "categories", "thumbnail", "added_at"),
        use_container_width=True,
        hide_index=True,
        
        # A MÓDOSÍTOTT LOGIKA BEÁLLÍTÁSA A KEY ÉS on_change PARAMÉTEREKKEL
        on_change=lambda: st.session_state.update(
            {"last_edited_data": st.session_state[f"edited_table_state"]}
        ),
        key=f"edited_table_state",
    )


    # --- A HELYESEN JAVÍTOTT FRISSÍTÉSI LOGIKA A SESSION STATE ALAPJÁN ---
    if "last_edited_data" in st.session_state and st.session_state["last_edited_data"]["edited_rows"]:
        edited_data = st.session_state["last_edited_data"]
        
        for idx in edited_data["edited_rows"]:
            
            # Megkeressük a teljes sor adatát a MÓDOSÍTOTT DF-ben
            row_data = edited_df.loc[idx]
            
            # Frissítjük a módosított mezőket a Streamlit által küldött adatokkal
            updated_values = edited_data["edited_rows"][idx]
            
            # Létrehozunk egy Book objektumot a frissített adatokkal
            updated_book_data = row_data.to_dict()
            updated_book_data.update(updated_values) 
            
            updated_book = Book(**updated_book_data)
            
            # Frissítjük az adatbázisban (itt kell a storage.py-nak kezelnie az UPDATE-et!)
            upsert_book(updated_book, db_path)

        st.success("Library updated! Page refreshing...")
        
        # Töröljük a kulcsot, hogy a logika csak egyszer fusson le
        del st.session_state["last_edited_data"]
        
        st.rerun() # Újratöltjük az oldalt

# --- Statisztikák Megjelenítése ---
st.markdown("### Stats")
s = stats(items)
c1, c2, c3 = st.columns(3)
c1.metric("Total", s["total"])
c2.metric("Pages read", s["pages_completed"])
c3.metric("Reading", s["by_status"].get("reading", 0))

if s["by_status"]:
    # 1. Pandas DataFrame létrehozása (Status nevekkel indexelve)
    df_chart = pd.DataFrame.from_dict(s["by_status"], orient="index", columns=["count"])
    
    # 2. Index átalakítása oszloppá (a Streamlit bar_chart-nak ez kell)
    df_chart = df_chart.reset_index().rename(columns={'index': 'Status'})
    
    # 3. Diagram megjelenítése a megfelelő oszlopokkal
    st.bar_chart(
        df_chart, 
        x='Status', 
        y='count'
        # A Streamlit automatikusan szebb színpalettát használ
    )
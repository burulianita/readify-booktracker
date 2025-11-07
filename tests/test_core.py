from readify.analytics import stats
from readify.models import Book
from readify.storage import save_library, load_library
def test_stats(tmp_path):
    db = tmp_path / "library.json"
    data=[Book(id="1", title="A", authors=["X"], page_count=100, status="completed").to_dict(),
          Book(id="2", title="B", authors=["X","Y"], page_count=150, status="reading").to_dict(),
          Book(id="3", title="C", authors=["Z"], page_count=200, status="planned").to_dict()]
    save_library(data, str(db))
    s=stats(load_library(str(db)))
    assert s["total"]==3 and s["by_status"]["completed"]==1 and s["pages_completed"]==100

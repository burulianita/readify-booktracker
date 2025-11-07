import os, click
from tabulate import tabulate
from .api import search_books, get_book
from .models import Book, STATUSES
from .storage import DEFAULT_PATH, load_library, upsert_book, save_library, get_by_id
from .analytics import stats
def _info(m): click.secho(m, fg="green", bold=True)
def _warn(m): click.secho(m, fg="yellow", bold=True)
def _err(m): click.secho(m, fg="red", bold=True)
@click.group()
@click.option("--db", default=DEFAULT_PATH, help="Path to JSON storage.", show_default=True)
@click.pass_context
def cli(ctx, db): ctx.ensure_object(dict); ctx.obj["DB"]=db
@cli.command(help="Search books on Google Books API.")
@click.option("--q", required=True)
@click.option("--max", "max_results", default=5, show_default=True)
def search(q, max_results):
    try: results=search_books(q, max_results=max_results)
    except Exception as e: _err(f"API error: {e}"); return
    if not results: _warn("No results."); return
    rows=[[i, r["id"], r["title"], ", ".join(r["authors"]), r["publishedDate"]] for i,r in enumerate(results,1)]
    click.echo(tabulate(rows, headers=["#","volume_id","title","authors","year"], tablefmt="github"))
@cli.command(help="Add a book to your library by volume ID.")
@click.option("--id","volume_id", required=True)
@click.pass_context
def add(ctx, volume_id):
    try: r=get_book(volume_id)
    except Exception as e: _err(f"API error: {e}"); return
    b=Book(id=r["id"], title=r["title"], authors=r["authors"], published_date=r["publishedDate"],
           page_count=r["pageCount"] or 0, categories=r["categories"], thumbnail=r["thumbnail"], status="planned")
    upsert_book(b, path=ctx.obj["DB"]); _info(f"Added: {b.title}")
@cli.command(help="List books")
@click.option("--status", type=click.Choice(list(STATUSES)))
@click.option("--sort", type=click.Choice(["title","added"]), default="title", show_default=True)
@click.pass_context
def list(ctx, status, sort):
    items=load_library(ctx.obj["DB"])
    if status: items=[b for b in items if b.get("status")==status]
    if not items: click.echo("No books yet."); return
    items.sort(key=(lambda x: x.get("title","").lower()) if sort=="title" else (lambda x: x.get("added_at","")))
    rows=[[b["id"], b["title"], ", ".join(b.get("authors",[])), b.get("status",""), b.get("rating","")] for b in items]
    click.echo(tabulate(rows, headers=["id","title","authors","status","rating"], tablefmt="github"))
@cli.command(help="Update status/rating/notes by ID.")
@click.option("--id","book_id", required=True)
@click.option("--status", type=click.Choice(list(STATUSES)))
@click.option("--rating", type=int)
@click.option("--notes", type=str)
@click.pass_context
def update(ctx, book_id, status, rating, notes):
    item=get_by_id(book_id, path=ctx.obj["DB"])
    if not item: _err("Book not found."); return
    if status: item["status"]=status
    if rating is not None: item["rating"]=max(1,min(5,int(rating)))
    if notes is not None: item["notes"]=notes
    items=load_library(ctx.obj["DB"])
    for i,b in enumerate(items):
        if b.get("id")==book_id: items[i]=item; break
    save_library(items, ctx.obj["DB"]); _info("Updated.")
@cli.command(help="Stats")
@click.pass_context
def stats_cmd(ctx):
    s=stats(load_library(ctx.obj["DB"]))
    rows=[["total",s["total"]],["pages_completed",s["pages_completed"]]]
    click.echo(tabulate(rows, headers=["metric","value"], tablefmt="github"))
    if s["by_status"]: click.echo("\nBy status:"); click.echo(tabulate(list(s["by_status"].items()), headers=["status","count"], tablefmt="github"))
    if s["top_authors"]: click.echo("\nTop authors:"); click.echo(tabulate(s["top_authors"], headers=["author","count"], tablefmt="github"))
@cli.command(help="Export to CSV")
@click.option("--csv","csv_path", required=True)
@click.pass_context
def export(ctx, csv_path):
    import pandas as pd
    items=load_library(ctx.obj["DB"])
    if not items: _warn("Library empty."); return
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    pd.DataFrame(items).to_csv(csv_path, index=False, encoding="utf-8"); _info(f"Exported to {csv_path}")
if __name__=="__main__": cli()

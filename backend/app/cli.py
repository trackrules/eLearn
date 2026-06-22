import argparse
from .db import run_sql_file
from .crawler import crawl
from .search import rebuild_index
from .seed_components import seed
from .match_components import match

p = argparse.ArgumentParser()
p.add_argument("command", choices=["migrate", "crawl", "reindex", "seed-components", "match-components"])
args = p.parse_args()
if args.command == "migrate": print(run_sql_file("migrations/001_schema.sql") or {"migrated": True})
elif args.command == "crawl": print(crawl())
elif args.command == "reindex": print(rebuild_index())
elif args.command == "seed-components": print(seed())
elif args.command == "match-components": print(match())

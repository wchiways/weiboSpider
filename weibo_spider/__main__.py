import sys
from pathlib import Path

from absl import app
sys.path.append(str(Path.cwd().parent.absolute()))
from weibo_spider.spider import main

app.run(main)

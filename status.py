from db import AllFreeNovelsDB

with AllFreeNovelsDB('allfreenovels.db') as conn:
    print(conn.count_all_books())
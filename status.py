from db import AllFreeNovelsDB

with AllFreeNovelsDB('allfreenovels.db') as conn:
    total_books = conn.count_all_books()
    total_books_with_infos = conn.count_all_books_with_infos()
    print("TOTAL BOOKS ", total_books_with_infos)
    print("TOTAL WITH INFOS ", total_books_with_infos)
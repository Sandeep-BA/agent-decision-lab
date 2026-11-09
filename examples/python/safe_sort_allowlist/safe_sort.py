# Author: Sandeep Belgavi. Synthetic, application-owned sorting options.
SORTS = {"published": "published_on", "pages": "page_count", "title": "title"}
DIRECTIONS = {"asc": "ASC", "desc": "DESC"}


def list_books(connection, sort="published", direction="asc", minimum=0):
    if sort not in SORTS or direction not in DIRECTIONS:
        raise ValueError("unsupported sort option")
    sql = (
        "SELECT id, title, page_count FROM book WHERE id >= ? "
        f"ORDER BY {SORTS[sort]} {DIRECTIONS[direction]}, id ASC"
    )
    return connection.execute(sql, (minimum,)).fetchall()

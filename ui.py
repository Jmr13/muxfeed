import curses
import textwrap
import article

def launch_ui(entries):
    curses.wrapper(lambda stdscr: ui_loop(stdscr, entries))

def ui_loop(stdscr, entries):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    current_row = 0
    page_idx = 0
    reading_mode = False
    page_lines = []
    page_scroll = 0
    article_row = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # consistent entries per page
        min_entry_height = 4
        entries_per_page = max(1, (h - 1) // min_entry_height)

        if reading_mode:
            wrapped = []
            for line in page_lines:
                wrapped.extend(textwrap.wrap(line, w - 1) or [""])
        
            visible = wrapped[page_scroll:page_scroll + (h - 1)]
            for i, line in enumerate(visible):
                stdscr.addstr(i, 0, line)  # no highlighting
        
            stdscr.addstr(h - 1, 0, "↑/↓ scroll, 'b' back")

        else:
            start = page_idx * entries_per_page
            end = start + entries_per_page
            page_entries = entries[start:end]

            y = 0
            for idx, entry in enumerate(page_entries):
                actual_idx = start + idx

                source = entry.get("source", "")
                date = entry.get("date", "")
                header_line = f"{source} {date}".strip()

                raw_lines = [header_line]
                wrapped_title = textwrap.wrap(entry["title"], w - 10)
                raw_lines.extend(wrapped_title or [""])

                longest = max(len(l) for l in raw_lines) + 4
                min_width = int(w * 0.8)
                box_width = max(longest, min_width)
                box_width = min(box_width, w - 2)

                # top border
                if y < (h - 1):
                    line = "=" * box_width
                    x = (w - box_width) // 2
                    if actual_idx == current_row:
                        stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, x, line)
                    if actual_idx == current_row:
                        stdscr.attroff(curses.color_pair(1))
                    y += 1

                # content lines
                for text_line in raw_lines:
                    if y >= (h - 1):
                        break
                    content = f"{text_line}"
                    content = content.center(box_width)
                    x = (w - box_width) // 2
                    if actual_idx == current_row:
                        stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, x, content[:box_width])
                    if actual_idx == current_row:
                        stdscr.attroff(curses.color_pair(1))
                    y += 1

                # bottom border
                if y < (h - 1):
                    line = "=" * box_width
                    x = (w - box_width) // 2
                    if actual_idx == current_row:
                        stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, x, line)
                    if actual_idx == current_row:
                        stdscr.attroff(curses.color_pair(1))
                    y += 1

            total_pages = (len(entries) - 1) // entries_per_page + 1
            stdscr.addstr(
                h - 1,
                0,
                f"Page {page_idx + 1}/{total_pages} — ← prev, → next, ↑/↓ nav, Enter read, ESC quit",
            )

        stdscr.refresh()
        key = stdscr.getch()

        if reading_mode:
            if key == curses.KEY_UP and article_row > 0:
                article_row -= 1
                if article_row < page_scroll:
                    page_scroll -= 1
            elif key == curses.KEY_DOWN and article_row < len(wrapped) - 1:
                article_row += 1
                if article_row >= page_scroll + (h - 1):
                    page_scroll += 1
            elif key == ord('b'):
                reading_mode = False
                page_scroll = article_row = 0

        else:
            # ↑/↓ nav
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
                if current_row < page_idx * entries_per_page:
                    page_idx -= 1

            elif key == curses.KEY_DOWN and current_row < len(entries) - 1:
                current_row += 1
                if current_row >= (page_idx + 1) * entries_per_page:
                    page_idx += 1

            # ← prev page
            elif key == curses.KEY_LEFT:
                if page_idx > 0:
                    page_idx -= 1
                    current_row = max(current_row, page_idx * entries_per_page)
                    current_row = min(current_row, (page_idx + 1) * entries_per_page - 1)

            # → next page
            elif key == curses.KEY_RIGHT:
                if (page_idx + 1) * entries_per_page < len(entries):
                    page_idx += 1
                    current_row = max(current_row, page_idx * entries_per_page)
                    current_row = min(
                        current_row,
                        min(len(entries) - 1, (page_idx + 1) * entries_per_page - 1),
                    )

            elif key in (curses.KEY_ENTER, 10, 13):
                content = article.get_page_content(entries[current_row]["link"])
                page_lines = content.split("\n")
                reading_mode = True
                article_row = page_scroll = 0

            elif key == 27:  # ESC
                break
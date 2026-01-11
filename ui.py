import curses
import textwrap
import article


def launch_ui(entries):
    """Launch the curses-based UI."""
    curses.wrapper(lambda stdscr: ui_loop(stdscr, entries))


# --- Helper Functions ---
def safe_addstr(win, y, x, text, attr=0):
    """
    Safely add a string to a curses window without raising errors.
    Clips text if it overflows window boundaries.
    """
    max_y, max_x = win.getmaxyx()
    if 0 <= y < max_y:
        if x < 0:
            text = text[-x:]
            x = 0
        if x + len(text) > max_x:
            text = text[: max_x - x]
        try:
            win.addstr(y, x, text, attr)
        except curses.error:
            pass


def wrap_lines(lines, width):
    """
    Wrap a list of lines to fit within a given width.
    Ensures empty lines are preserved.
    """
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width) or [""])
    return wrapped


def draw_boxed_entry(win, y, box_width, lines, highlight=False):
    """
    Draw a centered box with content lines.
    
    Returns the next Y position after the box.
    """
    max_y, max_x = win.getmaxyx()
    x = max((max_x - box_width) // 2, 0)
    attr = curses.color_pair(1) if highlight else 0

    safe_addstr(win, y, x, "=" * box_width, attr)
    y += 1

    for line in lines:
        safe_addstr(win, y, x, line.center(box_width), attr)
        y += 1

    safe_addstr(win, y, x, "=" * box_width, attr)
    y += 1
    return y


# --- Main UI Loop ---
def ui_loop(stdscr, entries):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Highlight
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Info/Status

    current_row = 0
    page_idx = 0
    reading_mode = False
    page_lines = []
    article_row = 0
    page_scroll = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        entries_per_page = max(1, (max_y - 1) // 4)

        if reading_mode:
            # --- Display article content ---
            wrapped = wrap_lines(page_lines, max_x - 1)
            visible_height = max_y - 1

            # Center the scroll around the current article row
            half_screen = visible_height // 2
            page_scroll = max(0, article_row - half_screen)
            page_scroll = min(page_scroll, max(0, len(wrapped) - visible_height))
            visible_lines = wrapped[page_scroll:page_scroll + visible_height]

            for i, line in enumerate(visible_lines):
                safe_addstr(stdscr, i, 0, line)

            safe_addstr(stdscr, max_y - 1, 0, "↑/↓ scroll, 'b' back", curses.color_pair(2))

        else:
            # --- Display entry list ---
            start = page_idx * entries_per_page
            end = start + entries_per_page
            page_entries = entries[start:end]

            y = 0
            for idx, entry in enumerate(page_entries):
                actual_idx = start + idx
                header = f"{entry.get('source','')} {entry.get('date','')}".strip()
                lines = [header] + wrap_lines([entry["title"]], max_x - 10)

                box_width = min(max(max(len(l) for l in lines) + 4, int(max_x * 0.8)), max_x - 2)
                y = draw_boxed_entry(stdscr, y, box_width, lines, highlight=(actual_idx == current_row))
                if y >= max_y - 1:
                    break

            total_pages = (len(entries) - 1) // entries_per_page + 1
            status = f"Page {page_idx + 1}/{total_pages} — ← prev, → next, ↑/↓ nav, Enter read, ESC quit"
            safe_addstr(stdscr, max_y - 1, 0, status, curses.color_pair(2))

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_RESIZE:
            continue  # Window resized, redraw

        # --- Reading Mode Navigation ---
        if reading_mode:
            if key == curses.KEY_UP and article_row > 0:
                article_row -= 1
            elif key == curses.KEY_DOWN and article_row < len(wrapped) - 1:
                article_row += 1
            elif key == ord('b'):
                reading_mode = False
                article_row = page_scroll = 0

        # --- Entry List Navigation ---
        else:
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
                if current_row < page_idx * entries_per_page:
                    page_idx -= 1
            elif key == curses.KEY_DOWN and current_row < len(entries) - 1:
                current_row += 1
                if current_row >= (page_idx + 1) * entries_per_page:
                    page_idx += 1
            elif key == curses.KEY_LEFT and page_idx > 0:
                page_idx -= 1
                current_row = min(current_row, (page_idx + 1) * entries_per_page - 1)
            elif key == curses.KEY_RIGHT and (page_idx + 1) * entries_per_page < len(entries):
                page_idx += 1
                current_row = max(current_row, page_idx * entries_per_page)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Enter reading mode
                page_lines = article.get_page_content(entries[current_row]["link"]).split("\n")
                reading_mode = True
                article_row = page_scroll = 0
            elif key == 27:  # ESC
                break
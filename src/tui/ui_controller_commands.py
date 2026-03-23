from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self, controller, stdscr):
        raise NotImplementedError
    
class MoveDownCommand(Command):
    def execute(self, controller, stdscr):
        height, _ = stdscr.getmaxyx()
        controller.model.move_down(height - 2)

class MoveUpCommand(Command):
    def execute(self, controller, stdscr):
        controller.model.move_up()

class ScrollLeftCommand(Command):
    def execute(self, controller, stdscr):
        if controller.view_mode == "list":
            controller.model.scroll_title_left()
            controller.renderer.draw(stdscr, controller.model, controller.title_text)

class ScrollRightCommand(Command):
    def execute(self, controller, stdscr):
        if controller.view_mode == "list":
            _, width = stdscr.getmaxyx()
            controller.model.scroll_title_right(width)
            controller.renderer.draw(stdscr, controller.model, controller.title_text)

class ShowDetailsCommand(Command):
    def execute(self, controller, stdscr):
        entry = controller.model.get_selected_entry()
        if entry:
            controller.view_mode = "details"
            controller.renderer.draw_details(stdscr, entry)

class QuitCommand(Command):
    def execute(self, controller, stdscr):
        controller.running = False  
        
class ScrollDownCommand(Command):
    def execute(self, controller, stdscr):
        details = controller.renderer.current_details
        if details:
            height, width = stdscr.getmaxyx()
            total_lines = len(details.lines)

            visible_lines = height - 2
            
            if details.start_line + visible_lines < total_lines:
                details.start_line += 1
                details.draw(stdscr, height, width)

class ScrollUpCommand(Command):
    def execute(self, controller, stdscr):
        details = controller.renderer.current_details
        if details and details.start_line > 0:
            details.start_line -= 1
            height, width = stdscr.getmaxyx()
            details.draw(stdscr, height, width)

class QuitDetailsCommand(Command):
    def execute(self, controller, stdscr):
        if controller.view_mode == "details":
            controller.view_mode = "list"
            controller.renderer.current_details = None
            controller.renderer.draw(stdscr, controller.model, controller.title_text)
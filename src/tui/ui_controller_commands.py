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
            height, _ = stdscr.getmaxyx()
            total_lines = len(details.lines)
            if details.start_line + height - 1 < total_lines:
                details.start_line += 1
                details.draw(stdscr, height, _)

class ScrollUpCommand(Command):
    def execute(self, controller, stdscr):
        details = controller.renderer.current_details
        if details and details.start_line > 0:
            details.start_line -= 1
            height, _ = stdscr.getmaxyx()
            details.draw(stdscr, height, _)

class QuitDetailsCommand(Command):
    def execute(self, controller, stdscr):
        if controller.view_mode == "details":
            controller.view_mode = "list"
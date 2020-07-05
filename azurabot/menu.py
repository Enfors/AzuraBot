"""AzuraBot's menu system.
"""

from typing import List

sample_todo_menu_items = (
    ("List todos", "list_todos"),
    ("View todo",
     ("Edit", "edit_todo"),
     ("Delete", "delete_todo"),
     ("Complete", "complete_todo"),
     ),
    ("Add todo", "add_todo")
)


class Menu:

    def __init__(self, name: str, items: List = ()):
        self.name = name
        self.items = items

    def enter(self):
        self._enter_section(self.items)

    def _enter_section(self, cur_items):
        self._display(self._format_section(cur_items))
        choice = -1
        while not (-1 < choice < len(cur_items) + 1):
            choice = int(input("Choose> "))

        if choice == 0:
            return

        print(type(cur_items[choice - 1][1]))
        if isinstance(cur_items[choice - 1][1], tuple):
            print(f"Going into submenu {cur_items[choice-1][1][0]}")
            self._enter_section(cur_items[choice - 1][1])
        else:
            self._display(f"You have chosen item {cur_items[choice-1][0]}")

    def _display(self, text: str):
        print(text)

    def __str__(self):
        if not self.items:
            return f"(The menu {self.name} is empty)"
        return self.name + "\n" + self._format_section(self.items)

    def _format_section(self, items):
        disp = ""

        for char in self.name:
            disp += "="
        disp += "\n"

        for num, item in enumerate(self.items, 1):
            disp += f"{num}) {item[0]}\n"
        disp += "0) Go back\n"
        return disp


if __name__ == "__main__":
    menu = Menu("Todo menu", sample_todo_menu_items)
    menu.enter()

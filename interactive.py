import questionary
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.styles import Style
from design import print_narrative, print_error, EMOJI_LAB, EMOJI_FILE, EMOJI_PIN, EMOJI_INFO, EMOJI_LIGHTNING

def main_menu():
    """Display an arrow-key navigable menu with emojis."""
    print_narrative(f"{EMOJI_LAB} The laboratory awaits your command...", style="bold cyan")
    try:
        choice = questionary.select(
            "What experiment shall we run?",
            choices=[
                f"{EMOJI_LIGHTNING} Send Experiment",
                f"{EMOJI_LIGHTNING} Receive Experiment",
                f"{EMOJI_INFO} System Inspection",
                f"{EMOJI_LIGHTNING} Exit Laboratory"
            ],
            style=questionary.Style([
                ('selected', 'fg:ansigreen bold'),
                ('pointer', 'fg:ansibrightred bold'),
            ])
        ).ask()
    except KeyboardInterrupt:
        print_narrative("The experiment was interrupted. Returning to shadows.", style="bold red")
        return "exit"
    except Exception as e:
        print_error(f"Menu malfunction: {e}", "Check your terminal or restart the lab.")
        return "exit"

    if choice is None:  # User pressed Ctrl+C
        return "exit"
    # Map friendly names to internal modes
    mapping = {
        f"{EMOJI_LIGHTNING} Send Experiment": "send",
        f"{EMOJI_LIGHTNING} Receive Experiment": "receive",
        f"{EMOJI_INFO} System Inspection": "sysinfo",
        f"{EMOJI_LIGHTNING} Exit Laboratory": "exit"
    }
    return mapping[choice]

def get_file_paths():
    """Prompt for file/folder paths with tab autocomplete."""
    print_narrative(f"{EMOJI_FILE} Select the specimen to transmit...", style="bold cyan")
    print_narrative(f"(Type path with <TAB> completion, then press Enter. Leave empty to start experiment.)", style="dim")

    paths = []
    session = PromptSession(completer=PathCompleter(), style=Style.from_dict({
        'prompt': 'ansicyan',
    }))

    while True:
        try:
            path = session.prompt("Path: ")
        except KeyboardInterrupt:
            print_narrative("Path selection cancelled.", style="bold red")
            return []
        except Exception as e:
            print_error(f"Path input error: {e}")
            continue

        if not path.strip():
            if paths:
                break
            else:
                print_error("No path entered. Please provide at least one file or folder.")
                continue
        paths.append(path.strip())
        print_narrative(f"Added: {path}", style="green")
    return paths

def get_pin():
    """Prompt for the 6-digit PIN."""
    print_narrative(f"{EMOJI_PIN} Enter the secret formula (6-digit PIN):", style="bold cyan")
    try:
        pin = questionary.text("PIN", validate=lambda text: len(text) == 6 and text.isdigit()).ask()
    except KeyboardInterrupt:
        print_narrative("PIN entry cancelled.", style="bold red")
        raise
    except Exception as e:
        print_error(f"PIN input error: {e}", "Try again or restart the lab.")
        raise
    if pin is None:
        raise KeyboardInterrupt
    return pin
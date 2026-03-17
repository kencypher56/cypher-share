#!/usr/bin/env python3
from design import show_banner, animate_sparks, print_narrative, print_error
import interactive
import sysinfo
import send
import receive
import sys
import traceback

def main():
    try:
        show_banner()
        animate_sparks()
        print_narrative("The laboratory is ready. What brings you here tonight?", style="bold bright_red")

        while True:
            mode = interactive.main_menu()
            if mode == "exit":
                print_narrative("Goodbye, creator. Until next experiment.", style="bold magenta")
                sys.exit(0)
            elif mode == "sysinfo":
                try:
                    sysinfo.display_system_info()
                except Exception as e:
                    print_error(f"System inspection failed: {e}", "Perhaps the machine is asleep.")
            elif mode == "send":
                paths = interactive.get_file_paths()
                if paths:
                    try:
                        send.start_sender(paths)
                    except Exception as e:
                        print_error(f"Sending experiment failed: {e}", "Check the network and try again.")
                else:
                    print_narrative("No files selected. Returning to main lab.", style="yellow")
            elif mode == "receive":
                try:
                    pin = interactive.get_pin()
                except KeyboardInterrupt:
                    print_narrative("PIN entry cancelled.", style="bold red")
                    continue
                except Exception:
                    continue
                try:
                    receive.start_receiver(pin)
                except Exception as e:
                    print_error(f"Receiving experiment failed: {e}", "Is the sender alive?")
    except KeyboardInterrupt:
        print_narrative("\n[⚡] The experiment was interrupted. The creature returns to the shadows.", style="bold red")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        if False:
            traceback.print_exc()
        print_narrative("The laboratory is unstable. Please check your setup.", style="bold red")
        sys.exit(1)

if __name__ == "__main__":
    main()
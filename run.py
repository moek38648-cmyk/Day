#!/usr/bin/env python3
import Code_Cyber

if __name__ == "__main__":
    try:
        Code_Cyber.main()
    except KeyboardInterrupt:
        Code_Cyber.stop_event.set()
        print(f"\n{Code_Cyber.RED}Turbo Engine Shutdown...{Code_Cyber.RESET}")

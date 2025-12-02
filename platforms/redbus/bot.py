# main.py
import sys
import time
from ui.choose_profile import ChromeProfileChooser
from ui.main_window import MainWindow
from core.driver_manager import get_driver_for_profile
from platforms.redbus.bot import RedBusBot

def main():
    print("--- CTRL+ALT+TICKET Automation Bot ---")

    # Step 1: Choose Chrome profile
    chooser = ChromeProfileChooser()
    user_data_dir, profile = chooser.run()

    if not user_data_dir or not profile:
        print("No profile selected or selection cancelled. Exiting.")
        return

    print(f"\nLaunching Chrome with profile path: {user_data_dir}  profile-directory: {profile}\n")

    # Step 2: Create driver (NO HEADLESS ARG HERE)
    try:
        driver = get_driver_for_profile(user_data_dir, profile)
    except FileNotFoundError as e:
        print("ERROR: The provided user-data directory does not exist.")
        print(e)
        return
    except RuntimeError as e:
        print("------------------------------------------------------------------------------------------------")
        print("CRITICAL ERROR: Failed to create Selenium session.")
        print("Error Details:", e)
        print("COMMON RESOLUTION STEPS (Check these carefully):")
        print("1. Ensure ALL Chrome processes are fully closed (Task Manager -> end chrome.exe).")
        print("2. Do NOT use the 'Default' profile. Use a secondary profile (create 'CTRL-ALT-PROFILE').")
        print("3. Update Chrome and webdriver-manager.")
        print("4. Run terminal as Administrator.")
        print("5. Restart the PC if profile remains locked.")
        print("------------------------------------------------------------------------------------------------")
        return
    except Exception as e:
        print("Unexpected error while creating driver:", e)
        return

    print("Chrome launched successfully. Starting RedBus bot...")

    # Step 3: Run bot
    try:
        bot = RedBusBot(driver)
        bot.open_site()
        bot.ensure_login()

        # example search
        src = "Mumbai"
        dst = "Pune"
        date_str = "12-Feb-2025"

        bot.search_buses(src, dst, date_str)
        bot.open_first_bus()

        print("Bot finished actions. Browser kept open for user interaction.")
    except Exception as e:
        print("Error during automation:", e)

    # NOTE: do NOT close driver — user needs it open for payment
    # driver.quit()

if __name__ == "__main__":
    main()

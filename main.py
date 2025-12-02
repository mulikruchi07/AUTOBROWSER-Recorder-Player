# main.py
from ui.main_window import MainWindow
from core.driver_manager import get_driver_with_temp_profile
from platforms.redbus.bot import RedBusBot

def main():
    print("--- CTRL+ALT+TICKET Automation Bot ---")

    # Always use fresh Chrome profile
    driver = get_driver_with_temp_profile()

    # UI
    mw = MainWindow()
    choice = mw.run()

    if choice == "redbus":
        bot = RedBusBot(driver)
        bot.open_site()
        bot.ensure_login()
        bot.search_buses("Mumbai", "Pune", "12-Feb-2025")
        bot.open_first_bus()

        print("Automation complete. Browser left open.")

if __name__ == "__main__":
    main()

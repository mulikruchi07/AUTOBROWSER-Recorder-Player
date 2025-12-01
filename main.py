from ui.choose_profile import ChromeProfileChooser
from ui.main_window import MainWindow
from core.driver_manager import get_driver_using_profile
from platforms.redbus.bot import RedBusBot

def main():
    # Step 1 — Select Chrome Profile
    profile = ChromeProfileChooser().run()
    if not profile:
        print("No profile selected.")
        return

    # Step 2 — Choose platform
    chosen = MainWindow().run()
    if chosen != "redbus":
        print("Only RedBus supported right now.")
        return

    # Step 3 — Create driver
    driver = get_driver_using_profile(profile)

    # Step 4 — Start RedBus bot
    bot = RedBusBot(driver)
    bot.open_site()
    bot.ensure_login()

    # Example test search
    bot.search_buses("Mumbai", "Pune", "12-Feb-2025")
    bot.open_first_bus()

    print("Bot completed. Browser left open for user.")
    # driver.quit()   # optional

if __name__ == "__main__":
    main()

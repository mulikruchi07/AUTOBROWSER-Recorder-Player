from core.driver_manager import get_driver
from ui.main_window import MainWindow
from platforms.example_site.bot import ExampleBot

def main():
    # available platform keys must match your platforms folder names
    platforms = ["example_site"]
    platform, profile = MainWindow(platforms).run()
    if not platform:
        print("No platform selected. Exiting.")
        return

    driver = get_driver(use_profile=True, profile_name=profile, headless=False)
    bot = None

    try:
        if platform == "example_site":
            bot = ExampleBot(driver)
            bot.open_site()
            logged = bot.ensure_login()
            if not logged:
                print("Login failed or cancelled.")
                return
            # example query (in a real GUI you'd accept user inputs)
            bot.search_and_open("test product")
            print("Reached product page. User should continue payment manually.")
    finally:
        # don't close immediately so user can complete payment in profile browser
        print("Bot finished. Browser left open for user to complete actions.")
        # driver.quit()  # optional - keep browser open for user to pay

if __name__ == "__main__":
    main()

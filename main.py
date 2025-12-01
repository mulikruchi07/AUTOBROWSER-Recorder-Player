from ui.choose_profile import ChromeProfileChooser
from ui.main_window import MainWindow
from core.driver_manager import get_driver_using_profile
# Import the new Platform Manager
from core.platform_manager import PlatformManager 
# Removed: from platforms.redbus.bot import RedBusBot

def main():
    # Step 1 — Select Chrome Profile
    profile = ChromeProfileChooser().run()
    if not profile:
        print("No profile selected. Exiting.")
        return

    # Step 2 — Choose platform
    chosen_platform = MainWindow().run()
    if not chosen_platform:
        print("No platform selected. Exiting.")
        return
    
    # Step 3 — Create driver
    driver = get_driver_using_profile(profile)
    
    # Step 4 — Start the chosen bot dynamically
    bot = PlatformManager.get_bot(chosen_platform, driver)
    
    if bot:
        print(f"Starting {chosen_platform} bot...")
        bot.open_site()
        # The bot handles session login check and user login UI
        bot.ensure_login() 
        
        # --- EXECUTION LOGIC: Needs to be generalized/moved later ---
        if chosen_platform == "redbus":
            # Example test search (Hardcoded for now)
            # Future step: Add a Tkinter UI to get these details
            print("Executing RedBus search...")
            bot.search_buses("Mumbai", "Pune", "12-Feb-2025")
            bot.open_first_bus()
        elif chosen_platform == "example_site":
            print("Executing ExampleSite search...")
            bot.search_and_open("Laptop")
        # ------------------------------------------------------------
        
        print("Bot completed. Browser left open for user.")
    else:
        print(f"Failed to load bot for platform: {chosen_platform}. Exiting.")
        
    # driver.quit()   # optional

if __name__ == "__main__":
    main()
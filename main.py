from ui.choose_profile import ChromeProfileChooser
from ui.main_window import MainWindow
from core.driver_manager import get_driver_using_profile
from core.platform_manager import PlatformManager 
from platforms.example_site import locators as example_locators 

def main():
    print("--- CTRL+ALT+TICKET Automation Bot ---")
    
    # Step 1 — Select Chrome Profile
    profile_path = ChromeProfileChooser().run()
    if not profile_path:
        print("No profile selected or profile detection failed. Exiting.")
        return # Graceful exit if UI returns None

    # Step 2 — Choose platform
    chosen_platform = MainWindow().run()
    if not chosen_platform:
        print("No platform selected. Exiting.")
        return
    
    # Step 3 — Create driver
    print(f"Launching Chrome with profile path: {profile_path}")
    driver = None
    try:
        driver = get_driver_using_profile(profile_path)
    except Exception as e:
        # get_driver_using_profile already prints the critical error message
        print(f"Driver initialization failed. Cannot continue.")
        return
    
    # Step 4 — Start the chosen bot dynamically
    bot = PlatformManager.get_bot(chosen_platform, driver)
    
    if bot:
        print(f"Starting {chosen_platform} bot...")
        
        try:
            bot.open_site()
            
            # The bot handles session login check and user login UI/manual steps
            if not bot.ensure_login():
                print("Login failed or cancelled. Terminating bot flow.")
                driver.quit()
                return

            # --- EXECUTION LOGIC: Needs to be generalized/moved later ---
            if chosen_platform == "redbus":
                # Example test search 
                print("Executing RedBus search flow...")
                bot.search_buses("Mumbai", "Pune", "25-Dec-2025") 
                bot.open_first_bus()
                
            elif chosen_platform == "example_site":
                # Example flow for the placeholder site (GitHub)
                print("Executing Example Site search flow...")
                bot.search_and_open("selenium python bot")

            # ------------------------------------------------------------
            
            print("Bot execution completed. Browser left open for inspection.")
            
        except Exception as e:
            print(f"An unexpected error occurred during bot execution: {e}")
            if driver:
                driver.quit()
            
    else:
        print(f"Failed to load bot for platform: {chosen_platform}. Exiting.")
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
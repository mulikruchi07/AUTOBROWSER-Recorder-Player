from ui.choose_profile import ChromeProfileChooser
from ui.main_window import MainWindow
from ui.search_input_window import SearchInputWindow
from core.driver_manager import get_driver_using_profile
from core.platform_manager import PlatformManager 
from platforms.example_site import locators as example_locators 
# Removed: import os

def main():
    print("--- CTRL+ALT+TICKET Automation Bot ---")
    
    # Step 1 — Select Chrome Profile
    profile_path = ChromeProfileChooser().run()
    if not profile_path:
        print("No profile selected or profile detection failed. Exiting.")
        return 

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
        
        # Broader try-except block to catch navigation/login failure
        try:
            # THIS IS WHERE NAVIGATION HAPPENS
            bot.open_site()
            
            # The bot handles session login check and user login UI/manual steps
            if not bot.ensure_login():
                print("Login failed or cancelled. Terminating bot flow.")
                driver.quit()
                return

            # --- EXECUTION LOGIC: Collect user inputs and run bot flow ---
            if chosen_platform == "redbus":
                # Collect search parameters from the new UI
                src, dst, date = SearchInputWindow().run()
                
                if src and dst and date:
                    print("Executing RedBus search flow with user inputs...")
                    bot.search_buses(src, dst, date) 
                    bot.open_first_bus()
                else:
                    print("RedBus search cancelled or incomplete details provided. Terminating flow.")
                
            elif chosen_platform == "example_site":
                # Example flow for the placeholder site (GitHub)
                print("Executing Example Site search flow...")
                bot.search_and_open("selenium python bot")

            # ------------------------------------------------------------
            
            print("Bot execution completed. Browser left open for inspection.")
            
        except Exception as e:
            # Catch failures that happen after driver initialization (e.g., navigation failure)
            print("------------------------------------------------------------------------------------------------")
            print(f"FATAL BOT EXECUTION ERROR:")
            print(f"The program failed during navigation or login after the browser opened.")
            print(f"Details: {type(e).__name__}: {e}")
            print("------------------------------------------------------------------------------------------------")
            if driver:
                driver.quit()
            
    else:
        print(f"Failed to load bot for platform: {chosen_platform}. Exiting.")
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
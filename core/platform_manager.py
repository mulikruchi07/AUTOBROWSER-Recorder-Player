import importlib

class PlatformManager:
    @staticmethod
    def get_bot(platform_name: str, driver):
        """
        Dynamically imports and returns the bot instance for the given platform.
        Expects a structure like 'platforms/{platform_name}/bot.py'
        with a class named '{PlatformNameCapitalized}Bot'.
        
        Example: 'redbus' -> 'RedBusBot'
        """
        try:
            # Convert platform_name (e.g., 'redbus', 'example_site') 
            # into the expected ClassName (e.g., 'RedBusBot', 'ExampleSiteBot')
            class_name_parts = [part.capitalize() for part in platform_name.split('_')]
            class_name = "".join(class_name_parts) + "Bot"

            # Import the module: e.g., platforms.redbus.bot
            module = importlib.import_module(f"platforms.{platform_name}.bot")

            # Get the class from the module
            BotClass = getattr(module, class_name)

            # Instantiate and return the bot
            return BotClass(driver)

        except ImportError as e:
            print(f"Error: Could not import bot for platform '{platform_name}'.")
            print(f"Make sure you have a folder: platforms/{platform_name}/bot.py")
            print(f"Details: {e}")
            return None
        except AttributeError as e:
            print(f"Error: Could not find class '{class_name}' in the bot module.")
            print(f"Make sure the class is named correctly: '{class_name}'")
            print(f"Details: {e}")
            return None
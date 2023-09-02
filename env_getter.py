import uio
from phew import logging

# Open and read the .env file
with uio.open(".env", "r") as f:
    env_contents = f.read()

# Split the content into lines
env_lines = env_contents.splitlines()

# Create a dictionary to store environment variables
env_vars = {}
for line in env_lines:
    # Split at the first occurrence of "="
    parts = line.split("=", 1)
    key = parts[0].strip()  # Remove leading and trailing spaces from key
    value = "=".join(parts[1:]).strip()  # Remove leading and trailing spaces from value
    env_vars[key] = value


# Function that is called by other files to get environment variables
def get_env(key):

    try:
        env_var = env_vars.get(key)
        if env_var is not None:
            # Use the API key in your code
            return env_var
        else:
            print("API Key not found.")
            # If the API key is not found throw an exception
            raise Exception("API Key not found.")

    except Exception as e:
        logging.error("> In env_getter.py Issue getting environment variables.", e)
   

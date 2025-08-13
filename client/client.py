import asyncio
import sys
import aiohttp
import configparser
import os

async def main():
    """
    Main function to run the terminal client.
    """
    # Read configuration
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.ini')
    config.read(config_path)
    
    host = config.get('server', 'host', fallback='127.0.0.1')
    port = config.getint('server', 'port', fallback=5000)
    server_url = f"http://{host}:{port}/query"

    async with aiohttp.ClientSession() as session:
        print(f"Client is ready. Enter your query or 'exit' to quit. (Connecting to {server_url})")
        while True:
            try:
                query = await asyncio.to_thread(input, "Query: ")
                if query.lower() == 'exit':
                    break

                payload = {'text': query}
                async with session.post(server_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("Answer:", result.get('text'))
                    else:
                        print(f"Error: Server returned status {response.status}", file=sys.stderr)

            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break
            except Exception as e:
                print(f"An error occurred: {e}", file=sys.stderr)
                break

if __name__ == "__main__":
    asyncio.run(main())
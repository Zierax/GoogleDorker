import argparse
from googlesearch import search
import sys
import time
import requests

class Colors:
    RED = "\33[91m"
    BLUE = "\33[94m"
    RESET = "\033[0m"

def print_colored(text, color, end="\n", delay=0.0):
    """Prints text in a given color with an optional delay between each character."""
    for char in text:
        print(color + char + Colors.RESET, end="", flush=True)
        time.sleep(delay)
    print(end=end)

def save_to_file(data, filename):
    """Saves the provided data to a specified file."""
    with open(f"{filename}.txt", "a") as file:
        file.write(data + "\n")

def google_dork_search(args):
    """Main function to perform Google Dork search based on the provided arguments."""
    print_colored("Google Dork Finder v2.0", Colors.RED, delay=0.002)

    dorks = []
    if args.dork:
        dorks.append(args.dork)
    if args.dorks_file:
        with open(args.dorks_file, 'r') as file:
            dorks.extend(file.read().splitlines())

    if not dorks:
        print_colored("[!] No dork query provided.", Colors.RED)
        sys.exit(1)

    if args.save:
        filename = args.save
        print("\n" + "  " + "»" * 78 + "\n")
    else:
        filename = None
        print("[!] Saving is skipped...")
        print("\n" + "  " + "»" * 78 + "\n")

    try:
        for dork in dorks:
            if args.domain:
                dork += f" site:{args.domain}"

            print_colored(f"[+] Searching for: {dork}", Colors.BLUE)
            for idx, result in enumerate(search(dork, num=args.number, stop=args.number, pause=2), start=1):
                output = f"[+] {idx}. {result}"
                print(output)
                if filename:
                    save_to_file(output, filename)
                if args.verbose:
                    print(f"[*] Verbose: Retrieved {result}")
                time.sleep(0.1)  # To avoid rate limiting

    except KeyboardInterrupt:
        print_colored("\n[!] User interruption detected.", Colors.RED)
    except Exception as e:
        print_colored(f"\n[!] Error: {str(e)}", Colors.RED)
    finally:
        print("[•] Done. Exiting...")
        sys.exit()

def main():
    parser = argparse.ArgumentParser(description="Google Dork Finder")
    parser.add_argument("--dork", type=str, help="Google dork query to search")
    parser.add_argument("--dorks_file", type=str, help="File containing multiple dork queries")
    parser.add_argument("--domain", type=str, help="Specific domain to search within")
    parser.add_argument("--number", type=int, default=10, help="Number of search results to display")
    parser.add_argument("--save", type=str, help="File name to save the results")
    parser.add_argument("--proxy", type=str, help="Proxy server to use (format: http://user:pass@host:port)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")

    args = parser.parse_args()

    # If a proxy is provided, set up the requests module to use it
    if args.proxy:
        print(f"[+] Using proxy: {args.proxy}")
        proxies = {
            "http": args.proxy,
            "https": args.proxy
        }
        # Check if proxy is valid (optional)
        try:
            response = requests.get("http://www.google.com", proxies=proxies, timeout=10)
            if response.status_code == 200:
                print("[+] Proxy is working")
            else:
                print(f"[!] Proxy returned status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print_colored(f"[!] Proxy error: {str(e)}", Colors.RED)
            sys.exit(1)

    google_dork_search(args)

if __name__ == "__main__":
    main()

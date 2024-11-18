import argparse
import sys
import time
import requests
import random
import os
import json
import csv
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from termcolor import colored
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from urllib.parse import quote_plus
from typing import List, Dict, Any, Tuple, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from anticaptchaofficial.imagecaptcha import imagecaptcha
import http.cookiejar
import socket
from stem import Signal
from stem.control import Controller
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

class Colors:
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"

def print_colored(text: str, color: str, end: str = "\n", delay: float = 0.0) -> None:
    """Prints text in a given color with an optional delay between each character."""
    try:
        for char in text:
            console.print(char, style=color, end="")
            time.sleep(delay)
        console.print(end=end)
    except Exception as e:
        logger.error(f"Error in print_colored: {str(e)}")

def save_to_file(data: str, filename: str) -> None:
    """Saves the provided data to a specified file."""
    try:
        with open(f"{filename}.txt", "a") as file:
            file.write(data + "\n")
        console.print(f"[bold green]Data saved to {filename}.txt[/bold green]")
    except IOError as e:
        console.print(f"[bold red]Error saving to file {filename}: {str(e)}[/bold red]")

def load_user_agents() -> List[str]:
    """Load a list of user agents using fake_useragent library."""
    try:
        ua = UserAgent()
        return [ua.random for _ in range(100)]
    except Exception as e:
        console.print(f"[bold red]Error loading user agents: {str(e)}[/bold red]")
        return []

def get_random_user_agent(user_agents: List[str]) -> str:
    """Return a random user agent from the list."""
    return random.choice(user_agents) if user_agents else ""

def check_url(url: str, timeout: int = 5, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Check if a URL is accessible and return additional information."""
    result = {'url': url, 'status': None, 'title': 'Unreachable', 'server': 'Unknown', 'content_type': 'Unknown'}
    try:
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        result.update({
            'status': response.status_code,
            'title': soup.title.string if soup.title else "No title",
            'server': response.headers.get('Server', 'Unknown'),
            'content_type': response.headers.get('Content-Type', 'Unknown')
        })
    except Timeout:
        console.print(f"[yellow]Timeout occurred while checking {url}[/yellow]")
    except ConnectionError:
        console.print(f"[yellow]Connection error occurred while checking {url}[/yellow]")
    except RequestException as e:
        console.print(f"[bold red]Error checking {url}: {str(e)}[/bold red]")
    return result

def bypass_waf(dork: str) -> Tuple[str, Dict[str, str]]:
    """Apply techniques to bypass WAF."""
    try:
        dork += f"&cb={random.randint(1, 1000000)}"
        dork = quote_plus(dork)
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        return dork, headers
    except Exception as e:
        console.print(f"[bold red]Error in bypass_waf: {str(e)}[/bold red]")
        return dork, {}

def bypass_recaptcha(driver, site_key: str, url: str, anti_captcha_api_key: str) -> str:
    """Bypass reCAPTCHA using various techniques."""
    try:
        # Method 1: Use undetected_chromedriver
        options = uc.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = uc.Chrome(options=options)
        driver.get(url)
        
        # Method 2: Use anti-captcha service
        solver = recaptchaV2Proxyless()
        solver.set_verbose(1)
        solver.set_key(anti_captcha_api_key)
        solver.set_website_url(url)
        solver.set_website_key(site_key)
        
        g_response = solver.solve_and_return_solution()
        if g_response != 0:
            console.print(f"[green]g-response: {g_response}[/green]")
        else:
            console.print(f"[yellow]Task finished with error {solver.error_code}[/yellow]")
        
        # Method 3: Delay and random actions
        time.sleep(random.uniform(2, 5))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 3))
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
        time.sleep(random.uniform(2, 4))
        
        # Method 4: Simulate human-like behavior
        actions = webdriver.ActionChains(driver)
        recaptcha_box = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border")
        actions.move_to_element(recaptcha_box).pause(random.uniform(0.5, 1.5)).click().perform()
        
        return g_response
    except Exception as e:
        console.print(f"[bold red]Error in bypass_recaptcha: {str(e)}[/bold red]")
        return ""

def perform_search(dork: str, args: argparse.Namespace, user_agents: List[str]) -> List[str]:
    """Perform the search for a given dork."""
    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_url = {executor.submit(search_with_rotation, dork, args.number, user_agents): dork}
            for future in as_completed(future_to_url):
                try:
                    results.extend(future.result())
                except Exception as e:
                    console.print(f"[bold red]Error in search: {str(e)}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error in perform_search: {str(e)}[/bold red]")
    return results

def search_with_rotation(dork: str, num_results: int, user_agents: List[str]) -> List[str]:
    """Perform search with rotation of user agents using requests."""
    results = []
    session = requests.Session()
    base_url = "https://www.google.com/search"
    start = 0  # Pagination starts at 0 for Google
    
    while len(results) < num_results:
        try:
            # Rotate user agent
            session.headers.update({'User-Agent': get_random_user_agent(user_agents)})
            
            # Perform search
            params = {
                'q': dork,
                'start': start,
                'num': 10,  # Number of results per page
                'hl': 'en'  # Language
            }
            response = session.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            for a_tag in soup.select('a[href^="/url?q="]'):
                href = a_tag.get('href')
                url = re.search(r'/url\?q=(.*?)&', href)
                if url:
                    decoded_url = url.group(1)
                    if decoded_url not in results:
                        results.append(decoded_url)
                        if len(results) >= num_results:
                            break

            # Move to the next page
            start += 10
            
            # Add delay between requests to avoid detection
            time.sleep(random.uniform(1, 3))
            
        except RequestException as e:
            console.print(f"[yellow]Error in search_with_rotation: {str(e)}[/yellow]")
            time.sleep(5)  # Wait longer if an error occurs

    return results[:num_results]

def check_urls(urls: List[str], args: argparse.Namespace, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Check the URLs and return the results."""
    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_url = {executor.submit(check_url, url, args.timeout, headers): url for url in urls}
            for future in as_completed(future_to_url):
                try:
                    results.append(future.result())
                except Exception as e:
                    console.print(f"[bold red]Error checking URL: {str(e)}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error in check_urls: {str(e)}[/bold red]")
    return results

def google_dork_search(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Perform Google Dork search based on the provided arguments."""
    console.print(Panel.fit("[bold red]Google Dork Finder v2.0[/bold red]", border_style="bold"))

    dorks = [args.dork] if args.dork else []
    if args.dorks_file:
        try:
            with open(args.dorks_file, 'r') as file:
                dorks.extend(file.read().splitlines())
        except IOError as e:
            console.print(f"[bold red]Error reading dorks file: {str(e)}[/bold red]")
            return []

    if not dorks:
        console.print("[bold red]No dork query provided.[/bold red]")
        return []

    user_agents = load_user_agents()
    all_results = []

    try:
        for dork in dorks:
            if args.domain:
                dork += f" site:{args.domain}"

            dork, headers = bypass_waf(dork)
            console.print(f"[bold blue][+] Searching for: {dork}[/bold blue]")
            
            urls = perform_search(dork, args, user_agents)
            results = check_urls(urls, args, headers)
            
            table = Table(title="Search Results")
            table.add_column("URL", style="cyan")
            table.add_column("Status", style="magenta")
            table.add_column("Title", style="green")
            table.add_column("Server", style="yellow")

            for result in results:
                all_results.append(result)
                status_style = "green" if result['status'] == 200 else "yellow" if result['status'] else "red"
                table.add_row(
                    result['url'],
                    str(result['status'] or 'Unreachable'),
                    result['title'],
                    result['server']
                )
                if args.save:
                    save_to_file(f"{result['url']} - Status: {result['status'] or 'Unreachable'} - Title: {result['title']} - Server: {result['server']}", args.save)
                if args.verbose:
                    console.print(f"[dim]Content-Type: {result['content_type']}[/dim]")
                time.sleep(args.delay)

            console.print(table)

    except KeyboardInterrupt:
        console.print("[yellow]User interruption detected.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error in google_dork_search: {str(e)}[/bold red]")
    finally:
        console.print("[bold blue][•] Search completed.[/bold blue]")
        return all_results

def use_tor_network():
    """Configure requests to use Tor network."""
    try:
        import socks
        socks.set_default_proxy(socks.SOCKS5, "localhost", 9050)
        socket.socket = socks.socksocket
    except Exception as e:
        console.print(f"[bold red]Error connecting to SOCKS5 proxy localhost:9050: {str(e)}[/bold red]")
        console.print("[yellow]Make sure Tor is running and the SOCKS proxy is correctly configured.[/yellow]")

def renew_tor_ip():
    """Renew the Tor IP address."""
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)

def rotate_ip_address():
    """Rotate IP address using Tor."""
    use_tor_network()
    renew_tor_ip()
    time.sleep(5)  # Wait for the new IP to be established

def exponential_backoff(attempt: int, max_delay: int = 60) -> None:
    """Implement exponential backoff for rate limiting."""
    delay = min(2 ** attempt, max_delay)
    time.sleep(delay)

def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced Google Dork Finder")
    parser.add_argument("--dork", type=str, help="Google dork query to search")
    parser.add_argument("--dorks-file", type=str, help="File containing multiple dork queries")
    parser.add_argument("--domain", type=str, help="Specific domain to search within")
    parser.add_argument("--number", type=int, default=10, help="Number of search results to display")
    parser.add_argument("--save", type=str, help="File name to save the results")
    parser.add_argument("--proxy", type=str, help="Proxy server to use (format: http://user:pass@host:port)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("--export", choices=["csv", "json"], help="Export results to CSV or JSON")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout for URL checks")
    parser.add_argument("--visual", action="store_true", help="Enable visual dorking mode")
    parser.add_argument("--headless", action="store_true", help="Run visual dorking in headless mode")
    parser.add_argument("--max-results", type=int, default=100, help="Maximum number of results for visual dorking")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads to use")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests to avoid rate limiting")
    parser.add_argument("--antirecaptcha-api", type=str, help="Anti-CAPTCHA API key")
    parser.add_argument("--tor", action="store_true", help="Use Tor network for searches")

    args = parser.parse_args()

    if args.proxy:
        setup_proxy(args.proxy, args.timeout)

    if args.tor:
        use_tor_network()

    try:
        if args.visual:
            results = visual_dorking(args.dork, args.domain, args.headless, args.max_results)
        else:
            results = google_dork_search(args)

        if args.export:
            export_results(results, args.export)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()

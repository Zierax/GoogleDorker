import argparse
import logging
import random
import sys
import time
import socket
from dataclasses import dataclass
from typing import List, Optional
import socks
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from requests.exceptions import RequestException
from stem import Signal
from stem.control import Controller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging with custom format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

def print_banner():
    """Display the tool banner"""
    banner = """
     ██████╗       ██████╗  ██████╗ ██████╗ ██╗  ██╗███████╗██████╗ 
    ██╔════╝       ██╔══██╗██╔═══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗
    ██║  ███╗█████╗██║  ██║██║   ██║██████╔╝█████╔╝ █████╗  ██████╔╝
    ██║   ██║╚════╝██║  ██║██║   ██║██╔══██╗██╔═██╗ ██╔══╝  ██╔══██╗
    ╚██████╔╝      ██████╔╝╚██████╔╝██║  ██║██║  ██╗███████╗██║  ██║
     ╚═════╝       ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                           by Zierax
    """
    version = "v2.0"
    console.print(Panel(Text(banner, style="bold blue"), title=f"[bold yellow]Version {version}[/bold yellow]", 
                       subtitle="[bold cyan]By Your Name[/bold cyan]"))

class SearchProgress:
    """Manage search progress display"""
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        )

    def __enter__(self):
        return self.progress.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.progress.__exit__(exc_type, exc_val, exc_tb)

@dataclass
class SearchResult:
    """Data class to store search result information"""
    url: str
    status: Optional[int] = None
    title: str = "Unreachable"
    server: str = "Unknown"
    content_type: str = "Unknown"

class UserAgentManager:
    """Manages user agent rotation"""
    def __init__(self):
        self.user_agents = self._load_user_agents()

    def _load_user_agents(self) -> List[str]:
        """Load a list of user agents"""
        try:
            ua = UserAgent()
            return [ua.random for _ in range(100)]
        except Exception as e:
            logger.error(f"Error loading user agents: {e}")
            return []

    def get_random(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents) if self.user_agents else ""

class TorManager:
    """Manages Tor network connections"""
    @staticmethod
    def configure_tor():
        """Configure requests to use Tor network"""
        try:
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            socket.socket = socks.socksocket
            logger.info("Tor configuration successful.")
        except Exception as e:
            logger.error(f"Error configuring Tor: {e}")
            console.print("[yellow]Ensure Tor is running and SOCKS proxy is configured.[/yellow]")

    @staticmethod
    def renew_ip():
        """Renew the Tor IP address"""
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
            time.sleep(5)  # Wait for new IP
        except Exception as e:
            logger.error(f"Error renewing Tor IP: {e}")

class RecaptchaHandler:
    """Handles reCAPTCHA bypass operations"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = {}

    def solve_captcha(self, url: str, site_key: str) -> str:
        """Solve reCAPTCHA using anti-captcha service"""
        cache_key = f"{url}_{site_key}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            solver = recaptchaV2Proxyless()
            solver.set_verbose(1)
            solver.set_key(self.api_key)
            solver.set_website_url(url)
            solver.set_website_key(site_key)
            
            response = solver.solve_and_return_solution()
            if response != 0:
                logger.info(f"Captcha solved successfully: {response}")
                self.cache[cache_key] = response
                return response
            else:
                logger.error(f"Captcha solving failed: {solver.error_code}")
                return ""
        except Exception as e:
            logger.error(f"Error solving captcha: {e}")
            return ""

class GoogleDorkFinder:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.ua_manager = UserAgentManager()
        self.session = requests.Session()
        self.driver = None
        self.captcha_handler = None
        
        print_banner()
        
        with SearchProgress() as progress:
            task1 = progress.add_task("[cyan]Initializing...", total=None)
            
            if args.tor:
                progress.update(task1, description="[yellow]Configuring Tor network...")
                TorManager.configure_tor()
            
            if args.antirecaptcha_api:
                progress.update(task1, description="[yellow]Setting up reCAPTCHA handler...")
                self.captcha_handler = RecaptchaHandler(args.antirecaptcha_api)
            
            if args.pre_automated_browsing:
                progress.update(task1, description="[yellow]Setting up Selenium...")
                self._setup_selenium()
            
            progress.update(task1, description="[green]Initialization complete!")
            time.sleep(1)

        console.print(Panel.fit(
            f"[cyan]Domain:[/cyan] {args.domain}\n"
            f"[cyan]Dorks File:[/cyan] {args.dorks_file}\n"
            f"[cyan]Max Results:[/cyan] {args.number}\n"
            f"[cyan]Using Tor:[/cyan] {'Yes' if args.tor else 'No'}\n"
            f"[cyan]Automated Browsing:[/cyan] {'Yes' if args.pre_automated_browsing else 'No'}",
            title="Configuration",
            border_style="blue"
        ))

    def _setup_selenium(self):
        """Setup Selenium WebDriver for automated browsing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            console.print("[green]✓[/green] Selenium WebDriver configured successfully")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to initialize Chrome WebDriver: {str(e)}")
            if self.args.pre_automated_browsing:
                console.print("[yellow]![/yellow] Continuing without automated browsing...")
                self.args.pre_automated_browsing = False

    def search(self):
        """Start searching with the loaded dorks"""
        dorks = self._load_dorks()
        if not dorks:
            console.print("[red]✗[/red] No dorks to search with.")
            return

        total_results = []
        with SearchProgress() as progress:
            search_task = progress.add_task("[cyan]Searching...", total=len(dorks))
            
            for dork in dorks:
                progress.update(search_task, description=f"[cyan]Processing dork:[/cyan] {dork[:50]}...")
                modified_dork = self._prepare_dork(dork)
                urls = self._perform_search(modified_dork)
                search_results = self._check_urls(urls)
                total_results.extend(search_results)
                progress.advance(search_task)

        self._display_results(total_results)
        
        if self.args.save:
            self._save_results(total_results)

    def _load_dorks(self) -> List[str]:
        """Load dorks from arguments or file"""
        dorks = [self.args.dork] if self.args.dork else []
        if self.args.dorks_file:
            try:
                with open(self.args.dorks_file, 'r') as file:
                    dorks.extend([line.strip() for line in file if line.strip()])
                logger.info(f"Loaded {len(dorks)} dorks from file")
            except IOError as e:
                logger.error(f"Error reading dorks file: {e}")
        return dorks

    def _prepare_dork(self, dork: str) -> str:
        """Prepares the dork by appending domain or other parameters."""
        if self.args.domain:
            domain = self.args.domain if not self.args.domain.startswith('*') else self.args.domain[2:]
            dork = f"{dork} site:{domain}"
            logger.debug(f"Prepared dork: {dork}")
        return dork

    def _perform_search(self, dork: str) -> List[str]:
        """Perform search with the prepared dork"""
        urls = []
        base_url = "https://www.google.com/search"
        start = 0
        consecutive_errors = 0

        while len(urls) < self.args.number and consecutive_errors < 3:
            try:
                current_ua = self.ua_manager.get_random()
                headers = {
                    'User-Agent': current_ua,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }

                params = {
                    'q': dork,
                    'start': start,
                    'num': 10,
                    'hl': 'en',
                    'filter': '0'
                }

                if self.args.pre_automated_browsing and self.driver:
                    self.driver.get(base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()]))
                    time.sleep(3)

                    if self._check_for_verification(self.driver):
                        logger.warning("Verification required by Google. Please bypass manually.")
                        console.print("[yellow]Google verification detected. Please bypass manually and press Enter to continue.[/yellow]")
                        input("Press Enter to continue once bypassed.")
                        continue

                    new_urls = self._extract_urls(self.driver.page_source)
                else:
                    response = self.session.get(
                        base_url,
                        params=params,
                        headers=headers,
                        timeout=self.args.timeout
                    )

                    if response.status_code != 200:
                        logger.warning(f"Received non-200 status code: {response.status_code}")
                        consecutive_errors += 1
                        continue

                    if "recaptcha" in response.text.lower():
                        logger.warning("CAPTCHA detected")
                        console.print("[yellow]CAPTCHA encountered. Trying to bypass...[/yellow]")
                        break

                    if "unusual traffic" in response.text.lower():
                        logger.warning("Unusual traffic detected")
                        console.print("[yellow]Google detected unusual traffic. Waiting...[/yellow]")
                        time.sleep(30)
                        continue

                    new_urls = self._extract_urls(response.text)

                if not new_urls:
                    logger.warning("No URLs found in response")
                    consecutive_errors += 1
                    continue

                urls.extend(new_urls)
                consecutive_errors = 0
                start += 10

                delay = random.uniform(self.args.delay, self.args.delay * 2)
                time.sleep(delay)

            except RequestException as e:
                logger.error(f"Request error: {e}")
                consecutive_errors += 1
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                consecutive_errors += 1
                time.sleep(5)

        return urls[:self.args.number]

    def _check_for_verification(self, driver: webdriver.Chrome) -> bool:
        """Check if Google verification page is detected"""
        try:
            if "recaptcha" in driver.page_source.lower() or "unusual traffic" in driver.page_source.lower():
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking verification: {e}")
            return False

    def _extract_urls(self, html_content: str) -> List[str]:
        """Extract URLs from search results"""
        urls = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            selectors = [
                'a[href^="/url?q="]',
                'div.g div.r a',
                'div.yuRUbf > a',
                'div.g a[href^="http"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href.startswith('/url?q='):
                        href = href.split('/url?q=')[1].split('&')[0]
                    if href.startswith(('http://', 'https://')):
                        urls.append(href)
            
            urls = list(dict.fromkeys(urls))
        except Exception as e:
            logger.error(f"Error extracting URLs: {e}")
        
        return urls

    def _display_results(self, results: List[SearchResult]):
        """Display search results in a table"""
        if not results:
            console.print("[bold red]No results found.[/bold red]")
            return

        table = Table(title="Google Dork Results", show_header=True, header_style="bold magenta")
        table.add_column("URL", style="dim", width=50)
        table.add_column("Title")
        table.add_column("Server")
        table.add_column("Content-Type")
        table.add_column("Status")

        for result in results:
            table.add_row(
                result.url,
                result.title[:40],
                result.server[:20],
                result.content_type[:20],
                str(result.status) if result.status else "Unknown"
            )

        console.print(table)

    def _check_urls(self, urls: List[str]) -> List[SearchResult]:
        """Check the URLs from the search results"""
        results = []

        for url in urls:
            try:
                logger.debug(f"Checking URL: {url}")
                headers = {'User-Agent': self.ua_manager.get_random()}
                response = self.session.get(url, headers=headers, timeout=self.args.timeout)
                result = SearchResult(
                    url=url,
                    status=response.status_code,
                    title=self._get_title(response),
                    server=response.headers.get('Server', 'Unknown'),
                    content_type=response.headers.get('Content-Type', 'Unknown')
                )
                results.append(result)
            except RequestException as e:
                logger.error(f"Error fetching URL {url}: {e}")
                results.append(SearchResult(url=url))

        return results

    def _get_title(self, response: requests.Response) -> str:
        """Extract title from HTML response"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.title
            return title_tag.text if title_tag else "No title"
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return "No title"

    def _save_results(self, results: List[SearchResult]):
        """Save results to file with progress indicator"""
        if not self.args.output:
            return

        with SearchProgress() as progress:
            save_task = progress.add_task("[cyan]Saving results...", total=len(results))
            
            try:
                with open(self.args.output, 'w') as file:
                    file.write("URL,Status,Title,Server,Content-Type\n")
                    for result in results:
                        file.write(f"{result.url},{result.status},{result.title},{result.server},{result.content_type}\n")
                        progress.advance(save_task)
                
                console.print(f"[green]✓[/green] Results saved to: {self.args.output}")
            except IOError as e:
                console.print(f"[red]✗[/red] Error saving results: {e}")
                
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Google Dork Finder")
    parser.add_argument("-d", "--domain", help="Search within specific domain")
    parser.add_argument("-dork", help="Specific dork query")
    parser.add_argument("-f", "--dorks-file", help="File containing a list of dorks")
    parser.add_argument("-n", "--number", type=int, default=50, help="Number of results to fetch")
    parser.add_argument("--delay", type=int, default=2, help="Delay between requests (seconds)")
    parser.add_argument("-o", "--output", help="Output file to save results")
    parser.add_argument("--save", action="store_true", help="Save results to file")
    parser.add_argument("--tor", action="store_true", help="Use Tor network")
    parser.add_argument("--antirecaptcha-api", help="API key for solving reCAPTCHA")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout (seconds)")
    parser.add_argument("--pre-automated-browsing", action="store_true", help="Use Selenium for automated browsing for bypass recaptcha")
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        dork_finder = GoogleDorkFinder(args)
        dork_finder.search()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")
        sys.exit(1)
    finally:
        if 'dork_finder' in locals() and hasattr(dork_finder, 'driver'):
            if dork_finder.driver:
                dork_finder.driver.quit()

if __name__ == "__main__":
    main()

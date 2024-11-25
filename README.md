# GoogleDorker v2.0

Google Dork Finder is an advanced Python tool designed for efficient and comprehensive Google Dorking. It offers a wide range of features for both automated and visual dorking, making it a versatile tool for information gathering and web reconnaissance.

## Features

- **Single and Multiple Dork Queries**: Search using a single dork or multiple dorks from a file.
- **Domain-Specific Searches**: Restrict searches to a specified domain.
- **Visual Dorking Mode**: Interactive browser-based dorking with real-time result extraction.
- **Proxy Support**: Route searches through a proxy server for anonymity.
- **Multi-threaded Operations**: Faster searches and URL checks using concurrent processing.
- **WAF Bypass Techniques**: Implements methods to bypass Web Application Firewalls.
- **Customizable User Agents**: Uses a pool of user agents to avoid detection.
- **Verbose Mode**: Detailed output for each search query and result.
- **Export Options**: Save results in various formats (CSV, JSON).
- **Timeout and Delay Settings**: Configure request timeouts and delays between searches.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Zierax/GoogleDorker.git
   cd GoogleDorker
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   sudo apt install tor
   ```

## Usage

Run Google Dork Finder from the command line with various options:
```python
python Gorker.py [OPTIONS_BELOW]
```
| Argument                     | Description                                                                                  |
|------------------------------|----------------------------------------------------------------------------------------------|
| `-d, --domain`               | Specify a domain to limit search results (e.g., `site:example.com`).                         |
| `-D, --dorks-file`           | Provide a file containing a list of dorks.                                                   |
| `--dork`                     | Specify a single dork query to use in the search.                                            |
| `-n, --number`               | Number of results to retrieve per query (default: 10).                                       |
| `-t, --threads`              | Number of threads to use for concurrent processing (default: 4).                             |
| `--timeout`                  | Timeout in seconds for HTTP requests (default: 5).                                           |
| `--delay`                    | Delay in seconds between each request to avoid rate-limiting (default: 2).                   |
| `--proxy`                    | Use Tor for privacy by routing traffic through the Tor network.                              |
| `--verbose`                  | Display detailed information about the search results.                                       |
| `--pre-automated-browsing`   | Automate browser actions like solving reCAPTCHA or bypassing restrictions.                   |


## Notes
- Ensure you have an active Anti-Captcha API key if using CAPTCHA bypass.  
- Tor must be properly configured for IP rotation.  
- Use responsibly and only for ethical purposes with permission.  

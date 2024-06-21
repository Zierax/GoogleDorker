<h1>Google Dork Finder</h1>
Google Dork Finder is a Python tool designed to facilitate the use of Google Dorking for searching specific information on the web. It supports domain-specific searches, the use of proxy servers, and processing multiple dorks from a file. Additionally, it includes options to save search results and provides a verbose mode for detailed output.

Features
  
Single Dork Query: Search the web using a specific Google dork query.
Multiple Dork Queries: Use a file containing multiple dork queries.
Domain-Specific Searches: Restrict searches to a specified domain.
Proxy Support: Route searches through a proxy server.
Verbose Mode: Get detailed output for each search query.
Save Results: Save search results to a specified file.
  
Installation
Clone the repository:

```

git clone https://github.com/yourusername/google-dork-finder.git
cd google-dork-finder
Install required packages:

```
```

pip install -r requirements.txt
```
Usage
You can run Google Dork Finder directly from the command line. Below are the available command-line arguments:
  
Command-Line Arguments
  
```
--dork: Specify a single Google dork query.
--dorks_file: Specify a file containing multiple Google dork queries.
--domain: Restrict searches to a specific domain.
--number: Define the number of search results to display for each query (default is 10).
--save: Provide a filename to save the results.
--proxy: Use a proxy server (format: http://user:pass@host:port).
--verbose: Enable verbose mode for detailed output.
```
Examples
Search with a single dork query:
  

```
python google_dork_finder.py --dork "intitle:index.of"
```

Search using a file with multiple dork queries:
```
python google_dork_finder.py --dorks_file dorks.txt
```
Restrict search to a specific domain:

```
python google_dork_finder.py --dork "intitle:index.of" --domain example.com
``
Save results to a file:

```
python google_dork_finder.py --dork "intitle:index.of" --save results
```
Use a proxy server:

```
python google_dork_finder.py --dork "intitle:index.of" --proxy "http://user:pass@proxyserver:port"
```
Enable verbose mode for detailed output:

```

python google_dork_finder.py --dork "intitle:index.of" --verbose
```

Contributing
Contributions are welcome! Please submit a pull request or open an issue to discuss changes.


Acknowledgments
Inspired by the original idea of Google Dorking.
Thanks to the open-source community for tools and libraries.
Contact
For any questions or suggestions, feel free to reach out via GitHub Issues.

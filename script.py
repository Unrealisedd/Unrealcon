import os
import subprocess
import sys
import time
import re
import concurrent.futures
from colorama import init, Fore, Style
import requests
import platform
import glob
import concurrent.futures
import urllib.parse
import shutil


class XssRecon:
    def __init__(self):
        self.domain_name = ""
        self.last_completed_option = 1
        self.skip_order_check_for_option_4 = False
        self.total_merged_urls = 0
        
        # Initialize colorama for Windows color support
        init()
        
        # Color definitions
        self.BOLD_WHITE = Style.BRIGHT + Fore.WHITE
        self.BOLD_BLUE = Style.BRIGHT + Fore.BLUE
        self.RED = Fore.RED
        self.YELLOW = Fore.YELLOW
        self.GREEN = Fore.GREEN
        self.CYAN = Fore.CYAN

    def show_banner(self):
        os.system("cls" if platform.system() == "Windows" else "clear")
        print(f"{self.BOLD_BLUE}")
        print(r" _   _ _ __  _ __ ___  __ _| | ___ ___  _ __  ")
        print(r"| | | | '_ \| '__/ _ \/ _` | |/ __/ _ \| '_ \ ")
        print(r"| |_| | | | | | |  __/ (_| | | (_| (_) | | | |")
        print(r" \__,_|_| |_|_|  \___|\__,_|_|\___\___/|_| |_|")
        print(f"{Style.RESET_ALL}")

        print(
            f"{self.BOLD_BLUE}                      Discord: Unrealisedd{Style.RESET_ALL}"
        )

    def check_tool_installation(self, tool_name, check_command=None):
        if not check_command:
            check_command = [tool_name, '--version']
        try:
            result = subprocess.run(check_command, capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    def install_go_tool(self, tool_name, tool_path):
        print(f"{self.BOLD_BLUE}Installing {tool_name}...{Style.RESET_ALL}")
        try:
            # Install the tool
            subprocess.run(['go', 'install', f"{tool_path}@latest"], check=True)
            
            # Get the binary path
            binary_name = tool_path.split("/")[-1]
            src_path = os.path.join(os.environ.get("GOPATH", os.path.expanduser("~/go")), "bin", f"{binary_name}.exe")
            
            if os.path.exists(src_path):
                # Use PowerShell to copy with elevation
                print(f"{self.YELLOW}Requesting admin privileges to install {tool_name}...{Style.RESET_ALL}")
                powershell_command = f'Start-Process powershell -Verb RunAs -ArgumentList "Copy-Item \'{src_path}\' \'C:\\Windows\\System32\' -Force"'
                subprocess.run(['powershell', '-Command', powershell_command], check=True)
                print(f"{self.GREEN}✓ {tool_name} installed successfully{Style.RESET_ALL}")
                return True
        except Exception as e:
            print(f"{self.RED}Failed to install {tool_name}: {str(e)}{Style.RESET_ALL}")
            return False


    def install_tools(self):
        print(f"{self.BOLD_WHITE}Checking and installing required tools...{Style.RESET_ALL}")
        is_windows = platform.system() == "Windows"
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)

        # Check Python packages first
        python_packages = ["requests", "colorama", "alive-progress", "aiodns", "structlog"]
        for package in python_packages:
            try:
                __import__(package)
                print(f"{self.GREEN}✓ {package} is already installed{Style.RESET_ALL}")
            except ImportError:
                print(f"{self.BOLD_BLUE}Installing {package}...{Style.RESET_ALL}")
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

        # Check Go installation
        if self.check_tool_installation('go', ['go', 'version']):
            print(f"{self.GREEN}✓ Go is already installed{Style.RESET_ALL}")
        else:
            print(f"{self.BOLD_BLUE}Go installation required. Please install Go from https://go.dev/dl/{Style.RESET_ALL}")
            return False

        # Check Go tools - Common tools for both platforms
        go_tools = {
            "gospider": "github.com/jaeles-project/gospider",
            "hakrawler": "github.com/hakluke/hakrawler",
            "katana": "github.com/projectdiscovery/katana/cmd/katana",
            "waybackurls": "github.com/tomnomnom/waybackurls",
            "gau": "github.com/lc/gau/v2/cmd/gau",
            "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder",
            "amass": "github.com/owasp-amass/amass/v4/...",
            "httpx": "github.com/projectdiscovery/httpx/cmd/httpx",
            "nuclei": "github.com/projectdiscovery/nuclei/v2/cmd/nuclei"
        }

        for tool_name, tool_path in go_tools.items():
            if self.check_tool_installation(tool_name):
                print(f"{self.GREEN}✓ {tool_name} is already installed{Style.RESET_ALL}")
            else:
                self.install_go_tool(tool_name, tool_path)

        # Base tools for both platforms
        other_tools = [
            ("arjun", "arjun"),
            ("uro", "uro"),
            ("subprober", "git+https://github.com/sanjai-AK47/Subprober.git")
        ]

        # Add Linux-specific tools
        if not is_windows:
            linux_tools = [
                ("dnsbruter", "git+https://github.com/RevoltSecurities/Dnsbruter.git"),
                ("subdominator", "git+https://github.com/RevoltSecurities/Subdominator")
            ]
            other_tools.extend(linux_tools)

        for tool_name, install_path in other_tools:
            if self.check_tool_installation(tool_name):
                print(f"{self.GREEN}✓ {tool_name} is already installed{Style.RESET_ALL}")
            else:
                print(f"{self.BOLD_BLUE}Installing {tool_name}...{Style.RESET_ALL}")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", install_path], check=True)
                except Exception as e:
                    print(f"{self.RED}Failed to install {tool_name}: {str(e)}{Style.RESET_ALL}")

        # Check and download wordlists
        wordlists_dir = "wordlists"
        os.makedirs(wordlists_dir, exist_ok=True)
        wordlist_path = os.path.join(wordlists_dir, "subdomains.txt")

        if os.path.exists(wordlist_path):
            print(f"{self.GREEN}✓ Wordlist already exists{Style.RESET_ALL}")
        else:
            print(f"{self.BOLD_BLUE}Downloading wordlist...{Style.RESET_ALL}")
            wordlist_url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-110000.txt"
            try:
                response = requests.get(wordlist_url)
                with open(wordlist_path, "wb") as f:
                    f.write(response.content)
                print(f"{self.GREEN}✓ Wordlist downloaded successfully{Style.RESET_ALL}")
            except Exception as e:
                print(f"{self.RED}Failed to download wordlist: {str(e)}{Style.RESET_ALL}")

        print(f"\n{self.BOLD_BLUE}Installation process completed{Style.RESET_ALL}")
        self.last_completed_option = 1


    def display_menu(self):
        print(f"\n{self.BOLD_BLUE}Please select an option:{Style.RESET_ALL}")
        print(f"{self.RED}1: Install all tools{Style.RESET_ALL}")
        print(f"{self.RED}2: Enter a domain name of the target{Style.RESET_ALL}")
        print(f"{self.YELLOW}3: Enumerate and filter domains{Style.RESET_ALL}")
        print(f"{self.YELLOW}4: Crawl and filter URLs{Style.RESET_ALL}")
        print(f"{self.YELLOW}5: Filtering all{Style.RESET_ALL}")
        print(f"{self.YELLOW}6: Create new separated file for parameter testing{Style.RESET_ALL}")
        print(f"{self.YELLOW}7: Getting ready for XSS & URLs with query strings{Style.RESET_ALL}")
        print(f"{self.YELLOW}8: unrealcon RUN{Style.RESET_ALL}")
        print(f"{self.YELLOW}9: URL dedupe{Style.RESET_ALL}")
        print(f"{self.YELLOW}10: Exit{Style.RESET_ALL}")
        print(f"{self.YELLOW}I would advice doing 9 before 8 btw, saves you some time :){Style.RESET_ALL}")
        

    def run(self):
        while True:
            self.show_banner()
            self.display_menu()
            
            try:
                choice = int(input("Enter your choice [1-10]: "))

                if choice == 1:
                    self.install_tools()
                    self.last_completed_option = 1
                elif choice == 2:
                    self.domain_name = input("Enter domain name (example.com): ")
                    self.last_completed_option = 2
                elif choice == 3:
                    if not self.domain_name:
                        print("Domain name not set. Please select option 2 to set the domain name.")
                    else:
                        self.enumerate_domains()
                elif choice == 4:
                    if not self.domain_name:
                        print("Domain name not set. Please select option 2 to set the domain name.")
                    else:
                        self.crawl_urls()
                elif choice == 5:
                    if not self.domain_name:
                        print("Domain name not set. Please select option 2 to set the domain name.")
                    else:
                        self.filter_all()
                elif choice == 6:
                    if not self.domain_name:
                        print("Domain name not set. Please select option 2 to set the domain name.")
                    else:
                        self.create_parameter_files()
                elif choice == 7:
                    if not self.domain_name:
                        print("Domain name not set. Please select option 2 to set the domain name.")
                    else:
                        self.prepare_xss()
                elif choice == 8:
                    if not self.domain_name:
                        print("Domain name not set. Please select option 2 to set the domain name.")
                    else:
                        self.run_xss()
                elif choice == 9:
                    if not self.domain_name:
                        print("Domain name not set. Please select option 2 to set the domain name.")
                    else:
                        self.dedupe_urls()
                elif choice == 10:
                    print("Exiting...")
                    break
                else:
                    print(f"{self.RED}Invalid option{Style.RESET_ALL}")
                
            except ValueError:
                print(f"{self.RED}Please enter a valid number{Style.RESET_ALL}")



    def enumerate_domains(self):
        if not self.domain_name:
            print(f"{self.RED}Domain name not set. Please use option 2 first.{Style.RESET_ALL}")
            return

        print(f"{self.BOLD_WHITE}Enumerating domains for {self.domain_name}{Style.RESET_ALL}")
        
        os.makedirs("recon_output", exist_ok=True)

        def run_subfinder():
            output_file = os.path.join("recon_output", "subfinder_output.txt")
            cmd = f"subfinder -d {self.domain_name} -o {output_file}"
            subprocess.run(cmd, shell=True)
            return output_file

        print(f"{self.BOLD_BLUE}Starting passive enumeration with Subfinder...⌛️{Style.RESET_ALL}")
        tool_output = run_subfinder()

        # Process results
        merged_file = os.path.join("recon_output", f"{self.domain_name}-domains.txt")
        if os.path.exists(tool_output):
            shutil.copy2(tool_output, merged_file)

        # Remove duplicates
        domains = set()
        with open(merged_file) as f:
            domains = {line.strip().lower() for line in f if line.strip()}

        # Write unique domains back
        with open(merged_file, "w") as f:
            for domain in sorted(domains):
                f.write(f"{domain}\n")

        print(f"{self.BOLD_BLUE}Found {len(domains)} unique domains{Style.RESET_ALL}")

        def check_domain(domain):
            try:
                response = requests.get(f"http://{domain}", timeout=5)
                return domain if response.status_code in [200, 301, 302, 307, 308, 403] else None
            except:
                return None

        print(f"{self.BOLD_BLUE}Verifying domain availability...⌛️{Style.RESET_ALL}")

        alive_domains = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(check_domain, domain) for domain in domains]
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    alive_domains.append(future.result())

        # Write alive domains
        alive_file = os.path.join("recon_output", f"{self.domain_name}-alive-domains.txt")
        with open(alive_file, "w") as f:
            for domain in sorted(alive_domains):
                f.write(f"http://{domain}\n")

        print(f"{self.GREEN}Found {len(alive_domains)} alive domains{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Results saved to {alive_file}{Style.RESET_ALL}")

        self.last_completed_option = 3



    def crawl_urls(self):
        if not self.domain_name:
            print(f"{self.RED}Domain name not set. Please use option 2 first.{Style.RESET_ALL}")
            return
            
        print(f"{self.BOLD_WHITE}Crawling URLs for {self.domain_name}{Style.RESET_ALL}")
        
        domains_file = os.path.join("recon_output", f"{self.domain_name}-alive-domains.txt")
        if not os.path.exists(domains_file):
            print(f"{self.RED}Domains file not found. Please run enumeration first.{Style.RESET_ALL}")
            return

        def safe_file_operation(file_path, mode='r', operation=None):
            try:
                if mode == 'w':
                    if os.path.exists(file_path):
                        os.chmod(file_path, 0o666)
                with open(file_path, mode) as f:
                    if operation:
                        return operation(f)
                    return f.read()
            except PermissionError:
                print(f"{self.YELLOW}Fixing permissions for {file_path}{Style.RESET_ALL}")
                try:
                    os.chmod(file_path, 0o666)
                    with open(file_path, mode) as f:
                        if operation:
                            return operation(f)
                        return f.read()
                except Exception as e:
                    print(f"{self.RED}Could not access {file_path}: {str(e)}{Style.RESET_ALL}")
                    return ""

        def run_gospider():
            output_file = os.path.join("recon_output", f"{self.domain_name}-gospider.txt")
            cmd = f"gospider -S {domains_file} -c 10 -d 5 -o {output_file}"
            subprocess.run(cmd, shell=True)
            return output_file

        def run_hakrawler():
            output_file = os.path.join("recon_output", f"{self.domain_name}-hakrawler.txt")
            with open(domains_file) as f:
                domains = f.read()
            process = subprocess.Popen(
                ["hakrawler", "-d", "3"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            output, _ = process.communicate(input=domains)
            safe_file_operation(output_file, 'w', lambda f: f.write(output))
            return output_file

        def run_katana():
            output_file = os.path.join("recon_output", f"{self.domain_name}-katana.txt")
            cmd = f"katana -list {domains_file} -o {output_file}"
            subprocess.run(cmd, shell=True)
            return output_file

        def run_waybackurls():
            output_file = os.path.join("recon_output", f"{self.domain_name}-wayback.txt")
            with open(domains_file) as f:
                domains = f.read()
            process = subprocess.Popen(
                ["waybackurls"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            output, _ = process.communicate(input=domains)
            safe_file_operation(output_file, 'w', lambda f: f.write(output))
            return output_file

        def run_gau():
            output_file = os.path.join("recon_output", f"{self.domain_name}-gau.txt")
            with open(domains_file) as f:
                domains = f.read()
            process = subprocess.Popen(
                ["gau"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            output, _ = process.communicate(input=domains)
            safe_file_operation(output_file, 'w', lambda f: f.write(output))
            return output_file

        print(f"{self.BOLD_BLUE}Starting URL crawling with multiple tools...⌛️{Style.RESET_ALL}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(run_gospider): "GoSpider",
                executor.submit(run_hakrawler): "Hakrawler",
                executor.submit(run_katana): "Katana",
                executor.submit(run_waybackurls): "Waybackurls",
                executor.submit(run_gau): "Gau"
            }
            
            for future in concurrent.futures.as_completed(futures):
                tool_name = futures[future]
                try:
                    output_file = future.result()
                    print(f"{self.GREEN}{tool_name} completed, output saved to {output_file}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{self.RED}{tool_name} failed: {str(e)}{Style.RESET_ALL}")

        merged_file = os.path.join("recon_output", f"{self.domain_name}-all-urls.txt")
        all_urls = set()
        url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
        
        for tool_file in glob.glob(os.path.join("recon_output", f"{self.domain_name}-*.txt")):
            if tool_file != merged_file:
                content = safe_file_operation(tool_file)
                urls = url_pattern.findall(content)
                all_urls.update(urls)

        safe_file_operation(merged_file, 'w', lambda f: f.write('\n'.join(sorted(all_urls)) + '\n'))

        self.total_merged_urls = len(all_urls)
        print(f"{self.BOLD_BLUE}Total unique URLs found: {self.total_merged_urls}{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Results merged and saved to {merged_file}{Style.RESET_ALL}")
        
        self.last_completed_option = 4


    def filter_all(self):
        if not self.domain_name:
            print(f"{self.RED}Domain name not set. Please use option 2 first.{Style.RESET_ALL}")
            return

        input_file = os.path.join("recon_output", f"{self.domain_name}-all-urls.txt")
        if not os.path.exists(input_file):
            print(f"{self.RED}URLs file not found. Please run crawling first.{Style.RESET_ALL}")
            return

        print(f"{self.BOLD_WHITE}Filtering URLs for {self.domain_name}{Style.RESET_ALL}")

        # Define unwanted extensions
        unwanted_extensions = r'\.(css|js|jpg|jpeg|png|gif|ico|woff|woff2|ttf|eot|svg|pdf|doc|docx|xls|xlsx|zip|tar|gz|mp3|mp4|avi|swf)($|\?)'
        
        def filter_urls(urls):
            filtered = []
            for url in urls:
                # Skip URLs with unwanted extensions
                if re.search(unwanted_extensions, url.lower()):
                    continue
                # Ensure URL belongs to target domain
                if self.domain_name in url.lower():
                    filtered.append(url)
            return filtered

        def normalize_urls(urls):
            normalized = set()
            for url in urls:
                # Convert https to http
                url = url.replace('https://', 'http://')
                # Remove www.
                url = url.replace('www.', '')
                # Remove trailing slashes
                url = url.rstrip('/')
                normalized.add(url)
            return sorted(normalized)

        def filter_parameters(urls):
            param_urls = {}
            for url in urls:
                base_url = url.split('?')[0]
                params = []
                if '?' in url:
                    query = url.split('?')[1]
                    params = sorted([p.split('=')[0] for p in query.split('&')])
                
                key = f"{base_url}|{'|'.join(params)}"
                if key not in param_urls:
                    param_urls[key] = url
            return list(param_urls.values())

        print(f"{self.BOLD_BLUE}Reading URLs...⌛️{Style.RESET_ALL}")
        with open(input_file) as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"{self.BOLD_BLUE}Initial URL count: {len(urls)}{Style.RESET_ALL}")

        # Apply filters
        print(f"{self.BOLD_BLUE}Filtering unwanted extensions...⌛️{Style.RESET_ALL}")
        filtered_urls = filter_urls(urls)
        
        print(f"{self.BOLD_BLUE}Normalizing URLs...⌛️{Style.RESET_ALL}")
        normalized_urls = normalize_urls(filtered_urls)
        
        print(f"{self.BOLD_BLUE}Filtering similar parameters...⌛️{Style.RESET_ALL}")
        final_urls = filter_parameters(normalized_urls)

        # Save filtered results
        output_file = os.path.join("recon_output", f"{self.domain_name}-filtered-urls.txt")
        with open(output_file, 'w') as f:
            for url in final_urls:
                f.write(f"{url}\n")

        print(f"{self.GREEN}Filtering complete:{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Initial URLs: {len(urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Final URLs: {len(final_urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Results saved to {output_file}{Style.RESET_ALL}")

        self.last_completed_option = 5

    def create_parameter_files(self):
        if not self.domain_name:
            print(f"{self.RED}Domain name not set. Please use option 2 first.{Style.RESET_ALL}")
            return

        input_file = os.path.join("recon_output", f"{self.domain_name}-filtered-urls.txt")
        if not os.path.exists(input_file):
            print(f"{self.RED}Filtered URLs file not found. Please run filtering first.{Style.RESET_ALL}")
            return

        print(f"{self.BOLD_WHITE}Creating parameter files for {self.domain_name}{Style.RESET_ALL}")

        def is_dynamic_endpoint(url):
            patterns = [r'\.php', r'\.asp', r'\.aspx', r'\.jsp', r'\.cfm']
            return any(re.search(pattern, url.lower()) for pattern in patterns)

        def run_parameter_finder():
            if platform.system() == 'Windows':
                output_file = os.path.join("recon_output", f"{self.domain_name}-arjun.txt")
                temp_urls_file = os.path.join("recon_output", "temp_arjun_urls.txt")
                with open(temp_urls_file, 'w') as f:
                    f.write('\n'.join(dynamic_urls))
                cmd = f"arjun -i {temp_urls_file} -oT {output_file} -t 10"
                subprocess.run(cmd, shell=True)
                os.remove(temp_urls_file)
            else:
                output_file = os.path.join("recon_output", f"{self.domain_name}-paramspider.txt")
                cmd = f"paramspider -l {dynamic_urls_file} -o {output_file}"
                subprocess.run(cmd, shell=True)
            return output_file

        # Separate URLs based on whether they have parameters
        dynamic_urls = []
        parameter_urls = []
        
        with open(input_file) as f:
            for line in f:
                url = line.strip()
                if '?' in url:
                    parameter_urls.append(url)
                elif is_dynamic_endpoint(url):
                    dynamic_urls.append(url)

        print(f"{self.BOLD_BLUE}Found {len(dynamic_urls)} dynamic endpoints{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Found {len(parameter_urls)} URLs with parameters{Style.RESET_ALL}")

        # Run parameter finder on dynamic endpoints
        if dynamic_urls:
            print(f"{self.BOLD_BLUE}Running parameter discovery...⌛️{Style.RESET_ALL}")
            params_file = run_parameter_finder()
            
            if os.path.exists(params_file):
                with open(params_file) as f:
                    new_params_urls = [line.strip() for line in f if line.strip()]
                print(f"{self.GREEN}Found {len(new_params_urls)} new parameter combinations{Style.RESET_ALL}")
                parameter_urls.extend(new_params_urls)

        # Save all URLs with parameters
        output_file = os.path.join("recon_output", f"{self.domain_name}-parameters.txt")
        with open(output_file, 'w') as f:
            for url in sorted(set(parameter_urls)):
                f.write(f"{url}\n")

        print(f"{self.BOLD_BLUE}Total URLs with parameters: {len(parameter_urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Results saved to {output_file}{Style.RESET_ALL}")

        self.last_completed_option = 6

    def prepare_xss(self):
        if not self.domain_name:
            print(f"{self.RED}Domain name not set. Please use option 2 first.{Style.RESET_ALL}")
            return

        input_file = os.path.join("recon_output", f"{self.domain_name}-parameters.txt")
        if not os.path.exists(input_file):
            print(f"{self.RED}Parameters file not found. Please run parameter testing first.{Style.RESET_ALL}")
            return

        print(f"{self.BOLD_WHITE}Preparing XSS testing for {self.domain_name}{Style.RESET_ALL}")

        def check_reflection(url):
            try:
                # Add a unique parameter to check reflection
                test_param = f"xsstest{int(time.time())}"
                test_value = f"reflection{int(time.time())}"
                
                if '?' in url:
                    test_url = f"{url}&{test_param}={test_value}"
                else:
                    test_url = f"{url}?{test_param}={test_value}"

                if platform.system() == 'Windows':
                    response = requests.get(test_url, timeout=10)
                    return test_value in response.text
                else:
                    cmd = f"curl -s '{test_url}' | grep -q '{test_value}'"
                    return subprocess.run(cmd, shell=True).returncode == 0
            except:
                return False

        def normalize_parameter_url(url):
            base_url = url.split('?')[0]
            if '?' not in url:
                return url
                
            params = url.split('?')[1].split('&')
            unique_params = []
            seen_params = set()
            
            for param in params:
                param_name = param.split('=')[0]
                if param_name not in seen_params:
                    seen_params.add(param_name)
                    unique_params.append(param)
                    
            return f"{base_url}?{'&'.join(sorted(unique_params))}"

        print(f"{self.BOLD_BLUE}Checking parameter reflection...⌛️{Style.RESET_ALL}")
        
        reflected_urls = []
        total_urls = 0
        
        with open(input_file) as f:
            urls = [line.strip() for line in f if line.strip()]
            total_urls = len(urls)

        max_workers = 10 if platform.system() == 'Windows' else 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(check_reflection, url): url for url in urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    if future.result():
                        reflected_urls.append(normalize_parameter_url(url))
                except Exception as e:
                    print(f"{self.RED}Error checking {url}: {str(e)}{Style.RESET_ALL}")

        # Save reflected URLs
        output_file = os.path.join("recon_output", f"{self.domain_name}-xss-candidates.txt")
        with open(output_file, 'w') as f:
            for url in sorted(set(reflected_urls)):
                f.write(f"{url}\n")

        print(f"{self.GREEN}XSS preparation complete:{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Total URLs checked: {total_urls}{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Reflected URLs found: {len(reflected_urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Results saved to {output_file}{Style.RESET_ALL}")

        self.last_completed_option = 7

    def run_xss(self):
        if not self.domain_name:
            print(f"{self.RED}Domain name not set. Please use option 2 first.{Style.RESET_ALL}")
            return

        input_file = os.path.join("recon_output", f"{self.domain_name}-xss-candidates.txt")
        if not os.path.exists(input_file):
            print(f"{self.RED}XSS candidates file not found. Please run XSS preparation first.{Style.RESET_ALL}")
            return

        print(f"{self.BOLD_WHITE}Running XSS tests for {self.domain_name}{Style.RESET_ALL}")

        def load_payloads():
            payloads_file = "payloads.txt"
            if not os.path.exists(payloads_file):
                print(f"{self.YELLOW}Creating default payloads file...{Style.RESET_ALL}")
                default_payloads = [
                    '"><script>alert(1)</script>',
                    '"><img src=x onerror=alert(1)>',
                    "'><script>alert(1)</script>",
                    '"><svg onload=alert(1)>',
                    "javascript:alert(1)"
                ]
                with open(payloads_file, 'w') as f:
                    f.write('\n'.join(default_payloads))
            
            with open(payloads_file) as f:
                return [line.strip() for line in f if line.strip()]

        def test_xss(url, payload):
            try:
                if platform.system() == 'Windows':
                    parsed_url = list(urllib.parse.urlparse(url))
                    query_params = urllib.parse.parse_qs(parsed_url[4])
                    
                    for param in query_params:
                        query_params[param] = [payload]
                    
                    parsed_url[4] = urllib.parse.urlencode(query_params, doseq=True)
                    test_url = urllib.parse.urlunparse(parsed_url)
                    
                    response = requests.get(test_url, timeout=10)
                    return payload in response.text, test_url
                else:
                    test_url = url.replace('=', f'={payload}')
                    cmd = f"curl -s '{test_url}' | grep -q '{payload}'"
                    is_vulnerable = subprocess.run(cmd, shell=True).returncode == 0
                    return is_vulnerable, test_url
                
            except Exception as e:
                return False, url

        payloads = load_payloads()
        print(f"{self.BOLD_BLUE}Loaded {len(payloads)} XSS payloads{Style.RESET_ALL}")

        vulnerable_urls = []
        with open(input_file) as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"{self.BOLD_BLUE}Testing {len(urls)} URLs for XSS vulnerabilities...⌛️{Style.RESET_ALL}")

        max_workers = 10 if platform.system() == 'Windows' else 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for url in urls:
                for payload in payloads:
                    futures.append(executor.submit(test_xss, url, payload))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    is_vulnerable, test_url = future.result()
                    if is_vulnerable:
                        vulnerable_urls.append(test_url)
                        print(f"{self.GREEN}Found XSS: {test_url}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{self.RED}Error during XSS test: {str(e)}{Style.RESET_ALL}")

        output_file = os.path.join("recon_output", f"{self.domain_name}-xss-vulnerable.txt")
        with open(output_file, 'w') as f:
            for url in sorted(set(vulnerable_urls)):
                f.write(f"{url}\n")

        print(f"{self.BOLD_BLUE}XSS testing complete:{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Total URLs tested: {len(urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Vulnerable URLs found: {len(vulnerable_urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Results saved to {output_file}{Style.RESET_ALL}")

        self.last_completed_option = 8

    def dedupe_urls(self):
        if not self.domain_name:
            print(f"{self.RED}Domain name not set. Please use option 2 first.{Style.RESET_ALL}")
            return

        print(f"{self.BOLD_WHITE}Select file to deduplicate:{Style.RESET_ALL}")
        print("1. XSS Candidates")
        print("2. Parameters file")
        
        try:
            choice = int(input("Enter your choice [1-2]: "))
            if choice == 1:
                input_file = os.path.join("recon_output", f"{self.domain_name}-xss-candidates.txt")
                output_suffix = "deduped-xss-candidates.txt"
            elif choice == 2:
                input_file = os.path.join("recon_output", f"{self.domain_name}-parameters.txt")
                output_suffix = "deduped-parameters.txt"
            else:
                print(f"{self.RED}Invalid choice{Style.RESET_ALL}")
                return
        except ValueError:
            print(f"{self.RED}Please enter a valid number{Style.RESET_ALL}")
            return

        if not os.path.exists(input_file):
            print(f"{self.RED}Input file not found. Please run previous steps first.{Style.RESET_ALL}")
            return

        print(f"{self.BOLD_WHITE}Performing advanced URL deduplication for {self.domain_name}{Style.RESET_ALL}")

        def parse_url_components(url):
            parsed = urllib.parse.urlparse(url)
            path = parsed.path.rstrip('/')
            params = urllib.parse.parse_qs(parsed.query)
            return path, params

        def get_pattern_signature(url):
            parsed = urllib.parse.urlparse(url)
            path_parts = parsed.path.split('/')
            
            # Replace sequences of numbers or letters with placeholders
            pattern_parts = []
            for part in path_parts:
                # Handle product IDs (like WA200002506)
                part = re.sub(r'[A-Z]{2}\d{9}', '{PRODUCT_ID}', part)
                # Handle any alphanumeric sequences
                part = re.sub(r'[A-Za-z0-9]{6,}', '{ID}', part)
                # Handle numeric sequences
                part = re.sub(r'\d+', '{NUM}', part)
                pattern_parts.append(part)
            
            pattern_path = '/'.join(pattern_parts)
            
            # Create pattern for query parameters
            query_params = sorted(urllib.parse.parse_qs(parsed.query).keys())
            
            return f"{parsed.netloc}{pattern_path}", tuple(query_params)

        def is_more_feature_rich(url1_params, url2_params):
            return all(param in url1_params for param in url2_params)

        url_groups = {}
        pattern_groups = {}
        
        with open(input_file) as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"{self.BOLD_BLUE}Processing {len(urls)} URLs...⌛️{Style.RESET_ALL}")

        # First group by patterns
        for url in urls:
            pattern_sig, params = get_pattern_signature(url)
            if pattern_sig not in pattern_groups:
                pattern_groups[pattern_sig] = []
            pattern_groups[pattern_sig].append(url)

        # Then process each pattern group
        deduped_urls = []
        for pattern, pattern_urls in pattern_groups.items():
            # If there's only one URL in the pattern group, keep it
            if len(pattern_urls) == 1:
                deduped_urls.extend(pattern_urls)
                continue
                
            # Group by path for parameter comparison
            path_groups = {}
            for url in pattern_urls:
                path, params = parse_url_components(url)
                if path not in path_groups:
                    path_groups[path] = []
                path_groups[path].append((url, params))
            
            # Select best URL from each path group
            for path_urls in path_groups.values():
                best_url = path_urls[0][0]
                best_params = path_urls[0][1]
                
                for url, params in path_urls[1:]:
                    if len(params) > len(best_params) or (len(params) == len(best_params) and len(url) < len(best_url)):
                        if is_more_feature_rich(params, best_params):
                            best_url = url
                            best_params = params
                
                deduped_urls.append(best_url)

        output_file = os.path.join("recon_output", f"{self.domain_name}-{output_suffix}")
        with open(output_file, 'w') as f:
            for url in sorted(set(deduped_urls)):
                f.write(f"{url}\n")

        print(f"{self.GREEN}Deduplication complete:{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Original URLs: {len(urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_WHITE}Deduplicated URLs: {len(deduped_urls)}{Style.RESET_ALL}")
        print(f"{self.BOLD_BLUE}Results saved to {output_file}{Style.RESET_ALL}")

        self.last_completed_option = 9



if __name__ == "__main__":
    recon = XssRecon()
    recon.run()

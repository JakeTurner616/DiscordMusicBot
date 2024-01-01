# This script can be used to download the latest musicbrainz picard binary from the download page and verify its contents via md5 hash.
import hashlib
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests
import subprocess  # Added for subprocess.run

file_name_exe = "MusicBrainz-Picard-latest.exe"
file_name_dmg = "MusicBrainz-Picard-latest.dmg"

# Check if the file exists in the current working directory
if os.path.exists(file_name_exe) or os.path.exists(file_name_dmg):
    print(f"The file '{file_name_exe}' or '{file_name_dmg}' exists. Exiting the script.")
    quit()

# Check if the current OS is Linux-based
if platform.system().lower() == 'linux':
    # Check if MusicBrainz is installed via snap
    try:
        subprocess.run(["snap", "list", "musicbrainz-picard"], check=True)
        print("MusicBrainz is installed via snap. Exiting the script.")
        quit()
    except subprocess.CalledProcessError:
        pass  # Snap package not installed

    # Check if MusicBrainz is installed via flatpak
    try:
        subprocess.run(["flatpak", "list", "musicbrainz-picard"], check=True)
        print("MusicBrainz is installed via flatpak. Exiting the script.")
        quit()
    except subprocess.CalledProcessError:
        pass  # Flatpak package not installed

# Continue with the rest of the script if not on Linux or if neither the file nor the packages are found
print("MusicBrainz is not installed or the files are not present. Continuing with the script.")


# URL of the MusicBrainz Picard download page
url = "https://picard.musicbrainz.org/downloads/"

# Check if the operating system is Windows, macOS, or Linux
current_os = platform.system()
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless=new")

# Initialize the webdriver
driver = webdriver.Chrome(options=chrome_options)

# Open the URL in the browser
driver.get(url)

try:
    if current_os == "Windows":
        version_selector = '#windows > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(4) > a:nth-child(1)'
        hash_xpath = '/html/body/div[3]/ul/li[1]/div/table/tbody/tr[2]/td[2]'
    elif current_os == "Darwin":  # macOS
        version_selector = '#mac > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4) > a:nth-child(1)'
        hash_xpath = '/html/body/div[3]/ul/li[2]/div/table/tbody/tr[1]/td[2]'
    elif current_os == "Linux":
        # Assuming Linux users have the choice between Snap and Flatpak
        install_choice = input("Enter 'snap' or 'flatpak' to choose the installation method: ")
        if install_choice not in ["snap", "flatpak"]:
            print(f"Installation method {install_choice} not supported.")
            quit()

        version_selector = f'#{install_choice} > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4) > a:nth-child(1)'
        hash_selector = f'#{install_choice} > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(2)'
    else:
        print(f"Operating system {current_os} not supported.")
        quit()

    version_link = driver.find_element(By.CSS_SELECTOR, version_selector)
    download_url = version_link.get_attribute("href")

    # Print the direct download link
    print(f"Direct Download Link: {download_url}")

    # Find the MD5 hash using XPath
    md5_hash_element = driver.find_element(By.XPATH, hash_xpath)
    expected_md5_hash = md5_hash_element.text

    # Print the expected MD5 hash
    print(f"Expected MD5 Hash: {expected_md5_hash}")


finally:
    # Close the webdriver
    driver.quit()

# Use requests to download the file
response = requests.get(download_url)

if response.status_code == 200:
    # Save the file to the desired location
    if current_os == "Linux":
        install_command = f"{install_choice} install --classic {download_url}"
        subprocess.run(install_command, shell=True)
        print(f"Installed MusicBrainz Picard using {install_choice}.")
    else:
        file_extension = ".exe" if current_os == "Windows" else ".dmg"
        new_file_path = os.path.join(os.getcwd(), f'MusicBrainz-Picard-latest{file_extension}')

        # Check if the file already exists
        if os.path.exists(new_file_path):
            print(f"The file '{new_file_path}' already exists. Exiting.")
            quit()
        
        with open(new_file_path, 'wb') as file:
            file.write(response.content)

        print(f"Downloaded: {new_file_path}")

        # Calculate MD5 hash of the downloaded file
        print("Calculating and comparing the MD5 hash. This could take a while.")
        with open(new_file_path, 'rb') as file:
            md5_hash = hashlib.md5()
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                md5_hash.update(chunk)
                print(f"Processed {file.tell()} bytes...")  # Debug statement to show progress

        # Print the calculated and expected MD5 hashes for debugging
        print(f"Calculated MD5 Hash: {md5_hash.hexdigest()}")
        print(f"Expected MD5 Hash  : {expected_md5_hash}")

        # Compare the calculated hash with the expected hash
        if md5_hash.hexdigest() == expected_md5_hash:
            print("MD5 hash verification successful.")
        else:
            print("MD5 hash verification failed.")
          
else:
    print(f"Failed to download. Status code: {response.status_code}")

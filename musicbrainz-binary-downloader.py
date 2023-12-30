# This script can be used to download the latest musicbrainz picard binary from the download page and verify its contents via md5 hash.
import hashlib
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests
import subprocess  # Added for subprocess.run

# URL of the MusicBrainz Picard download page
url = "https://picard.musicbrainz.org/downloads/"

# Check if the operating system is Windows, macOS, or Linux
current_os = platform.system()

# Initialize the webdriver
driver = webdriver.Chrome()

# Open the URL in the browser
driver.get(url)

try:
    if current_os == "Windows":
        version_selector = '#windows > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(4) > a:nth-child(1)'
        hash_selector = '#windows > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(2)'
    elif current_os == "Darwin":  # macOS
        version_selector = '#mac > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4) > a:nth-child(1)'
        hash_selector = '#mac > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(2)'
    elif current_os == "Linux":
        # Assuming Linux users have the choice between Snap and Flatpak
        install_choice = input("Enter 'snap' or 'flatpak' to choose the installation method: ")
        if install_choice not in ["snap", "flatpak"]:
            print(f"Installation method {install_choice} not supported.")
            exit()

        version_selector = f'#{install_choice} > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4) > a:nth-child(1)'
        hash_selector = f'#{install_choice} > div:nth-child(2) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(2)'
    else:
        print(f"Operating system {current_os} not supported.")
        exit()

    version_link = driver.find_element(By.CSS_SELECTOR, version_selector)
    download_url = version_link.get_attribute("href")

    # Print the direct download link
    print(f"Direct Download Link: {download_url}")

    # Find the MD5 hash using CSS selector
    md5_hash_element = driver.find_element(By.CSS_SELECTOR, hash_selector)
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
        # Compare the calculated hash with the expected hash
        if md5_hash.hexdigest() == expected_md5_hash:
            print("MD5 hash verification successful.")
        else:
            print("MD5 hash verification failed.")
          
else:
    print(f"Failed to download. Status code: {response.status_code}")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def get_product_image_urls(driver, product_url):
    driver.get(product_url)
    try:
        # Wait for the card name to be present
        card_name = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product-details__name[data-testid="lblProductDetailsProductName"]'))
        ).text
        print(f"Card Name: {card_name}")

        # Wait for the images to be present
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'img'))
        )
        image_elements = driver.find_elements(By.TAG_NAME, 'img')
        print(f"Found {len(image_elements)} image elements")

        # Filter the image elements to find the correct one and adjust the URL
        card_image_url = next(
            (img.get_attribute('src') for img in image_elements if 'https://tcgplayer-cdn.tcgplayer.com' in img.get_attribute('src') and img.get_attribute('src').endswith('.jpg')), None
        )

        if card_image_url:
            # Change the dimensions to 1000x1000.jpg
            card_image_url = card_image_url.replace('_200x200.jpg', '_1000x1000.jpg')

        print(f"Card Image URL: {card_image_url}")
        return card_name, card_image_url
    except TimeoutException:
        print(f"Failed to retrieve image or name for {product_url}")
        return None, None
    except Exception as e:
        print(f"An error occurred while retrieving image or name for {product_url}: {e}")
        return None, None

# Example usage
driver = webdriver.Chrome()  # Make sure to have the appropriate driver installed and in your PATH
product_url = 'https://www.tcgplayer.com/product/478741/magic-commander-phyrexia-all-will-be-one-otharri-suns-glory-extended-art?Printing=Normal&Condition=Near+Mint&Language=English&page=1'
get_product_image_urls(driver, product_url)
driver.quit()

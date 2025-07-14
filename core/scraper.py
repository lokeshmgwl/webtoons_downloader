# core/scraper.py

import requests
from bs4 import BeautifulSoup
from utils.config import SEARCH_URL
from utils.logger import logger

def search_manga(query):
    """Search for a manga on Webtoons across all result pages."""
    results = []
    page = 1
    while True:
        search_url = SEARCH_URL.format(query=query, page=page)
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            webtoon_list = soup.find("ul", class_="webtoon_list")
            
            if not webtoon_list:
                logger.info(f"No more search results found for '{query}' on page {page}.")
                break

            new_results_found = False
            for item in webtoon_list.find_all("li"):
                new_results_found = True
                link_element = item.find("a")
                title_element = item.find("strong", class_="title")
                author_element = item.find("div", class_="author")
                views_element = item.find("div", class_="view_count")
                
                if title_element and link_element and author_element and views_element:
                    title = title_element.get_text(strip=True)
                    url = link_element["href"]
                    author = author_element.get_text(strip=True)
                    views = views_element.get_text(strip=True).split(' ')[0]
                    results.append({"title": title, "author": author, "views": views, "url": url})
            
            if not new_results_found:
                logger.info(f"No more search results found for '{query}' on page {page}.")
                break

            logger.info(f"Found {len(results)} results so far for '{query}' after searching page {page}.")
            page += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Error during search request on page {page}: {e}")
            break
            
    logger.info(f"Found a total of {len(results)} results for '{query}'.")
    return results

def scrape_episodes(manga_url):
    """Scrape all episodes from a manga series page using the brute-force method."""
    episodes = []
    scraped_episode_numbers = set()
    current_url = manga_url.split('&page=')[0]
    page = 1

    while True:
        try:
            paginated_url = f"{current_url}&page={page}"
            response = requests.get(paginated_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            episode_list = soup.find("ul", id="_listUl")
            if not episode_list:
                logger.info("Could not find episode list. Assuming end of pages.")
                break

            episode_items = episode_list.find_all("li", class_="_episodeItem")
            if not episode_items:
                logger.info(f"No more episodes found on page {page}. Concluding scrape.")
                break

            new_episodes_found = False
            for item in episode_items:
                episode_number = int(item["data-episode-no"])
                if episode_number not in scraped_episode_numbers:
                    new_episodes_found = True
                    scraped_episode_numbers.add(episode_number)
                    episode_link = item.find("a")
                    episode_title_span = item.find("span", class_="subj")
                    if episode_link and episode_title_span:
                        episode_title = episode_title_span.get_text(strip=True)
                        episodes.append({
                            "title": episode_title,
                            "url": episode_link["href"],
                            "number": episode_number
                        })
            
            if not new_episodes_found:
                logger.info(f"No new episodes found on page {page}. Concluding scrape.")
                break

            logger.info(f"Scraped page {page} of episodes.")
            page += 1
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping episodes from {paginated_url}: {e}")
            break
            
    logger.info(f"Found {len(episodes)} total episodes.")
    return sorted(episodes, key=lambda x: x['number'])

def scrape_chapter_images(episode_url):
    """Scrape all image URLs from a single episode page."""
    try:
        response = requests.get(episode_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        image_urls = []
        image_list_container = soup.find("div", id="_imageList")
        if not image_list_container:
            logger.warning(f"Could not find image list container in {episode_url}")
            return []

        img_tags = image_list_container.find_all("img", class_="_images")
        for img in img_tags:
            # The image URL is in the 'data-url' attribute
            if img.has_attr("data-url"):
                image_urls.append(img["data-url"])
        
        logger.info(f"Found {len(image_urls)} images in {episode_url}")
        return image_urls

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping chapter images from {episode_url}: {e}")
        return []

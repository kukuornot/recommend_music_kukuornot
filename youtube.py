from youtubesearchpython import VideosSearch

def get_youtube_link(title, artist):
    query = f"{title} {artist} official audio"
    search = VideosSearch(query, limit=1)
    result = search.result()

    if result["result"]:
        return result["result"][0]["link"]
    return None

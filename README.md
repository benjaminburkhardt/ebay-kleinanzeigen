# Ebay-Kleinanzeigen notifier

This is very simple Telegram bot checking new ads on [Ebay-Kleinanzeigen.de](https://www.ebay-kleinanzeigen.de/stadt/muenchen/).

It accepts just a link to a page with the search results (i.e. `https://www.ebay-kleinanzeigen.de/s-pc-zubehoer-software/grafikkarten/81825/anzeige:angebote/preis:100:500/c225l16390r150+pc_zubehoer_software.art_s:grafikkarten`) and then starts monitoring this page (by default every 15 minutes).

When some new ad appears, you'll be notified. 
 
 # Documentation
 
 ## Algorithm

No rocket science here, I made it just for myself and the simplest approach worked well. Bot remembers the topmost
item in the list for the current `chat_id` and during subsequent checks prints all the ads until the last remembered item
is met. Obviously, this will cause a full update if the last item disappeared, but during ~2 weeks of usage I haven't really noticed 
such a case.
 
 ### Requirements
Python 3.6+ and Docker (preferrably)
 
 ### Manual

- Install requirements
- Get Telegram TOKEN
- Run bot in screen so you can detach from it:
-     screen -d -m python3 main.py --token <your token> --opt_minutes <minutes to refresh>


Commands for running in docker:

    git pull
    docker-compose build
    docker-compose up -d
    
### Public availability and terms of usage

NOTE: I do not plan to host this bot publicly available (in contrast with [Munich Termin Notifier bot](https://github.com/okainov/munich-scripts)) because
it seems to have much more personalized queries and there is no point in analyzing the data in a single place. 

WARNING: Use this script on your own risk since usage may violate eBay Classified terms of usage. 

# Future improvements and contributions

Contributions welcome! Feel free to create Pull Request and/or propose ideas in [Issues](https://github.com/okainov/ebay-kleinanzeigen/issues)
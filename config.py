# config.py:

### bot token 
token = "bot token"
# role format needs to be specific
# Factions: Grineer, Infested, Corpus, Orokin
# Types: Grineer Defense, Corpus Survival..
# Nodes: Sechura, Helene, Hydron...
## change server id to yours and invite the bot if you want role pings
## make a webhook in the channel you want arbitrations to be posted and use the url
## this DOES support multiple servers if you want to use it in that manner
## leave the values blank if you do not want them used
servers = [
{
    "name": "Example",
    "serverid": 000000000000000000,
    "arbywebhook": "arbitration webhook url",
    "barowebhook": "baro webhook url",
    "giftinvasionswebhook": "gift/invasions webhook url",
    "redtextwebhook": "redtext webhook url"
}
]

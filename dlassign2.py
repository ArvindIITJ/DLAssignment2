#!/usr/bin/env python
# coding: utf-8

# # Lux AI Season 1 Python Tutorial Notebook
# 
# Welcome to Lux AI Season 1!
# 
# This notebook is the basic setup to use Jupyter Notebooks and the `kaggle-environments` package to develop your bot. If you plan to not use Jupyter Notebooks or any other programming language, please see our [Github](https://github.com/Lux-AI-Challenge/Lux-Design-2021). The following are some important links!
# 
# - Competition Page: https://www.kaggle.com/c/lux-ai-2021/
# 
# - Online Visualizer: https://2021vis.lux-ai.org/
# 
# - Specifications: https://www.lux-ai.org/specs-2021
# 
# - Github: https://github.com/Lux-AI-Challenge/Lux-Design-2021
# 
# - Bot API: https://github.com/Lux-AI-Challenge/Lux-Design-2021/tree/master/kits
# 
# And if you haven't done so already, we **highly recommend** you join our Discord server at https://discord.gg/aWJt3UAcgn or at the minimum follow the kaggle forums at https://www.kaggle.com/c/lux-ai-2021/discussion. We post important announcements there such as changes to rules, events, and opportunities from our sponsors!
# 
# Now let's get started!
# 
# ## Prerequisites
# 
# We assume that you have a basic knowledge of Python and programming. It's okay if you don't know the game specifications yet! Feel free to always refer back to https://www.lux-ai.org/specs-2021.
# 
# ## Basic Setup
# 
# First thing to verify is that you have **Node.js v12 or above**. The engine for the competition runs on Node.js (for many good reasons including an awesome visualizer) and thus it is required. You can download it [here](https://nodejs.org/en/download/). You can then verify you have the appropriate version by running
# 

# In[1]:


get_ipython().system('node --version')


# We will also need Kaggle Environments

# In[2]:


get_ipython().system('pip install kaggle-environments -U')


# Next, we have to import the `make` function from the `kaggle_environments` package

# In[3]:


from kaggle_environments import make


# The `make` function is used to create environments that can then run the game given agents. Agents refer to programmed bots that play the game given observations of the game itself. 
# 
# In addition to making the environment, you may also pass in special configurations such as the number of episode steps (capped at 361) and the seed.
# 
# Now lets create our environment using `make` and watch a Episode! (We will be using the seed 562124210 because it's fun)

# In[4]:


# create the environment. You can also specify configurations for seed and loglevel as shown below. If not specified, a random seed is chosen. 
# loglevel default is 0. 
# 1 is for errors, 2 is for match warnings such as units colliding, invalid commands (recommended)
# 3 for info level, and 4 for everything (not recommended)
# set annotations True so annotation commands are drawn on visualizer
# set debug to True so print statements get shown
env = make("lux_ai_2021", configuration={"seed": 562124210, "loglevel": 2, "annotations": True}, debug=True)


# In[5]:


# run a match between two simple agents, which are the agents we will walk you through on how to build!
steps = env.run(["simple_agent", "simple_agent"])
# if you are viewing this outside of the interactive jupyter notebook / kaggle notebooks mode, this may look cutoff
# render the game, feel free to change width and height to your liking. We recommend keeping them as large as possible for better quality.
# you may also want to close the output of this render cell or else the notebook might get laggy
env.render(mode="ipython", width=1200, height=800)


# Ok so woah, what just happened? We just ran a match, that's what :)
# 
# There's a number of quality of life features in the visualizer, which you can also find embedded on the kaggle competition page when watching replays or on the online visualizer when using replay files. 
# 
# If you find this replay viewer slow, you can also download a local copy of this replay viewer in addition to lowering the graphics quality, see https://github.com/Lux-AI-Challenge/LuxViewer2021 for instructions.
# 
# At this point, we recommend reading the [game specifications](https://www.lux-ai.org/specs-2021) a bit more to understand how to build a bot that tries to win the game.

# ## Building from Scratch
# 
# The following bit of code is all you need for a empty agent that does nothing

# In[6]:


# run this if using kaggle notebooks
get_ipython().system('cp -r ../input/lux-ai-2021/* .')
# if working locally, download the `simple/lux` folder from here https://github.com/Lux-AI-Challenge/Lux-Design-2021/tree/master/kits/python
# and we recommend following instructions in there for local development with python bots


# In[7]:


# for kaggle-environments
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
import math
import sys

# we declare this global game_state object so that state persists across turns so we do not need to reinitialize it all the time
game_state = None
def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    
    # add debug statements like so!
    if game_state.turn == 0:
        print("Agent is running!", file=sys.stderr)
        actions.append(annotate.circle(0, 0))
    return actions


# Unfortunately it's not that easy. This agent will eventually lose and all units and cities will fall to darkness! We will need to write something to help the agent first find resources and then collect them.
# 
# Let's first run a game with our empty agent, which will populate the `game_state` variable and we can now work with it and look into how we would proceed with finding resources.

# In[8]:


steps = env.run([agent, "simple_agent"])


# In[9]:


# this snippet finds all resources stored on the map and puts them into a list so we can search over them
def find_resources(game_state):
    resource_tiles: list[Cell] = []
    width, height = game_state.map_width, game_state.map_height
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles

# the next snippet finds the closest resources that we can mine given position on a map
def find_closest_resources(pos, player, resource_tiles):
    closest_dist = math.inf
    closest_resource_tile = None
    for resource_tile in resource_tiles:
        # we skip over resources that we can't mine due to not having researched them
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
        dist = resource_tile.pos.distance_to(pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = resource_tile
    return closest_resource_tile


# In[10]:


# lets look at some of the resources found
resource_tiles = find_resources(game_state)
cell = resource_tiles[0]
print("Cell at", cell.pos, "has")
print(cell.resource.type, cell.resource.amount)


# In[11]:


# lets see if we do find some close resources
cell = find_closest_resources(Position(1, 1), game_state.players[0], resource_tiles)
print("Closest resource at", cell.pos, "has")
print(cell.resource.type, cell.resource.amount)


# Ok now that we have code to find resources closest to a given position, lets code our agent to use this and tell its units to go to the closest resource and mine them! We can copy our empty agent code and add a loop that loops over all our units and make them move towards the resources

# In[12]:


game_state = None
def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    
    # add debug statements like so!
    if game_state.turn == 0:
        print("Agent is running!", file=sys.stderr)

    resource_tiles = find_resources(game_state)
    
    for unit in player.units:
        # if the unit is a worker (can mine resources) and can perform an action this turn
        if unit.is_worker() and unit.can_act():
            # we want to mine only if there is space left in the worker's cargo
            if unit.get_cargo_space_left() > 0:
                # find the closest resource if it exists to this unit
                closest_resource_tile = find_closest_resources(unit.pos, player, resource_tiles)
                if closest_resource_tile is not None:
                    # create a move action to move this unit in the direction of the closest resource tile and add to our actions list
                    action = unit.move(unit.pos.direction_to(closest_resource_tile.pos))
                    actions.append(action)
    
    return actions


# Now lets watch a match where our agent plays against a sample agent and see if it moves towards the resources! We can then verify by watching the replay and seeing our orange unit (team 0) move towards a nearby forest and collect wood

# In[13]:


env = make("lux_ai_2021", configuration={"seed": 562124210, "loglevel": 2, "annotations": True}, debug=True)
steps = env.run([agent, "simple_agent"])
env.render(mode="ipython", width=1200, height=800)


# Ok now that our agent finds and collects resources but our citytile was consumed by darkness! What now? Well units can only carry so much resources before they can't collect anymore. And to keep your City alive, you must move your unit on top of any CityTile that is in that City. (Recall that a City is composed of connected CityTiles)

# In[14]:


# snippet to find the closest city tile to a position
def find_closest_city_tile(pos, player):
    closest_city_tile = None
    if len(player.cities) > 0:
        closest_dist = math.inf
        # the cities are stored as a dictionary mapping city id to the city object, which has a citytiles field that
        # contains the information of all citytiles in that city
        for k, city in player.cities.items():
            for city_tile in city.citytiles:
                dist = city_tile.pos.distance_to(pos)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_city_tile = city_tile
    return closest_city_tile


# With this function, we are ready to start surviving the nights! The code below rewrites our agent to now have units who have full cargos to head towards the closest citytile and drop off their resources to fuel the city.

# In[15]:


game_state = None
def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    
    # add debug statements like so!
    if game_state.turn == 0:
        print("Agent is running!", file=sys.stderr)

    resource_tiles = find_resources(game_state)
    
    for unit in player.units:
        # if the unit is a worker (can mine resources) and can perform an action this turn
        if unit.is_worker() and unit.can_act():
            # we want to mine only if there is space left in the worker's cargo
            if unit.get_cargo_space_left() > 0:
                # find the closest resource if it exists to this unit
                closest_resource_tile = find_closest_resources(unit.pos, player, resource_tiles)
                if closest_resource_tile is not None:
                    # create a move action to move this unit in the direction of the closest resource tile and add to our actions list
                    action = unit.move(unit.pos.direction_to(closest_resource_tile.pos))
                    actions.append(action)
            else:
                # find the closest citytile and move the unit towards it to drop resources to a citytile to fuel the city
                closest_city_tile = find_closest_city_tile(unit.pos, player)
                if closest_city_tile is not None:
                    # create a move action to move this unit in the direction of the closest resource tile and add to our actions list
                    action = unit.move(unit.pos.direction_to(closest_city_tile.pos))
                    actions.append(action)
    
    return actions


# In[16]:


env = make("lux_ai_2021", configuration={"seed": 562124210, "loglevel": 2, "annotations": True}, debug=True)
steps = env.run([agent, "simple_agent"])
env.render(mode="ipython", width=1200, height=800)


# We have something that survives! We are now ready to submit something to the leaderboard. The code below compiles all we have built so far into one file that you can then submit to the competition leaderboard

# In[17]:


get_ipython().run_cell_magic('writefile', 'agent.py', '# for kaggle-environments\nfrom lux.game import Game\nfrom lux.game_map import Cell, RESOURCE_TYPES\nfrom lux.constants import Constants\nfrom lux.game_constants import GAME_CONSTANTS\nfrom lux import annotate\nimport math\nimport sys\n\n### Define helper functions\n\n# this snippet finds all resources stored on the map and puts them into a list so we can search over them\ndef find_resources(game_state):\n    resource_tiles: list[Cell] = []\n    width, height = game_state.map_width, game_state.map_height\n    for y in range(height):\n        for x in range(width):\n            cell = game_state.map.get_cell(x, y)\n            if cell.has_resource():\n                resource_tiles.append(cell)\n    return resource_tiles\n\n# the next snippet finds the closest resources that we can mine given position on a map\ndef find_closest_resources(pos, player, resource_tiles):\n    closest_dist = math.inf\n    closest_resource_tile = None\n    for resource_tile in resource_tiles:\n        # we skip over resources that we can\'t mine due to not having researched them\n        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue\n        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue\n        dist = resource_tile.pos.distance_to(pos)\n        if dist < closest_dist:\n            closest_dist = dist\n            closest_resource_tile = resource_tile\n    return closest_resource_tile\n\ndef find_closest_city_tile(pos, player):\n    closest_city_tile = None\n    if len(player.cities) > 0:\n        closest_dist = math.inf\n        # the cities are stored as a dictionary mapping city id to the city object, which has a citytiles field that\n        # contains the information of all citytiles in that city\n        for k, city in player.cities.items():\n            for city_tile in city.citytiles:\n                dist = city_tile.pos.distance_to(pos)\n                if dist < closest_dist:\n                    closest_dist = dist\n                    closest_city_tile = city_tile\n    return closest_city_tile\n\ngame_state = None\ndef agent(observation, configuration):\n    global game_state\n\n    ### Do not edit ###\n    if observation["step"] == 0:\n        game_state = Game()\n        game_state._initialize(observation["updates"])\n        game_state._update(observation["updates"][2:])\n        game_state.id = observation.player\n    else:\n        game_state._update(observation["updates"])\n    \n    actions = []\n\n    ### AI Code goes down here! ### \n    player = game_state.players[observation.player]\n    opponent = game_state.players[(observation.player + 1) % 2]\n    width, height = game_state.map.width, game_state.map.height\n\n    resource_tiles = find_resources(game_state)\n    \n    for unit in player.units:\n        # if the unit is a worker (can mine resources) and can perform an action this turn\n        if unit.is_worker() and unit.can_act():\n            # we want to mine only if there is space left in the worker\'s cargo\n            if unit.get_cargo_space_left() > 0:\n                # find the closest resource if it exists to this unit\n                closest_resource_tile = find_closest_resources(unit.pos, player, resource_tiles)\n                if closest_resource_tile is not None:\n                    # create a move action to move this unit in the direction of the closest resource tile and add to our actions list\n                    action = unit.move(unit.pos.direction_to(closest_resource_tile.pos))\n                    actions.append(action)\n            else:\n                # find the closest citytile and move the unit towards it to drop resources to a citytile to fuel the city\n                closest_city_tile = find_closest_city_tile(unit.pos, player)\n                if closest_city_tile is not None:\n                    # create a move action to move this unit in the direction of the closest resource tile and add to our actions list\n                    action = unit.move(unit.pos.direction_to(closest_city_tile.pos))\n                    actions.append(action)\n    \n    return actions')


# ## Create a submission
# Now we need to create a .tar.gz file with main.py (and agent.py) at the top level. We can then upload this!

# In[18]:


get_ipython().system('tar -czf submission.tar.gz *')


# ## Submit
# Now open the /kaggle/working folder and find submission.tar.gz, download that file, navigate to the "MySubmissions" tab in https://www.kaggle.com/c/lux-ai-2021/ and upload your submission! It should play a validation match against itself and once it succeeds it will be automatically matched against other players' submissions. Newer submissions will be prioritized for games over older ones. Your team is limited in the number of succesful submissions per day so we highly recommend testing your bot locally before submitting.

# ## CLI Tool
# 
# There's a separate CLI tool that can also be used to run matches. It's recommended for Jupyter Notebook users to stick with just this notebook, and all other users including python users to follow the instructions on https://github.com/Lux-AI-Challenge/Lux-Design-2021
# 
# The other benefit however of using the CLI tool is that it generates much smaller, "stateless" replays and also lets you run a mini leaderboard on multiple bots ranked by various ranking algorithms

# ## Additional things to check out
# 
# Make sure you check out the Bot API at https://github.com/Lux-AI-Challenge/Lux-Design-2021/tree/master/kits
# 
# This documents what you can do using the starter kit files in addition to telling you how to use the annotation debug commands that let you annotate directly on a replay (draw lines, circle things etc.)
# 
# You can also run the following below to save a episode to a JSON replay file. These are the same as what is shown on the leaderbaord and you can upload the replay files to the online replay viewer https://2021vis.lux-ai.org/
# 
# 
# For a local (faster) version of the replay viewer, follow installation instructions here https://github.com/Lux-AI-Challenge/Lux-Viewer-2021

# In[19]:


import json
replay = env.toJSON()
with open("replay.json", "w") as f:
    json.dump(replay, f)


# ## Suggestions / Strategies
# 
# There are a lot of places that could be improved with the agent we have in this tutorial notebook. Here are some!
# 
# - Using the build city action to build new cities and thus build new units
# - Having cities perform research each turn to unlock new resources
# - Writing collision-free code that lets units move smoothly around and through each other when navigating to targets
# - Mining resources near your opponent's citytiles so they have less easy access to resources
# - Using carts to deliver resources from far away clusters of wood, coal, uranium to a city in need
# - Sending worker units over to the opponent's roads and pillaging them to slow down their agent
# - Optimizing over how much to mine out of forests before letting them regrow so you can build more cities and get sustainable fuel

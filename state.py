from aiogram.fsm.state import State, StatesGroup

class AnimeAdd(StatesGroup):
    name = State()
    code = State()
    episodes = State()
    video = State()

class EpisodeAdd(StatesGroup):
    anime_id = State()
    episode_number = State()
    video = State()    


class Broadcast(StatesGroup):
    media = State()
    text = State()

class AddChannel(StatesGroup):
    link = State()    

from scripts.manager import GameManager, Process, logging, get_config_value


def main():
    import pygame as pg
    GameManager().run()


if __name__ == '__main__':
    game = GameManager()
    # Debug
    if get_config_value('game', 'duplicate_window'):
        logging.info('Create duplicate window')
        Process(target=main, daemon=True).start()
    game.run()
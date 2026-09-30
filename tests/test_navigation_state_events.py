"""Menu state follows explicit transitions, never incidental format names."""
import unittest

from state.state_machine import BotState, PlayerLogStateTracker, get_state_from_playerlog


class NavigationStateEventTests(unittest.TestCase):
    def test_format_and_deck_names_do_not_invent_a_page(self):
        for text in ('{"deckName":"Historic My Decks"}', 'Find Match',
                     '{"formats":["Historic", "Standard"]}'):
            with self.subTest(text=text):
                self.assertEqual(get_state_from_playerlog(text), BotState.UNKNOWN)

    def test_mainnav_supersedes_old_scene_and_format_payload(self):
        text = '"toSceneName":"Store"\nHistoric\nMainNav load in\nMy Decks'
        self.assertEqual(get_state_from_playerlog(text), BotState.HOME)

    def test_newer_scene_supersedes_mainnav(self):
        self.assertEqual(get_state_from_playerlog(
            'MainNav load in\n"toSceneName":"Matchmaking"'), BotState.FIND_MATCH)

    def test_game_entry_supersedes_home(self):
        self.assertEqual(get_state_from_playerlog(
            'MainNav load in\nGREMessageType_GameStateMessage'), BotState.IN_GAME)

    def test_completion_does_not_reuse_an_old_home_or_game(self):
        self.assertEqual(get_state_from_playerlog(
            '"toSceneName":"Home"\nGREMessageType_GameStateMessage\n'
            'MatchGameRoomStateType_MatchCompleted'), BotState.UNKNOWN)

    def test_mainnav_after_completion_is_home(self):
        self.assertEqual(get_state_from_playerlog(
            'MatchGameRoomStateType_MatchCompleted\nMainNav load in'), BotState.HOME)

    def test_unknown_loading_scene_invalidates_old_home(self):
        self.assertEqual(get_state_from_playerlog(
            'MainNav load in\n"toSceneName":"Loading"'), BotState.UNKNOWN)

    def test_historic_scene_is_not_generic_play_menu(self):
        self.assertEqual(get_state_from_playerlog(
            '"toSceneName":"HistoricPlay"'), BotState.HISTORIC)

    def test_tracker_keeps_transition_when_diagnostic_tail_rotates(self):
        tracker = PlayerLogStateTracker(max_lines=50)
        tracker.push_line('MainNav load in')
        for _ in range(60):
            tracker.push_line('{"deckName":"Historic"}')
        self.assertEqual(tracker.get_state(), BotState.HOME)

    def test_tracker_clears_state_on_completion_and_reenters_next_match(self):
        tracker = PlayerLogStateTracker()
        for line, expected in (
            ('MainNav load in', BotState.HOME),
            ('GREMessageType_GameStateMessage', BotState.IN_GAME),
            ('MatchGameRoomStateType_MatchCompleted', BotState.UNKNOWN),
            ('Historic', BotState.UNKNOWN),
            ('MainNav load in', BotState.HOME),
            ('GREMessageType_GameStateMessage', BotState.IN_GAME),
        ):
            tracker.push_line(line)
            self.assertEqual(tracker.get_state(), expected)

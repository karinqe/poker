import os.path
from nose.tools import assert_list_equal, assert_equal
from nose.tools import raises
from robopoker.entities import Card, CardException
import poker.state

PLAYER_NAME = "kari"
FILES = os.path.join("tests", "files")


class TestHoleParsing(object):
    def test_hole_cards(self):
        hole = "7D AC"
        hole_cards = [Card('7', 'D'), Card('A', 'C')]
        state = poker.state.State(PLAYER_NAME, hole, '', '')
        assert_list_equal(sorted(state.hole), sorted(hole_cards))

    @raises(poker.state.StateParseException)
    def test_no_hole_card__negative(self):
        poker.state.State(PLAYER_NAME, '', '', '')

    @raises(poker.state.StateParseException)
    def test_single_hole_card__negative(self):
        hole = "7D"
        poker.state.State(PLAYER_NAME, hole, '', '')

    @raises(poker.state.StateParseException)
    def test_3_hole_cards__negative(self):
        hole = "7D AC 8H"
        poker.state.State(PLAYER_NAME, hole, '', '')

    @raises(CardException)
    def test_invalid_hole_card__negative(self):
        hole = "7D 3B"
        poker.state.State(PLAYER_NAME, hole, '', '')


class TestActionParsing(object):
    def test_possible_actions(self):
        hole = "7D AC"
        actions = ["fold", "call", "raise"]
        state = poker.state.State(PLAYER_NAME, hole, '\n'.join(actions), '')
        assert_list_equal(sorted(actions), sorted(state.possible_actions))

    def test_ignore_unknown_actions(self):
        # If an unknown action is presented, don't raise anything - just put it
        # there. This is so that it doesn't start failing if the API is updated
        hole = "7D AC"
        actions = ["fold", "call", "raise", "whatever"]
        state = poker.state.State(PLAYER_NAME, hole, '\n'.join(actions), '')
        assert_list_equal(sorted(actions), sorted(state.possible_actions))

    def test_no_possible_actions(self):
        # ignore the case when no actions are possible
        hole = "7D AC"
        state = poker.state.State(PLAYER_NAME, hole, '', '')
        assert_list_equal([], state.possible_actions)


class TestStateParsing(object):
    hole = "7D AC"

    @classmethod
    def setup_class(cls):
        with open(os.path.join(FILES, "preflop.xml")) as f:
            cls.preflop_state = ''.join(f.readlines())
        with open(os.path.join(FILES, "flop.xml")) as f:
            cls.flop_state = ''.join(f.readlines())
        with open(os.path.join(FILES, "turn.xml")) as f:
            cls.turn_state = ''.join(f.readlines())
        with open(os.path.join(FILES, "river.xml")) as f:
            cls.river_state = ''.join(f.readlines())

    def test_empty_community_cards(self):
        state = poker.state.State(PLAYER_NAME, self.hole, '',
                                  self.preflop_state)
        assert_list_equal([], state.community)
        assert_equal('preflop', state.round)

    def test_flop_community_cards(self):
        community_cards = [Card('K', 'S'), Card('9', 'D'), Card('A', 'S')]
        state = poker.state.State(PLAYER_NAME, self.hole, '', self.flop_state)
        assert_equal(len(state.community), 3)
        assert_list_equal(community_cards, state.community)
        assert_equal('flop', state.round)

    def test_turn_community_cards(self):
        community_cards = [Card('K', 'S'), Card('9', 'D'), Card('A', 'S'),
                           Card('2', 'S')]
        state = poker.state.State(PLAYER_NAME, self.hole, '', self.turn_state)
        assert_equal(len(state.community), 4)
        assert_list_equal(sorted(community_cards), sorted(state.community))
        assert_equal('turn', state.round)

    def test_river_community_cards(self):
        community_cards = [Card('K', 'S'), Card('9', 'D'), Card('A', 'S'),
                           Card('2', 'S'), Card('Q', 'S')]
        state = poker.state.State(PLAYER_NAME, self.hole, '', self.river_state)
        assert_equal(len(state.community), 5)
        assert_list_equal(sorted(community_cards), sorted(state.community))
        assert_equal('river', state.round)

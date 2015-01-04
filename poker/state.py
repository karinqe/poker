import logging
import itertools
import pokereval.card
from pokereval.hand_evaluator import HandEvaluator
import xmltodict
import robopoker.entities
import robopoker.combinations

LOG = logging.getLogger("bot")
ROUNDS = ["preflop", "flop", "turn", "river"]


class StateParseException(Exception):
    pass


class State(object):
    pot = 0      # the money on the table in total
    max_bet = 0  # what is on the maximum bet on the table (by any player),
                 # i.e. how much has my bet have to be to continue
    bet = 0      # how much money did I already put in
    players = None
    player_name = ""
    possible_actions = None
    hole = None  # two cards I'm holding in my hand

    def __init__(self, player_name, hole_str, possible_actions_str, state_xml):

        self.player_name = player_name
        self.hole = parse_card_representation(hole_str)
        if len(self.hole) != 2:
            raise StateParseException("There should be exactly 2 hole cards")
        self.possible_actions = possible_actions_str.split()
        self._state = self._parse_xml_state(state_xml)
        LOG.info("hole: %s", self.hole)
        LOG.info("possible actions: %s", self.possible_actions)

    def get_hand_strength(self):
        # poker eval uses a different representation, we must convert it first
        hole = [_get_pokereval_representation(card)
                for card in self.hole]
        community = [_get_pokereval_representation(card)
                     for card in self.community]
        score = HandEvaluator.evaluate_hand(hole, community)
        LOG.info("Score %f" % score)
        return score

    @property
    def round(self):
        """Return one of `ROUNDS`"""
        return {
            0: 'preflop',
            3: 'flop',
            4: 'turn',
            5: 'river',
        }[len(self.community)]

    @property
    def raise_count(self):
        count = 0
        actions = self._get_current_round_actions()
        for action in actions:
            if action['@type'] == 'raise' or action['@type'] == 'bet':
                count += 1
        return count

    @property
    def follower_count(self):
        return 0

    def _parse_xml_state(self, xml):
        """Take robopoker's description of the state in XML parse in to objects
        """
        if not xml:
            return None
        LOG.info(xml)
        state = xmltodict.parse(xml)
        self.community = parse_community_cards(state)
        if self.community:
            if len(self.community) > 5:
                raise StateParseException("More than 5 community cards: %s"
                                          % self.community)
            LOG.info("community: %s", self.community)
        self.players = parse_players(state)
        self.pot, self.max_bet, self.my_bet = self._get_bets()
        return state

    def _get_current_round_actions(self):
        rnd_index = ROUNDS.index(self.round)
        rnd = self._state['game']['betting']['round'][rnd_index]
        assert rnd['@name'] == self.round
        actions = rnd.get('action', [])
        if isinstance(actions, dict):
            # the way we transform xml to dict, if there is only one action in
            # the round, then if will be just a dict, otherwise it's a
            # list of dicts - make it so that it's always a list
            actions = [actions]
        LOG.info("Actions in current round: %s", actions)
        return actions

    def _get_bets(self):
        total_bets = 0
        max_bet = 0
        my_bet = 0
        for player in self.players:
            bet = int(player['@in_stack']) - int(player['@stack'])
            total_bets += bet
            if player['@name'] == self.player_name:
                my_bet = bet
            if bet > max_bet:
                max_bet = bet
        return total_bets, max_bet, my_bet


def parse_community_cards(state):
    """Return a list of the community cards

    :param state: returned from xmltodict of the robopoker representation
    """
    community_cards = list()
    community = state['game']['community']
    if community and 'card' in community:
        for card in community['card']:
            new_card = robopoker.entities.Card(card['@rank'], card['@suit'])
            community_cards.append(new_card)
    return community_cards


def parse_players(state):
    """Return list of players still in the game"""
    players = state['game']['table']['player']
    active_players = list()
    rounds = state['game']['betting']['round']
    for i, rnd in enumerate(rounds):
        if rnd and 'action' in rnd and isinstance(rnd['action'], dict):
            # the way we transform xml to dict, if there is only one action in
            # the round, then if will be just a dict, otherwise it's a
            # list of dicts - make it so that it's always a list
            rounds[i]['action'] = [rnd['action']]
    actions = [r['action'] for r in rounds if 'action' in r]
    actions = list(itertools.chain.from_iterable(actions))
    for player in players:
        player_fold = [a for a in actions
                       if (a['@type'] == 'fold'
                           and a['@player'] == player['@name'])]
        if not player_fold:
            active_players.append(player)
    return active_players


def parse_card_representation(cards_string):
    """Parse robopoker's string representation of cards into Card objects

    :param cards_string: e.g. "2D 2S" or "QC 8C 3S"
    :returns: list of robopoker Card objects
    """
    cards_string = cards_string.split()
    cards = list()
    for card in cards_string:
        if len(card) != 2:
            raise Exception("The card should be represented by 2 characters,"
                            " got '%s'" % cards_string)
        new_card = robopoker.entities.Card(card[0], card[1])
        cards.append(new_card)
    return cards


def _get_pokereval_representation(card):
    rank = robopoker.combinations.RANKS.index(card.rank)
    if card.suit == 'S':  # spades
        suit = 1
    elif card.suit == 'H':  # hearts
        suit = 2
    elif card.suit == 'D':  # diamonds
        suit = 3
    elif card.suit == 'C':  # clubs
        suit = 4
    else:
        raise Exception("Unknown card suit '%s'" % card)
    assert rank in range(2, 15)
    assert suit in range(1, 5)
    return pokereval.card.Card(rank, suit)

import logging
import math
from poker.state import State
from poker.random_choice import choice

LOG = logging.getLogger("bot")

# what is the fixed bet amount
BET_AMOUNT = 20


class SimpleBot(object):

    """Simplest strategy, always call if we can"""
    name = 'simple'

    def __init__(self, state):
        self.state = state

    def get_decision_probabilities(self):
        return [0.0, 1.0, 0.0]

    def decide(self):
        """Randomly choose to check/call/raise depending on the triplet.

        Uses `get_decision_probabilities()` to get the triplet of probabilities
        of picking the actions. If the action is not possible, pick the action
        to the left (i.e. if we would raise but cannot, try to call; if we
        cannot call, try to check; if we cannot check, fold).

        """
        triplet = self.get_decision_probabilities()
        assert (sum(triplet) + 0.01) > 1.0
        decision = choice(['check', 'call', 'raise'], triplet)
        if decision == 'raise':
            if 'bet' in self.state.possible_actions:
                # RoboPoker makes a disctinction between a raise an bet, but we
                # don't care
                decision = 'bet'
            elif 'raise' not in self.state.possible_actions:
                # we cannot raise/bet, so we do the next best thing
                LOG.info('cannot %s, chose to call' % decision)
                decision = 'call'

        if decision == 'call' and ('call' not in self.state.possible_actions):
            LOG.info('cannot %s, chose to check' % decision)
            # cannot call, so let's at least try to check
            decision = 'check'

        if decision not in self.state.possible_actions:
            LOG.info('cannot %s, chose to fold' % decision)
            # if we still cannot do the action we want (e.g. cannot check)
            decision = 'fold'

        LOG.info("Decision: %s", decision)
        return decision


class RandomBot(SimpleBot):

    """Choose fold/call/raise randomly with equal probabilities"""
    name = 'random'

    def get_decision_probabilities(self):
        return [0.333, 0.333, 0.333]


class ThresholdBot(SimpleBot):

    """Choosing based on whether the hand strength is higher than threshold"""
    name = 'threshold'
    RAISE_THRESHOLD = 0.7
    CALL_THRESHOLD = 0.4

    def get_decision_probabilities(self):
        triplet = [1, 0, 0]
        hand_strength = self.state.get_hand_strength()
        LOG.info("hand_strength: %f", hand_strength)
        if hand_strength >= self.RAISE_THRESHOLD:
            triplet = [0, 0, 1]
        elif hand_strength >= self.CALL_THRESHOLD:
            triplet = [0, 1, 0]
        return triplet


class SmartBot(SimpleBot):

    """Raise based on hand strenght and #players, call based on pot odds"""
    name = 'smart'
    RAISE_THRESHOLD = 0.6
    PREFLOP_CALL_THRESHOLD = 0.4

    def get_decision_probabilities(self):
        raise_needed = self.state.max_bet - self.state.bet
        pot_odds = raise_needed / float(self.state.pot + raise_needed)
        reraise_pot_odds = ((BET_AMOUNT + raise_needed) /
                            float(self.state.pot + raise_needed + BET_AMOUNT))
        hand_strength = math.pow(self.state.get_hand_strength(),
                                 len(self.state.players) - 1)
        LOG.info("pot_odds: %f", pot_odds)
        LOG.info("hand_strength: %f", hand_strength)
        triplet = [1, 0, 0]
        if hand_strength >= self.RAISE_THRESHOLD \
                and reraise_pot_odds <= hand_strength:
            triplet = [0, 0, 1]
        elif pot_odds <= hand_strength:
            triplet = [0, 1, 0]
        elif self.state.round == 'preflop' and self.state.bet > 0 \
                and hand_strength >= self.PREFLOP_CALL_THRESHOLD:
            triplet = [0, 1, 0]
        return triplet


class RandomizedSmartBot(SmartBot):

    """Same as SmartBot, but sometimes randomly chooses different action"""
    name = 'randomized-smart'

    def get_decision_probabilities(self):
        triplet = self.get_decision_probabilities()
        if triplet == [0, 0, 1]:
            triplet = [0.1, 0.2, 0.7]
        elif triplet == [0, 1, 0]:
            triplet = [0.1, 0.7, 0.2]
        elif triplet == [1, 0, 0]:
            triplet = [0.7, 0.2, 0.1]

        return triplet


class AgressiveLooseBot(SmartBot):

    """Raise even with bad hand; play even bad hands in preflop"""
    name = 'agressive-loose'
    RAISE_THRESHOLD = 0.5
    PREFLOP_CALL_THRESHOLD = 0.2


class AgressiveTightBot(AgressiveLooseBot):

    """Raise even with bad hand; play only good hands in preflop"""
    name = 'agressive-tight'
    PREFLOP_CALL_THRESHOLD = 0.6


class PassiveLooseBot(SmartBot):

    """Raise only with a good hand; play even bad hands in preflop"""
    name = 'passive-loose'
    RAISE_THRESHOLD = 0.7
    PREFLOP_CALL_THRESHOLD = 0.2


class PassiveTightBot(PassiveLooseBot):

    """Raise only with a good hand; play only good hands in preflop"""
    name = 'passive'
    PREFLOP_CALL_THRESHOLD = 0.6


def get_bot(name, hole, possible_actions, state):
    """Return the bot based on its name"""
    parsed_state = State(name, hole, possible_actions, state)
    bot = SmartBot(parsed_state)
    if 'simple' == name:
        bot = SimpleBot(parsed_state)
    elif 'random' == name:
        bot = RandomBot(parsed_state)
    elif 'threshold' == name:
        bot = ThresholdBot(parsed_state)
    elif 'agressive-loose' == name:
        bot = AgressiveLooseBot(parsed_state)
    elif 'agressive-tight' == name:
        bot = AgressiveTightBot(parsed_state)
    elif 'passive-loose' == name:
        bot = PassiveLooseBot(parsed_state)
    elif 'passive-tight' == name:
        bot = PassiveTightBot(parsed_state)
    elif 'smart' == name:
        bot = SmartBot(parsed_state)
    elif 'randomized-smart' == name:
        bot = RandomizedSmartBot(parsed_state)
    LOG.info("\n\nname of the bot: %s", bot.name)
    return bot

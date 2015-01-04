import random
from robopoker import combinations, dictionary, shuffler

__all__ = ['Card', 'Deck', 'CardSet', 'Player', 'Table']


class CardException(Exception):
    pass


class Card(object):

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        if self.rank not in combinations.RANKS:
            raise CardException("Invalid rank: %s" % self.rank)
        if self.suit not in ['S', 'D', 'H', 'C']:
            raise CardException("Invalid suit: %s" % self.suit)

    def __repr__(self):
        return self.rank + self.suit

    def __cmp__(self, other):
        if self.rank == other.rank and self.suit == other.suit:
            return 0
        index = combinations.RANKS.index(self.rank)
        other_index = combinations.RANKS.index(other.rank)
        if index < other_index:
            return -1
        else:
            return 1


class Deck(object):

    def __init__(self, cards=None):
        if not cards:
            cards = [
                Card(r, s)
                for r in dictionary.RANK_NAME.keys()
                for s in dictionary.SUIT_NAME.keys()
            ]
        self.cards = cards

    def draw(self):
        return self.cards.pop()

    def shuffle(self):
        shuffler.shuffle(self.cards)


class CardSet(object):

    def __init__(self, cards=None):
        self.cards = []
        self.base = None
        self.kickers = []
        if cards:
            map(self.add, cards)

    def add(self, card):
        self.cards.append(card)

    def rate(self):
        hand = [repr(c) for c in self.cards]
        self.base, self.kickers = combinations.rate_hand(hand)

    def __cmp__(self, other):
        return cmp(self.base, other.base) \
            or combinations.cmp_rate(self.kickers, other.kickers)

    def __repr__(self):
        """
        Format: 8C TS KC 9H 4S 7D 2S
        """
        return ' '.join([repr(c) for c in self.cards])


class Player(object):

    def __init__(self, name, transport, stack=100):
        self.name = name
        self.transport = transport
        self.pocket = CardSet()
        self.hand = None  # Actual hand (commonly pocket + community)
        self.stack = self.initial_stack = stack
        self.folded = False
        self.allin = False
        self.bet = None  # Current bet
        self.blind = 0  # Current "live" post (like small blind bet)
        self.win = 0

    def message(self, actions, state):
        return self.transport.message(
            self.name, repr(self.pocket), actions, state)

    def table_chips(self):
        return self.blind + (self.bet or 0)


class Table(object):

    def __init__(self, size=9):
        self.size = size
        self.sits = [None] * size
        self.button = 0

    def players(self):
        s, b = self.sits, self.button
        return [p for p in s[b + 1:] + s[:b + 1] if p]

    def empty_sits(self):
        return [k for k, s in enumerate(self.sits) if not s]

    def occupied_sits(self):
        return [k for k, s in enumerate(self.sits) if s]

    def sit_in(self, player, sit=None):
        empty = self.empty_sits()
        if sit is None:
            if not empty:
                raise Exception('Table is full')
            sit = random.choice(empty)
        elif sit not in empty:
            raise Exception('Sit %s is not empty' % sit)
        self.sits[sit] = player

    def rotate_button(self):
        occupied = self.occupied_sits()
        following = occupied[self.button + 1:]
        if not following:
            self.button = occupied[0]
        else:
            self.button = random.choice(following)

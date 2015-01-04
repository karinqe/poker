class HandState(object):

    def __init__(self, table, deck):
        self.table = table
        self.deck = deck
        self.community = []
        self.posts = []
        self.betting = {'preflop': [], 'flop': [], 'turn': [], 'river': []}
        self.showdown = []

    def add_post(self, player, amount, post_type):
        self.posts.append({
            'player': player.name,
            'amount': amount,
            'type': post_type
        })

    def add_action(self, rnd, player, action_type, amount=0, error=None):
        data = {
            'player': player.name,
            'type': action_type,
            'amount': amount,
            'error': error
        }
        self.betting[rnd].append(data)

    def add_showdown(self, player, hand):
        self.showdown.append({
            'player': player.name,
            'win': player.win,
            'hand': hand
        })

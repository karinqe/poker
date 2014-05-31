#!/usr/bin/env python
import sys
import os
import xmltodict
import json

"""Collect statistics about player money.

At this point, it only collects the sum of money each player won/lost. It reads
the json file `STATS_FILE` (or creates a new one), reads the resulting state of
the poker game from stdin. It assumes stdin is the xml output from running:

    $ python poker_platform.py play_hand | ./this_script.py

It will add the difference between `stack` and `in_stack` into the resulting
statistics. If the player doesn't have any statistic on the money he has, it
will initialize it to 0 and then add the difference there.
"""

STATS_FILE = 'stats.json'


def write_stats(players):
    if os.path.isfile(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            stats = json.load(f)
    else:
        stats = dict()

    for player in players:
        diff = int(player['@stack']) - int(player['@in_stack'])
        name = player['@name']
        original = stats.get(name, 0)
        stats[name] = original + diff
    print stats

    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)


def main():
    with sys.stdin as f:
        xml = ''.join(f.readlines())
    state = xmltodict.parse(xml)
    players = state['game']['table']['player']
    write_stats(players)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import random
import sys
from typing import List


class Card:
    SUITS = {"Hearts": "♥", "Diamonds": "♦", "Clubs": "♣", "Spades": "♠"}
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self, rank: str, suit: str):
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        self.rank = rank
        self.suit = suit

    @property
    def base_value(self) -> int:
        if self.rank == "A":
            return 11
        if self.rank in ("J", "Q", "K"):
            return 10
        return int(self.rank)

    def __str__(self) -> str:
        return f"{self.rank}{self.SUITS[self.suit]}"

    def __repr__(self) -> str:
        return f"Card({self.rank!r}, {self.suit!r})"


class Deck:
    RESHUFFLE_THRESHOLD = 15

    def __init__(self, num_decks: int = 1):
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self._build()
        self.shuffle()

    def _build(self) -> None:
        self.cards = [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in Card.SUITS
            for rank in Card.RANKS
        ]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self) -> Card:
        if len(self.cards) < self.RESHUFFLE_THRESHOLD:
            print("\n  (Reshuffling the deck...)")
            self._build()
            self.shuffle()
        return self.cards.pop()

    def __len__(self) -> int:
        return len(self.cards)


class Hand:
    def __init__(self):
        self.cards: List[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    @property
    def value(self) -> int:
        total = sum(card.base_value for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    @property
    def is_soft(self) -> bool:
        total = sum(card.base_value for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return aces > 0

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value == 21

    @property
    def is_bust(self) -> bool:
        return self.value > 21

    def display(self, hide_first: bool = False) -> str:
        if hide_first:
            return "[??] " + " ".join(f"[{c}]" for c in self.cards[1:])
        return " ".join(f"[{c}]" for c in self.cards)


class Player:
    def __init__(self, name: str, balance: int = 500):
        self.name = name
        self.balance = balance
        self.hand = Hand()
        self.bet = 0

    def reset_hand(self) -> None:
        self.hand = Hand()

    def place_bet(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Bet must be positive.")
        if amount > self.balance:
            raise ValueError("Bet exceeds your balance.")
        self.bet = amount
        self.balance -= amount

    def win(self, multiplier: float = 1.0) -> None:
        self.balance += self.bet + int(self.bet * multiplier)

    def push(self) -> None:
        self.balance += self.bet

    def can_double(self) -> bool:
        return len(self.hand.cards) == 2 and self.balance >= self.bet


class Dealer:
    STAND_ON = 17

    def __init__(self):
        self.hand = Hand()

    def reset_hand(self) -> None:
        self.hand = Hand()

    def should_hit(self) -> bool:
        return self.hand.value < self.STAND_ON


class BlackjackGame:
    STARTING_BALANCE = 500
    MIN_BET = 5

    def __init__(self):
        self.deck = Deck(num_decks=4)
        self.dealer = Dealer()
        self.player: Player = None

    @staticmethod
    def _prompt(message: str) -> str:
        try:
            return input(message).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nThanks for playing. Goodbye!")
            sys.exit(0)

    def _get_bet(self) -> int:
        while True:
            raw = self._prompt(
                f"\nBalance: ${self.player.balance}. "
                f"Enter your bet (${self.MIN_BET}-${self.player.balance}): $"
            )
            try:
                amount = int(raw)
            except ValueError:
                print("  Please enter a whole number.")
                continue
            if amount < self.MIN_BET:
                print(f"  Minimum bet is ${self.MIN_BET}.")
                continue
            if amount > self.player.balance:
                print("  You don't have enough chips for that bet.")
                continue
            return amount

    def _get_action(self) -> str:
        options = ["(H)it", "(S)tand"]
        valid = {"h", "s"}
        if self.player.can_double():
            options.append("(D)ouble down")
            valid.add("d")
        prompt = f"  {' / '.join(options)}: "
        while True:
            choice = self._prompt(prompt).lower()
            if choice in valid:
                return choice
            print(f"  Invalid choice. Please enter one of: {', '.join(sorted(valid))}.")

    def _ask_yes_no(self, message: str) -> bool:
        while True:
            choice = self._prompt(message).lower()
            if choice in ("y", "yes"):
                return True
            if choice in ("n", "no"):
                return False
            print("  Please answer 'y' or 'n'.")

    def _show_table(self, hide_dealer: bool = True) -> None:
        print("\n" + "-" * 44)
        if hide_dealer:
            visible = self.dealer.hand.cards[1].base_value
            shown = "A" if self.dealer.hand.cards[1].rank == "A" else visible
            print(f"Dealer: {self.dealer.hand.display(hide_first=True)}   (showing {shown})")
        else:
            print(f"Dealer: {self.dealer.hand.display()}   (total {self.dealer.hand.value})")
        soft = " (soft)" if self.player.hand.is_soft else ""
        print(f"{self.player.name}: {self.player.hand.display()}   "
              f"(total {self.player.hand.value}{soft})")
        print("-" * 44)

    def setup(self) -> None:
        print("=" * 44)
        print("          ♠ ♥  BLACKJACK  ♦ ♣")
        print("=" * 44)
        print("Rules: Beat the dealer without going over 21.")
        print("Blackjack pays 3:2. Dealer stands on 17.\n")
        name = self._prompt("Enter your name: ") or "Player"
        self.player = Player(name, self.STARTING_BALANCE)
        print(f"\nWelcome, {self.player.name}! You start with ${self.player.balance}.")

    def _deal_initial(self) -> None:
        self.player.reset_hand()
        self.dealer.reset_hand()
        for _ in range(2):
            self.player.hand.add_card(self.deck.deal())
            self.dealer.hand.add_card(self.deck.deal())

    def _player_turn(self) -> None:
        while not self.player.hand.is_bust and self.player.hand.value < 21:
            action = self._get_action()
            if action == "h":
                self.player.hand.add_card(self.deck.deal())
                self._show_table()
            elif action == "s":
                break
            elif action == "d":
                self.player.balance -= self.player.bet
                self.player.bet *= 2
                print(f"  Doubled down! Bet is now ${self.player.bet}.")
                self.player.hand.add_card(self.deck.deal())
                self._show_table()
                break

    def _dealer_turn(self) -> None:
        print("\nDealer reveals their hand...")
        self._show_table(hide_dealer=False)
        while self.dealer.should_hit():
            print("  Dealer hits.")
            self.dealer.hand.add_card(self.deck.deal())
            self._show_table(hide_dealer=False)

    def _settle(self) -> None:
        p, d = self.player.hand, self.dealer.hand
        if p.is_bust:
            print(f"\nYou bust with {p.value}. Dealer wins. (-${self.player.bet})")
        elif d.is_bust:
            print(f"\nDealer busts with {d.value}! You win ${self.player.bet}!")
            self.player.win()
        elif p.value > d.value:
            print(f"\nYou win, {p.value} to {d.value}! (+${self.player.bet})")
            self.player.win()
        elif p.value < d.value:
            print(f"\nDealer wins, {d.value} to {p.value}. (-${self.player.bet})")
        else:
            print(f"\nPush - both have {p.value}. Your bet is returned.")
            self.player.push()

    def play_round(self) -> None:
        bet = self._get_bet()
        self.player.place_bet(bet)
        self._deal_initial()
        self._show_table()

        player_bj = self.player.hand.is_blackjack
        dealer_bj = self.dealer.hand.is_blackjack

        if player_bj or dealer_bj:
            self._show_table(hide_dealer=False)
            if player_bj and dealer_bj:
                print("\nBoth have Blackjack - push.")
                self.player.push()
            elif player_bj:
                winnings = int(self.player.bet * 1.5)
                print(f"\nBLACKJACK! You win ${winnings}!")
                self.player.win(multiplier=1.5)
            else:
                print(f"\nDealer has Blackjack. You lose ${self.player.bet}.")
            return

        self._player_turn()

        if self.player.hand.is_bust:
            self._show_table(hide_dealer=False)
        else:
            self._dealer_turn()
        self._settle()

    def run(self) -> None:
        self.setup()
        while True:
            self.play_round()

            if self.player.balance < self.MIN_BET:
                print(f"\nYou're out of chips, {self.player.name}. Game over!")
                break

            if not self._ask_yes_no(
                f"\nBalance: ${self.player.balance}. Play another round? (y/n): "
            ):
                break

        net = self.player.balance - self.STARTING_BALANCE
        sign = "+" if net >= 0 else "-"
        print(f"\nFinal balance: ${self.player.balance} ({sign}${abs(net)})")
        print("Thanks for playing. Goodbye!")


def main() -> None:
    try:
        BlackjackGame().run()
    except Exception as exc:
        print(f"\nUnexpected error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
# Mini Player Arcade - Release (11 games)

Staged 2026-10-10. Self-contained copy of the working launcher plus all
11 games. Copy the contents of this folder onto the Zero W card (or over
the existing files) to install.

## Contents
- main.py            launcher entry point (run this)
- game_menu.py       the game menu
- mini_player.py     hardware / display / button driver (shared)
- demo_lcd.py        optional standalone LCD demo
- READ ME.md         original README
- games/             11 game modules
- images/            shared sprites and splash assets
- SHA256SUMS         SHA-256 manifest of all files
- RELEASE-README.md  this file

## Games (11)
1. Screen Runner
2. Snake
3. Pong
4. Breakout
5. Asteroids
6. Blocks
7. Flappy
8. Space Invader
9. Frogger
10. Pac-Man
11. Whack-a-Mole

## Controls (common)
- D-pad (PAD_UP / PAD_DOWN / PAD_LEFT / PAD_RIGHT)  move / steer
- BTN_A        start / play again / confirm
- BTN_X        shoot / action (where used)
- BTN_SELECT   return to menu from any state

## Install
Copy this folder's contents onto the target card, keeping the layout
(main.py at the root, with games/ and images/ folders beside it). Then run:

    python3 main.py

## Verify
    sha256sum -c SHA256SUMS

## On-device checklist (still pending)
- Menu starts and all 11 entries appear.
- Each game launches; SELECT returns to menu from every state.
- Graphics are the right size and orientation.
- Controls respond; held buttons do not cause accidental actions.
- Restart (A) works; sustained play stays responsive.

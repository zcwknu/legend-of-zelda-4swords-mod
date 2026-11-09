# Four Swords Adventures: Two GameCube Controllers Mod

A mod for **The Legend of Zelda: Four Swords Adventures** (GameCube, USA, `G4SE01`, revision 0). It lets two people play the multiplayer modes with two regular GameCube controllers. The original game requires every multiplayer player to have a Game Boy Advance and a GBA link cable.

**Due to GitHub size limitations and me being scared of Nintendo suing me; there is no game file uploaded; however, the tools are below to create your own version.**.

## What it does

### 1. Two-player with two GameCube controllers
- Controller port 1 is Player 1 and controller port 2 is Player 2. No Game Boy Advance or link cables needed.
- Each player controls their own Links on their own controller.
- At the start of a level, walk next to your sleeping partner Link and press **Y** to gather it.

### 2. Split screen instead of GBA screens
In the original game, when a player goes into a house or cave, their view moves to their Game Boy Advance screen. In this mod it goes to the TV instead:
- **Top (~60%)**: the shared world view, shrunk and centered.
- **Bottom left**: Player 1's private view (inside houses, caves, etc.).
- **Bottom right**: Player 2's private view.

The top view only shrinks while someone is inside a private area. When both players are back outside, it returns to full screen.

### 3. Shadow Battle works with two controllers
Shadow Battle (the versus mode) loads and plays with two GameCube controllers. The original game crashed here because it tried to load arena map data meant for GBA players. The mod loads the standard arena instead.

### 4. New menu option
On the player-count screen, the **Two-Player Game** row now shows two GameCube controllers instead of two Game Boy Advances.

### 5. Single player is unchanged
Single-player plays exactly like the original, including its own window on the TV when you go into houses. All new behavior only switches on in the two-controller mode.

## Controls (same for both players)

This is the game's own GameCube controller layout. Nothing was remapped.

| Action | Button |
|---|---|
| Move | Control Stick |
| Sword (hold for spin attack) | B |
| Use item / talk | A |
| Lift / throw | R |
| Gather Links / formation menu | Y or L |
| Quick formation | C-Stick |
| Split off / switch Links | X or D-Pad |
| Pause | START |

## How it works (short version)

- **Input:** the game already had code for a GameCube controller player. It was only allowed for single-player. Small patches let the multiplayer setup accept a controller in each port and register each player as a "GameCube controller" player. A check that decides whether a player "has a GBA" now also accepts a controller, but only in the two-controller mode. That way single-player keeps its original behavior.
- **Display:** the game already draws each player's private view as a window on the TV (that's how single-player shows houses). The mod uses that window for both players and moves the windows to the bottom of the screen. It also scales the main 3D view (viewport and scissor) down into the top area whenever a window is open.
- **Shadow Battle:** forces the game to use the standard arena map file.
- **Menu:** edits the menu layout file (`adv_n_player.blo` inside `entry.arc`) so the Two-Player row uses the GameCube controller picture.
- **Where the new code lives:** about 1 KB of new code is added as an extra section of the game's executable (`main.dol`) at `0x80555F80`, right after the game's own memory. The game's heap start is raised so nothing overwrites it. The low-memory area some loaders and cheat engines use is left alone.

## Building

Requirements: Python 3 and your own clean ISO.

1. Extract the disc (`tools/gcfs.py`).
2. Bake the patches into `main.dol` (`build/bake_dol.py`).
3. Patch the menu file (`menu/patch_menu.py`).
4. Rebuild the ISO (`tools/copy_used.py` then `tools/build_iso.py`). Only `main.dol` and `entry.arc` change. They are written into unused space on the disc, and all other game files stay byte-for-byte identical to the original.

The result is a standard full-size GameCube disc image (1,459,978,240 bytes) that keeps the original game ID, `G4SE01`.

## Playing on a real GameCube

Copy the ISO to an SD card and launch it with **Swiss** (tested target: Swiss v0.6 with an SD2SP2 adapter). Plug controllers into ports 1 and 2. Choose **Hyrulean Adventure → Two-Player Game**, or **Shadow Battle**.

## Known limitations
- Two players only. Three- and Four-Player still expect Game Boy Advances.
- Real-GBA multiplayer is not supported in the modded image.
- The Shadow Battle player-count screen still shows GBA pictures.
- On the overworld, the bottom panels stay empty and the top view uses the full screen. The panels only appear when someone goes inside.

## Disclaimer
Fan project for personal use. *The Legend of Zelda* is a trademark of Nintendo. Not affiliated with or endorsed by Nintendo. Do not distribute game files or ISOs.

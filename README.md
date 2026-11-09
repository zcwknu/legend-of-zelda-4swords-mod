# Four Swords Adventures: Two GameCube Controllers Mod

![Split screen with both players inside](docs/img/split_screen_both_inside.png)

A mod for **The Legend of Zelda: Four Swords Adventures** (GameCube, USA, `G4SE01`, revision 0). It lets two people play the multiplayer modes with two regular GameCube controllers. The original game requires every multiplayer player to have a Game Boy Advance and a GBA link cable.

> **No game files are included.** You need your own copy of the game. This repo only contains the tools and patches that modify it.

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

## Building your own ISO

Requirements: **Python 3** (no extra packages) and **your own clean USA ISO** (`G4SE01`, SHA-1 `4bd926835dfbeaae72d01abe5fb581b527154a30`).

```
python3 build.py "Legend of Zelda, The - Four Swords Adventures (USA).iso" "Zelda FSA 2GC.iso"
```

That's it. The script:
1. Checks that your ISO is the expected clean USA copy. Your original is only read, never changed.
2. Builds the patches into the game's executable (`build/bake_dol.py`, using `patches/G4SE01_2gc_patches.ini`).
3. Patches the menu file (`menu/patch_menu.py`).
4. Writes the new ISO (`tools/copy_used.py`, then `tools/build_iso.py`). Only `main.dol` and `entry.arc` change. They are written into unused space on the disc, and all other game files stay byte-for-byte identical.
5. Prints the SHA-1 of the result. The expected value is `336f8607b761ac5d0e0ac76f8cfc9ada683d7855`.

The output is a standard full-size GameCube disc image (1,459,978,240 bytes) with the original game ID `G4SE01`. If the build is interrupted, run the same command again and it resumes.

### Trying it in Dolphin without building
`patches/G4SE01_2gc_patches.ini` is a Dolphin game-patch file. Copy it to Dolphin's `GameSettings` folder as `G4SE01.ini` to run the gameplay and split-screen changes on an unmodified ISO. The menu icons need the built ISO. Don't use this patch file together with the built ISO.

### Repository layout
| Path | What it is |
|---|---|
| `build.py` | One-command build |
| `patches/G4SE01_2gc_patches.ini` | All code patches (Dolphin patch format) |
| `build/bake_dol.py` | Builds the patches into `main.dol` and adds the new code section |
| `menu/patch_menu.py` | Changes the Two-Player menu icons (plus `rarc.py` and `yaz0enc.py` archive helpers) |
| `tools/gcfs.py` | Reads the GameCube disc file system |
| `tools/copy_used.py`, `tools/build_iso.py` | Write the patched disc image |
| `docs/img/` | Screenshots |

## Playing on a real GameCube

Copy the ISO to an SD card and launch it with **Swiss** (tested target: Swiss v0.6 with an SD2SP2 adapter). Plug controllers into ports 1 and 2. Choose **Hyrulean Adventure → Two-Player Game**, or **Shadow Battle**.

## Status

| Feature | Dolphin emulator | Real GameCube |
|---|---|---|
| Two controllers, independent players | ✅ | not yet tested |
| Split screen (one or both players inside) | ✅ (patch build) | not yet tested |
| Shadow Battle loads and plays | ✅ (patch build) | not yet tested |
| New menu icons | ✅ (ISO) | not yet tested |
| Single-player unchanged | ✅ (patch build) | not yet tested |
| Full level / full battle completed | not yet | not yet |

"Patch build" means the change was tested with the same code running as Dolphin patches, before it was built into the ISO.

## Known limitations
- Two players only. Three- and Four-Player still expect Game Boy Advances.
- Real-GBA multiplayer is not supported in the modded image.
- The Shadow Battle player-count screen still shows GBA pictures.
- On the overworld, the bottom panels stay empty and the top view uses the full screen. The panels only appear when someone goes inside.

## Disclaimer
Fan project for personal use. *The Legend of Zelda* is a trademark of Nintendo. Not affiliated with or endorsed by Nintendo. Do not distribute game files or ISOs.

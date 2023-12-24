# Septluxian Scope

A decompiler for games using the YS7_SCP format, specifically *Ys Seven*, *Ys 8: Lacrimosa of Dana* and *The Legend of Nayuta: Boundless Trails*.
*Ys vs. Trails in the Sky: Alternative Saga* is partially supported, but do not currently have any instruction tables included.

To use, ensure Python (3.10 or above) is installed, then drag a `.bin` file onto `main.py`.
Edit the resulting `.7l` file, then drag it back onto `main.py` to recompile.

It also supports the *Ys 8*'s `script/{en,fr,ja}/*.scp` files, used for translating the game.
These are translated to/from `.csv` files in an identical manner.
Do not confuse them with `script/*.scp`, however, which are uncompiled source code for the `.bin` scripts.

## Supported games

- *The Legend of Nayuta: Boundless Trails*: full support for scripts (`script/*.bin`)
- *Ys 7*: full support for scripts (`script/*.bin`). However, no reliable method exists for distinguishing these from Nayuta, so you need to pass `-i ys7` to use this.
- *Ys 8: Lacrimosa of Dana*: full support for scripts (`script/*.bin`), and also the translation files (`script/$lang/*.scp`), see above.
  **Do note** however that the game does not actually use the `script/*.bin` files; it reads the textual `script/*.scp` files directly, which can be edited with a plain text editor.

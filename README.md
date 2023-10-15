# Septluxian Scope

A decompiler for games using the YS7_SCP format, specifically *Ys 8: Lacrimosa of Dana* and *The Legend of Nayuta: Boundless Trails*.
*Ys Seven* and *Ys vs. Trails in the Sky: Alternative Saga* are partially supported, but do not currently have any instruction tables included.

To use, ensure Python (3.10 or above) is installed, then drag a `.bin` file onto `main.py`.
Edit the resulting `.7l` file, then drag it back onto `main.py` to recompile.

It also supports the *Ys 8*'s `script/{en,fr,ja}/*.scp` files, used for translating the game.
These are translated to/from `.csv` files in an identical manner.
Do not confuse them with `script/*.scp`, however, which are uncompiled source code for the `.bin` scripts.

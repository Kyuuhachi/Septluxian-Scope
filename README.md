# Septluxian Scope

A decompiler for games using the YS7_SCP format, specifically *Ys Seven*, *Ys 8: Lacrimosa of Dana* and *The Legend of Nayuta: Boundless Trails*.
*Ys vs. Trails in the Sky: Alternative Saga* is partially supported, but do not currently have any instruction tables included.

To use, ensure Python (3.10 or above) is installed, then drag a `.bin` file onto `main.py`.
Edit the resulting `.7l` file, then drag it back onto `main.py` to recompile.

In addition, the translation files for *Ys 7* and *8* are supported.
For *Ys 7*, these are in `lang/*/text/*.dbin`, and are translated to json files.
For *Ys 8*, they are in `script/{en,fr,ja}/*.scp`, and are converted to csv.
Do not confuse these with `script/*.scp`, however, which are source code for the `.bin` scripts.

## Supported games

- *The Legend of Nayuta: Boundless Trails*: full support for scripts (`script/*.bin`)
- *Ys SEVEN*: full support for scripts (`script/*.bin`). However, no reliable method exists for distinguishing these from Nayuta, so you need to pass `-i ys7` to use this.
- *Ys VIII: Lacrimosa of Dana*: full support for scripts (`script/*.bin`), and also the translation files (`script/$lang/*.scp`), see above.
  **Do note** however that the game does not actually use the `script/*.bin` files; it reads the textual `script/*.scp` files directly, which can be edited with a plain text editor.
- *Ys IX: Monstrum Nox*: full support for scripts. For English and French scripts, you'll need to pass `-e utf8` or change the encoding in `settings.py`.

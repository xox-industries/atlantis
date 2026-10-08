# Atlantis

Atlantis is a command-line tool for running and managing dedicated game servers on your own Linux machine.

## Why

Hosting a game server usually means wrestling with SteamCMD, manual config files, Docker, and half a dozen tutorials. Atlantis wraps all of that into one consistent workflow so you can spend less time setting things up and more time playing.

## What it does

Atlantis lets you create, start, stop, and update game servers from the terminal. It handles the messy parts — downloading the right server binaries, generating config files, picking Java versions for Minecraft, managing Steam authentication, and running each game in its own isolated container — so the same commands work whether you are running Palworld, Terraria, Minecraft, TModLoader, or Don't Starve Together.

## How it works

You talk to Atlantis through a terminal app. Pick a game, give your server a name, answer a few prompts, and Atlantis builds everything it needs behind the scenes. Each server runs as a separate container, which keeps saves, mods, and settings tidy and prevents one game from interfering with another.

When you want to change a setting or update a manifest, you edit through Atlantis instead of hunting down config files by hand. When you are done, stop the server the same way you started it.

## Who it is for

Atlantis is built for anyone who wants self-hosted game servers without becoming a full-time sysadmin: friend groups, small communities, or anyone who prefers to own their own hardware.

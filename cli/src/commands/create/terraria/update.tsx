import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

const AUTOCREATE_OPTIONS = [
  { value: 1, label: 'Small' },
  { value: 2, label: 'Medium' },
  { value: 3, label: 'Large' },
]

const DIFFICULTY_OPTIONS = [
  { value: 0, label: 'Normal' },
  { value: 1, label: 'Expert' },
  { value: 2, label: 'Master' },
  { value: 3, label: 'Journey' },
]

const promptOptionalText = async (options: {
  message: string
  initialValue?: string | null
}) => {
  const value = ensureNotCancelled(
    await p.text({
      message: options.message,
      initialValue: options.initialValue ?? '',
    })
  )
  return value.trim().length > 0 ? value.trim() : undefined
}

export const updateTerrariaAction = async () => {
  const { displayTerraria: manifests } =
    await graphQLClient.ATL_CommandsCreateTerraria_DisplayTerraria()

  if (manifests.length === 0) {
    p.log.warn('No Terraria manifests found')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Terraria manifest to update',
      options: manifests.map((manifest) => ({
        value: manifest.path,
        label: manifest.path === '' ? '.' : manifest.path,
      })),
    })
  )

  const manifest = manifests.find((m) => m.path === selected)
  if (manifest === undefined) {
    throw new Error('Selected manifest not found')
  }

  const steamAppBetaBranch = await promptOptionalText({
    message: 'Steam app beta branch (leave empty for none)',
    initialValue: manifest.steamAppBetaBranch,
  })

  const gameAutocreate = ensureNotCancelled(
    await p.select<number>({
      message: 'World size',
      options: AUTOCREATE_OPTIONS,
      initialValue: manifest.gameAutocreate,
    })
  )

  const gameDifficulty = ensureNotCancelled(
    await p.select<number>({
      message: 'Difficulty',
      options: DIFFICULTY_OPTIONS,
      initialValue: manifest.gameDifficulty ?? 0,
    })
  )

  const gameMotd = await promptOptionalText({
    message: 'Message of the day (leave empty for none)',
    initialValue: manifest.gameMotd,
  })

  const gameSeed = await promptOptionalText({
    message: 'World seed (leave empty for random)',
    initialValue: manifest.gameSeed,
  })

  const gamePassword = await promptOptionalText({
    message: 'Password (leave empty for none)',
    initialValue: manifest.gamePassword,
  })

  const updating = p.spinner()
  updating.start('Updating Terraria manifest')

  try {
    const { updateTerraria: updated } =
      await graphQLClient.ATL_CommandsCreateTerraria_UpdateTerraria({
        path: selected,
        steamAppBetaBranch,
        gameAutocreate,
        gameDifficulty,
        gameMotd,
        gamePassword,
        gameSeed,
      })

    updating.stop(
      `Updated manifest at ${chalk.magentaBright(
        updated.path === '' ? 'terraria/manifest.json' : `${updated.path}/manifest.json`
      )}`
    )
  } catch (e) {
    updating.cancel()
    throw e
  }
}

const updateTerrariaCommand = new AtlantisCommand('update')
  .description('Update an existing Terraria manifest')
  .action(updateTerrariaAction)

export default updateTerrariaCommand

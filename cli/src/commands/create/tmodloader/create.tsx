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
  initialValue?: string
}) => {
  const value = ensureNotCancelled(
    await p.text({
      message: options.message,
      initialValue: options.initialValue ?? '',
    })
  )
  return value.trim().length > 0 ? value.trim() : undefined
}

export const createTModLoaderAction = async () => {
  const steamAppBetaBranch = await promptOptionalText({
    message: 'Steam app beta branch (leave empty for none)',
  })

  const gameAutocreate = ensureNotCancelled(
    await p.select<number>({
      message: 'World size',
      options: AUTOCREATE_OPTIONS,
      initialValue: 1,
    })
  )

  const gameDifficulty = ensureNotCancelled(
    await p.select<number>({
      message: 'Difficulty',
      options: DIFFICULTY_OPTIONS,
      initialValue: 0,
    })
  )

  const gameMotd = await promptOptionalText({
    message: 'Message of the day (leave empty for none)',
  })

  const gameSeed = await promptOptionalText({
    message: 'World seed (leave empty for random)',
  })

  const gamePassword = await promptOptionalText({
    message: 'Password (leave empty for none)',
  })

  const creating = p.spinner()
  creating.start('Creating TModLoader manifest')

  try {
    const { createTmodloader: created } =
      await graphQLClient.ATL_CommandsCreateTModLoader_CreateTModLoader({
        steamAppBetaBranch,
        gameAutocreate,
        gameDifficulty,
        gameMotd,
        gamePassword,
        gameSeed,
      })

    creating.stop(
      `Created manifest at ${chalk.magentaBright(
        `tmodloader/${created.path}/trident.manifest.json`
      )}`
    )
  } catch (e) {
    creating.cancel()
    throw e
  }
}

const createTModLoaderCommand = new AtlantisCommand('create')
  .description('Create a TModLoader manifest')
  .action(createTModLoaderAction)

export default createTModLoaderCommand

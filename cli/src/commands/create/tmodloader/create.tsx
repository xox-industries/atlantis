import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import type { AutocompletePrompt } from '@clack/core'
import * as p from '@clack/prompts'
import chalk from 'chalk'

const SELF_DIRECTORY = '.'

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

const promptManifestPath = async () => {
  const { displayTmodloaderDirectories: directories } =
    await graphQLClient.ATL_CommandsCreateTModLoader_DisplayTModLoaderDirectories()

  const allDirectories = new Set(directories)

  const choice = ensureNotCancelled(
    await p.autocomplete({
      message: `Navigate to manifest directory ${chalk.gray('(type a path, Tab to complete, Enter to confirm)')}`,
      options: function (this: AutocompletePrompt<p.Option<string>>): p.Option<string>[] {
        const input = (this.userInput ?? '').replace(/\/+$/, '')

        const options: p.Option<string>[] = []

        if (input !== '' && allDirectories.has(input)) {
          options.push({ value: input, label: `${input}/${SELF_DIRECTORY}` })
        }

        let parent = ''
        let filterSuffix = input.toLowerCase()

        for (const dir of allDirectories) {
          if (dir === '') {
            continue
          }
          if (input === dir) {
            parent = dir
            filterSuffix = ''
            break
          }
          if (input.startsWith(`${dir}/`)) {
            parent = dir
            filterSuffix = input.slice(dir.length + 1).toLowerCase()
          }
        }

        const prefix = parent === '' ? '' : `${parent}/`
        const seen = new Set<string>()

        for (const dir of allDirectories) {
          if (!dir.startsWith(prefix) || dir === parent) {
            continue
          }

          const remainder = dir.slice(prefix.length)
          const childName = remainder.split('/')[0]
          if (childName === '') {
            continue
          }

          if (filterSuffix !== '' && !childName.toLowerCase().startsWith(filterSuffix)) {
            continue
          }

          const childPath = `${prefix}${childName}`
          if (seen.has(childPath)) {
            continue
          }

          seen.add(childPath)
          options.push({ value: childPath, label: childPath })
        }

        return options.sort((a, b) => (a.label ?? '').localeCompare(b.label ?? ''))
      },
      filter: () => true,
      completeOnTab: true,
    })
  )

  return choice
}

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
  const path = await promptManifestPath()

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
        path,
        steamAppBetaBranch,
        gameAutocreate,
        gameDifficulty,
        gameMotd,
        gamePassword,
        gameSeed,
      })

    creating.stop(
      `Created manifest at ${chalk.magentaBright(
        created.path === '' ? 'tmodloader/manifest.json' : `${created.path}/manifest.json`
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

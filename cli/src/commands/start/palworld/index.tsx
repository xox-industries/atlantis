import { printAttachTips, StartOptions } from '@/src/commands/start'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const startPalworldAction = async (options: StartOptions) => {
  const { displayPalworldInstances: instances } =
    await graphQLClient.ATL_CommandsStartPalworld_DisplayPalworldInstances()

  if (!instances.some((i) => !i.running)) {
    p.log.warn('No Palworld instances available to start')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Palworld instance',
      options: instances.map((instance) => ({
        value: instance.path,
        label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        hint: instance.running ? `port ${instance.port}) (already running` : undefined,
        disabled: instance.running,
      })),
    })
  )

  if (!options.skipSteamValidate) {
    const updating = p.taskLog({ title: 'Checking Palworld application', limit: 5 })
    for await (const result of graphQLClient.ATL_CommandsStartPalworld_PalworldValidateApp(
      {
        path: selected,
      }
    )) {
      const line = result.palworldValidateApp
      if (line.trim().length > 0) {
        updating.message(line)
      }
    }
    updating.success('Palworld application check complete')
  }

  const starting = p.spinner()
  starting.start(`Starting Palworld instance ${chalk.magentaBright(selected)}`)
  try {
    const { startPalworld: started } =
      await graphQLClient.ATL_CommandsStartPalworld_StartPalworld({
        path: selected,
      })
    starting.stop(
      `Palworld instance ${chalk.magentaBright(
        started.path === '' ? '.' : started.path
      )} started ${chalk.gray(`on port ${started.port}`)}`
    )

    printAttachTips(started.containerName)
  } catch (e) {
    starting.cancel()
    throw e
  }
}

const startPalworldCommand = new AtlantisCommand('palworld')
  .description('Start a Palworld instance')
  .option('--skip-steam-validate', 'Skip Steam validation before starting')
  .action(startPalworldAction)

export default startPalworldCommand

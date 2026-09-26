import { StartOptions } from '@/src/commands/start'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const startPalworldAction = async (options: StartOptions) => {
  const { displayPalworld: instances } =
    await graphQLClient.ATL_CommandsStartPalworld_DisplayPalworld()

  if (!instances.some((i) => !i.running)) {
    p.log.warn('No Palworld instances available to start')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Palworld instance',
      options: instances.map((instance) => ({
        value: instance.name,
        label: chalk.magentaBright(instance.name),
        hint: instance.running ? `port ${instance.port}) (already running` : undefined,
        disabled: instance.running,
      })),
    })
  )

  if (!options.skipSteamValidate) {
    const updating = p.taskLog({ title: 'Checking Palworld application', limit: 5 })
    for await (const result of graphQLClient.ATL_CommandsStartPalworld_PalworldValidateApp()) {
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
        instance: selected,
      })
    starting.stop(
      `Palworld instance ${chalk.magentaBright(started.name)} started ${chalk.gray(`on port ${started.port}`)}`
    )
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
